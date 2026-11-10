"""Tela fechada dos roteiros acadêmicos calculados na demonstração local."""

from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd
import streamlit as st

from vrac.analyses.academic import (
    TITLES,
    AnalysisFilters,
    AnalysisKind,
    CalculatedAnalysis,
    ChartSpec,
    ResultTable,
    calculate,
    chart_unit,
)
from vrac.analyses.academic_data import AcademicSource
from vrac.analyses.academic_export import report_zip, result_context, summary_table, table_csv
from vrac.analyses.academic_quality import inspect_source
from vrac.analyses.export import _write, detail_csv, summary_csv
from vrac.analyses.faculty_overview import OverviewFilters, compute_overview, filter_options
from vrac.analyses.pdf_export import report_pdf
from vrac.analyses.verification import (
    IDENTITY,
    RULE_ID,
    Context,
    Status,
    VerificationSession,
)
from vrac.branding import Branding
from vrac.charts import academic_chart, render_png
from vrac.demo_data import (
    DemoDataError,
    DemoOptions,
    load_academic_source,
    load_department_hierarchy,
)
from vrac.faculty_presentation import (
    render_composition,
    render_faculty_details,
    render_faculty_metric,
)
from vrac.feedback import OVERVIEW_STATUS
from vrac.feedback_ui import render_feedback
from vrac.indicators import change_label
from vrac.navigation import ALL_FACULTY, COMPLETE_CODES, FACULTY, FACULTY_PICKER, VIEW_KEY
from vrac.organisation_ui import OrganisationScope, organisation_filters
from vrac.settings import DemoSource, Settings
from vrac.ui_kit import card_title, data_table, download_button, scroll_to, show_chart, step
from vrac.web_charts import interactive_chart

ANALYSIS_GUIDE = {
    "R01": (
        "Como está composto o corpo docente?",
        "Cadastro atual por departamento, quadro e categoria, com detalhe das Horas Reais. "
        "O intervalo de semestres não altera o cadastro atual.",
    ),
    "R02": (
        "Como o grupo QP se compara ao corpo docente geral?",
        "Cadastro atual e grupo de comparação configurável. A composição de QP é uma "
        "simulação identificada; não representa uma definição institucional.",
    ),
    "R03": (
        "Como o corpo docente evoluiu no período?",
        "Evolução por semestre e mês. Selecione o intervalo; pessoas distintas por semestre "
        "não correspondem à soma das contagens mensais.",
    ),
    "R04": (
        "Como se distribuem a carga horária e as alocações?",
        "Use o semestre da carga horária. Horas Reais e horas alocadas são medidas distintas "
        "e aparecem com suas próprias unidades e fontes.",
    ),
    "R05": (
        "Quais funções possuem evidência no período?",
        "Consulte as vigências no intervalo selecionado. Mudança de função ou cargo "
        "não comprova contratação.",
    ),
    "R06": (
        "Como evoluíram as matrículas e os alunos?",
        "Compare o intervalo por curso, habilitação, turno, nível e forma de ingresso. "
        "Registros de matrícula e alunos únicos permanecem separados.",
    ),
}

# Filtros que cada análise realmente usa; ao calcular várias, aparecem os de todas.
# Os ocultos mantêm o valor inicial do formulário, sem alterar o cálculo daquela análise.
INTERVAL_ANALYSES = {"R03", "R05", "R06"}
WORKLOAD_ANALYSES = {"R04"}
CADRE_ANALYSES = {"R01", "R03", "R04", "R05"}
CATEGORY_ANALYSES = {"R01", "R02", "R03", "R04", "R05"}
QP_ANALYSES = {"R02"}
ACADEMIC_ANALYSES = {"R06"}

# Sufixos das chaves; cada aba usa o seu prefixo para não misturar estados.
FILTER_WIDGET_KEYS = (
    "first",
    "last",
    "workload_period",
    "cadres",
    "categories",
    "qp",
    "courses",
    "qualifications",
    "shifts",
    "levels",
    "entries",
)

# Códigos e datas são inteiros na tabela, mas não são quantidades.
NOT_QUANTITIES = {"Matrícula fictícia", "Ano", "Mês"}
CHANGE_COLUMN = "Variação %"


def analysis_names() -> dict[str, str]:
    """Nomes do seletor associados aos códigos, na ordem apresentada."""
    return {
        "R01 · Situação geral do departamento": "R01",
        **{f"{key} · {value}": key for key, value in TITLES.items()},
    }


def _clear(*, source: bool = False, prefix: str = "suite") -> None:
    for key in (
        "results",
        "result_key",
        "generated",
        "overview",
        "verification",
        "execution_id",
    ):
        st.session_state.pop(f"{prefix}_{key}", None)
    if source:
        st.session_state.pop(f"{prefix}_source", None)
        st.session_state.pop(f"{prefix}_loaded_at", None)


def _format(value: object) -> str:
    if value is None or value is pd.NA or (isinstance(value, float) and pd.isna(value)):
        return "ausente"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value) if isinstance(value, int) else f"{value:g}".replace(".", ",")
    return str(value)


def _percent(value: object) -> str:
    """Uma casa decimal só na tela; o CSV mantém a precisão calculada."""
    if value is None or pd.isna(value):
        return "ausente"
    return f"{value:.1f}".replace(".", ",")


def _display(table) -> None:
    if not table.rows:
        st.info("Sem registros para esta tabela no recorte selecionado.")
        return
    raw = pd.DataFrame(table.rows, columns=table.columns)
    numeric = [
        name
        for name in table.columns
        if name not in NOT_QUANTITIES
        and any(isinstance(value, int | float) for value in raw[name])
        and all(value is None or isinstance(value, int | float) for value in raw[name])
    ]
    shown = raw.map(_format)
    for name in table.columns:
        if "%" in name and name in numeric:
            shown[name] = raw[name].map(_percent)
    if CHANGE_COLUMN in raw:
        shown[CHANGE_COLUMN] = [
            change_label(None if pd.isna(value) else value, text)
            for value, text in zip(raw[CHANGE_COLUMN], shown[CHANGE_COLUMN], strict=True)
        ]
    data_table(shown, numeric=numeric)
    st.caption(f"Unidade: {table.unit}. {table.note}")


def _pick(label: str, options: set[str], key: str) -> tuple[str, ...]:
    # Remover seleções que deixaram de existir quando a origem é recarregada.
    if key in st.session_state:
        st.session_state[key] = [x for x in st.session_state[key] if x in options]
    return tuple(
        st.multiselect(label, sorted(options), key=key, placeholder="Todos", persist_state="page")
    )


def _reset_filters(prefix: str) -> None:
    """Limpa somente o recorte analítico, preservando a origem explicitamente carregada."""
    _clear(prefix=prefix)
    for key in FILTER_WIDGET_KEYS:
        st.session_state.pop(f"{prefix}_{key}", None)


def _filters(source: AcademicSource, kinds: frozenset[str], prefix: str) -> AnalysisFilters:
    periods = source.periods
    first_period, last_period, workload_period = periods[0], periods[-1], periods[-1]
    st.caption(
        "Seleções vazias incluem todos os valores disponíveis. "
        "Ao mudar um filtro, calcule novamente para atualizar resultados e arquivos."
    )
    single = len(kinds) == 1
    show_interval = bool(kinds & INTERVAL_ANALYSES)
    show_workload = bool(kinds & WORKLOAD_ANALYSES)
    if show_interval or show_workload:
        fields = iter(st.columns(3 if show_interval and show_workload else 2))
    if show_interval:
        with next(fields):
            first_period = st.selectbox(
                "Semestre inicial",
                periods,
                key=f"{prefix}_first",
                persist_state="page",
                help="Início do intervalo usado no histórico docente, funções e matrículas.",
            )
        with next(fields):
            last_period = st.selectbox(
                "Semestre final",
                periods,
                index=len(periods) - 1,
                key=f"{prefix}_last",
                persist_state="page",
                help="Fim do intervalo, incluindo o semestre selecionado.",
            )
    if show_workload:
        with next(fields):
            workload_period = st.selectbox(
                "Semestre da carga horária",
                periods,
                index=len(periods) - 1,
                key=f"{prefix}_workload_period",
                persist_state="page",
                help="Referência específica da R04; não é a soma do intervalo de semestres.",
            )
    from vrac.analyses.faculty_overview import NOT_INFORMED

    cadres = {
        r.cadre or NOT_INFORMED
        for r in (*source.faculty.register, *source.history, *source.workloads)
    }
    categories = {r.category or NOT_INFORMED for r in (*source.faculty.register, *source.history)}
    staff_cadres: tuple[str, ...] = ()
    staff_categories: tuple[str, ...] = ()
    qp: tuple[str, ...] = ()
    if kinds & CATEGORY_ANALYSES:
        show_cadres = bool(kinds & CADRE_ANALYSES)
        with st.expander("Filtros docentes e grupo de comparação", expanded=single):
            first, second = st.columns(2)
            if show_cadres:
                with first:
                    staff_cadres = _pick("Quadros docentes", cadres, f"{prefix}_cadres")
            with second if show_cadres else first:
                staff_categories = _pick(
                    "Categorias funcionais", categories, f"{prefix}_categories"
                )
            if kinds & QP_ANALYSES:
                qp_key = f"{prefix}_qp"
                qp_options = sorted({r.cadre for r in source.faculty.register if r.cadre})
                defaults = [x for x in qp_options if x in {"PROF PRINCIPAL", "PRINCIPAL"}]
                if qp_key in st.session_state:
                    st.session_state[qp_key] = [
                        x for x in st.session_state[qp_key] if x in qp_options
                    ]
                else:
                    st.session_state[qp_key] = defaults
                qp = tuple(
                    st.multiselect(
                        "Quadros do grupo QP — simulação configurável",
                        qp_options,
                        key=qp_key,
                        persist_state="page",
                    )
                )
            st.caption(
                "O grupo inicial é apenas um exemplo de simulação, sem definição institucional "
                "de QP. Seus quadros ficam registrados nos filtros e nas exportações. Na R03, "
                "o filtro de quadros controla as séries exibidas e preserva o total; na "
                "R04/R05 filtra a população. Na R02, Quadros docentes não recorta o geral: "
                "use o grupo QP para a comparação."
            )
    courses: tuple[str, ...] = ()
    qualifications: tuple[str, ...] = ()
    levels: tuple[str, ...] = ()
    shifts: tuple[str, ...] = ()
    entries: tuple[str, ...] = ()
    if kinds & ACADEMIC_ANALYSES:
        with st.expander("Filtros acadêmicos", expanded=single):
            student_rows = (*source.students, *source.student_history)
            courses = _pick(
                "Cursos (códigos separados)", {r.course for r in student_rows}, f"{prefix}_courses"
            )
            first, second = st.columns(2)
            with first:
                qualifications = _pick(
                    "Habilitações",
                    {r.qualification for r in student_rows if r.qualification},
                    f"{prefix}_qualifications",
                )
                levels = _pick(
                    "Níveis", {r.level for r in student_rows if r.level}, f"{prefix}_levels"
                )
            with second:
                shifts = _pick(
                    "Turnos", {r.shift for r in student_rows if r.shift}, f"{prefix}_shifts"
                )
                entries = _pick(
                    "Formas de ingresso",
                    {r.entry_kind for r in student_rows if r.entry_kind},
                    f"{prefix}_entries",
                )
            st.caption(
                "As situações de cada série seguem a regra documentada; cursos "
                "não são unidos pelo nome."
            )
    return AnalysisFilters(
        first_period,
        last_period,
        workload_period,
        qp,
        courses,
        staff_cadres,
        staff_categories,
        qualifications,
        shifts,
        levels,
        entries,
    )


def _table_download(
    result: CalculatedAnalysis,
    table: ResultTable,
    generated_at: datetime,
    export_context: dict[str, str] | None,
    *,
    key: str,
) -> None:
    download_button(
        "Baixar tabela (CSV)",
        table_csv(result, table, generated_at, export_context),
        file_name=f"vrac-{result.kind}-{table.key}.csv",
        mime="text/csv",
        key=key,
    )


def _chart_card(
    result: CalculatedAnalysis,
    specification: ChartSpec,
    index: int,
    branding: Branding,
    generated_at: datetime,
    *,
    prefix: str,
    export_context: dict[str, str] | None,
    csv_key: str,
) -> tuple[str, Callable[[], bytes]]:
    """Gráfico primeiro e tabela sob demanda, com a unidade e o gerador do PNG do pacote."""
    table = next(t for t in result.tables if t.key == specification.table)
    unit = chart_unit(result, specification)
    chart_context = result_context(result, export_context) | {
        "Análise": str(result.kind),
        "Gráfico": specification.title,
        "Unidade": unit,
        "Avisos": " | ".join((*result.notes, table.note)),
    }

    def png() -> bytes:
        return render_png(lambda: academic_chart(result, specification, branding), chart_context)

    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center"):
            card_title(specification.title, f"Unidade: {unit}")
            download_button(
                "Baixar gráfico (PNG)",
                png,
                file_name=f"vrac-{result.kind}-grafico-{index + 1}.png",
                mime="image/png",
                key=f"{prefix}_{result.kind}_png_{index}",
                type="tertiary",
                on_click="ignore",
            )
        show_chart(
            f"{prefix}-{result.kind}-{index}",
            chart_context,
            lambda: interactive_chart(result, specification, branding),
            key=f"{prefix}_{result.kind}_chart_{index}",
        )
        if specification.kind == "stacked_bar":
            st.warning(
                "As barras empilham presenças por quadro, com possível sobreposição. "
                "A altura da pilha não é o total de pessoas distintas; consulte o "
                "gráfico do total e a tabela da mesma competência ou semestre."
            )
        with st.expander("Ver tabela do gráfico"):
            _display(table)
            _table_download(result, table, generated_at, export_context, key=csv_key)
    return f"{result.kind}/grafico-{index + 1}.png", png


def _render_result(
    result: CalculatedAnalysis,
    branding: Branding,
    generated_at: datetime,
    *,
    prefix: str = "suite",
    export_context: dict[str, str] | None = None,
) -> dict[str, Callable[[], bytes]]:
    st.subheader(result.title)
    st.caption(f"{result.kind} · Situação: {result.status} · Origem: {result.source}")
    with st.container(key=f"vrac-narrative-{prefix}-{result.kind}"):
        st.write(result.narrative)
    if result.metrics:
        with st.container(key=f"vrac-metrics-{prefix}-{result.kind}"):
            columns = st.columns(min(len(result.metrics), 5))
            for index, metric in enumerate(result.metrics):
                with columns[index % len(columns)]:
                    st.metric(
                        metric.label,
                        "—" if metric.value is None else _format(metric.value),
                        help=f"{metric.unit}. {metric.status}. {metric.note}",
                    )
    urgent = result.status in {"Bloqueado", "Parcial"}

    def notes() -> None:
        with st.expander("Regras, avisos e limitações", expanded=urgent):
            for note in result.notes:
                st.write(f"• {note}")

    if urgent:
        notes()
    images = {}
    visible = []
    for index, specification in enumerate(result.charts):
        table = next(t for t in result.tables if t.key == specification.table)
        if table.rows and any(
            row[table.columns.index(s)] is not None
            for row in table.rows
            for s in specification.series
        ):
            visible.append((index, specification))
    # Séries mensais precisam da largura toda; as demais ficam duas por linha.
    wide = [item for item in visible if item[1].table == "monthly_history"]
    narrow = [item for item in visible if item[1].table != "monthly_history"]
    charted: set[str] = set()

    def card(index: int, specification: ChartSpec) -> None:
        # Uma tabela pode alimentar dois gráficos; a primeira chave segue a da tabela.
        csv_key = f"{prefix}_{result.kind}_{specification.table}_csv"
        name, build = _chart_card(
            result,
            specification,
            index,
            branding,
            generated_at,
            prefix=prefix,
            export_context=export_context,
            csv_key=f"{csv_key}_{index}" if specification.table in charted else csv_key,
        )
        charted.add(specification.table)
        images[name] = build

    for index, specification in wide:
        card(index, specification)
    for start in range(0, len(narrow), 2):
        pair = narrow[start : start + 2]
        targets = st.columns(2, gap="medium") if len(pair) == 2 else [st.container()]
        for target, (index, specification) in zip(targets, pair, strict=True):
            with target:
                card(index, specification)
    if visible:
        st.caption(
            "Passe o cursor sobre o gráfico para ler os valores. Nos gráficos com várias séries, "
            "clique na legenda para destacar (Shift permite várias) e clique duas vezes para "
            "limpar. O destaque não altera filtros, totais, tabelas ou downloads. Para os "
            "números completos, abra Ver tabela do gráfico."
        )
    summary = summary_table(result)
    tables = [
        table
        for table in (*((summary,) if summary.rows else ()), *result.tables)
        if table.key not in charted
    ]
    if tables:
        title = "Outras tabelas e arquivos" if visible else "Tabelas e arquivos"
        st.html(f'<div class="vrac-subtitle">{title}</div>')
    for table in tables:
        # Sem gráfico, a tabela é o próprio resultado e não fica escondida.
        with st.expander(table.title, expanded=not visible):
            _display(table)
            _table_download(
                result,
                table,
                generated_at,
                export_context,
                key=f"{prefix}_{result.kind}_{table.key}_csv",
            )
    if not urgent:
        notes()
    return images


def _render_overview(
    source: AcademicSource,
    filters: AnalysisFilters,
    branding: Branding,
    generated_at: datetime,
    export_context: dict[str, str],
    prefix: str,
) -> tuple[dict[str, bytes | Callable[[], bytes]], dict[str, str]]:
    if "register" not in source.available:
        st.error("R01 indisponível: o cadastro docente não pôde ser consultado neste snapshot.")
        return (
            {
                "R01/indisponivel.txt": (
                    b"DEMONSTRACAO: cadastro docente indisponivel; sem resultado."
                )
            },
            {"kind": "R01", "status": "indisponível"},
        )
    requested = OverviewFilters(
        frozenset(filters.cadres) if filters.cadres else None,
        frozenset(filters.categories) if filters.categories else None,
    )
    # O formulário compartilhado inclui domínios históricos: valores sem cadastro
    # atual correspondem a nenhuma linha da R01, sem bloquear outros roteiros.
    options = filter_options(source.faculty)
    effective = OverviewFilters(
        requested.cadres & set(options.cadres) if requested.cadres is not None else None,
        requested.categories & set(options.categories)
        if requested.categories is not None
        else None,
    )
    result = replace(compute_overview(source.faculty, effective), filters=requested)
    export_context = export_context | {
        "Snapshot": result.fingerprint,
        "Versão dos dados": result.version,
    }
    if requested != effective:
        st.info(
            "R01: seleções sem correspondência no cadastro atual não acrescentam vínculos. "
            "O histórico mantém seu domínio e sua referência próprios."
        )
    st.subheader("R01 · Situação geral do departamento")
    if result.status == "partial":
        st.warning("Parcial — composição calculada; fonte de Horas Reais indisponível.")
    st.caption(
        "Referência: cadastro atual; categoria e departamento contam linhas com matrícula; "
        "total e quadro contam matrículas funcionais distintas. Horas Reais: "
        "maior semestre por vínculo. Atualização da fonte: não disponível."
    )
    st.write(result.narrative)
    if result.total is not None:
        render_faculty_metric(result, prefix=prefix)
    for note in result.warnings:
        st.caption(note)
    files = {
        "R01/resumo.csv": summary_csv(result, generated_at, export_context),
        "R01/lista-conferencia.csv": detail_csv(result, generated_at, export_context),
    }
    files.update(
        render_composition(result, branding, prefix=f"{prefix}_r01", export_context=export_context)
    )
    render_faculty_details(result)
    for name, data in tuple(files.items()):
        if name.endswith(".csv"):
            download_button(
                "Baixar " + name.removeprefix("R01/"),
                data,
                file_name="vrac-" + name.replace("/", "-"),
                mime="text/csv",
                key=f"{prefix}_{name}",
            )
    st.caption(
        "A referência da R01 é o cadastro atual. A R02 trata separadamente o grupo QP simulado."
    )
    return files, {
        "kind": "R01",
        "status": OVERVIEW_STATUS[result.status],
        "source": result.source,
        "version": result.version,
        "fingerprint": result.fingerprint,
    }


def _request_complete_report() -> None:
    """Executado antes dos widgets: o relatório completo vive em Docentes."""
    st.session_state[VIEW_KEY] = FACULTY.tab
    st.session_state[FACULTY_PICKER] = ALL_FACULTY
    st.session_state.pop("suite_pdf_analyses", None)
    st.session_state["suite_autorun"] = True


def export_box(
    target,
    *,
    prefix: str,
    available: tuple[str, ...],
    package: Callable[[tuple[str, ...] | None], bytes],
    branding: Branding,
    generated_at: datetime,
) -> None:
    """Bloco único de exportação, no topo dos resultados de todas as telas.

    PDF e ZIP são montados só no clique, a partir do mesmo pacote.
    """
    pdf_key = f"{prefix}_pdf_analyses"
    if pdf_key in st.session_state:
        st.session_state[pdf_key] = [k for k in st.session_state[pdf_key] if k in available]
    stamp = f"{generated_at:%Y%m%d-%H%M%S}"
    with target, st.container(border=True, key=f"vrac-export-{prefix}"):
        card_title(
            "Baixar relatório",
            "PDF em formato de apresentação, com resultados e gráficos. "
            "ZIP com todas as tabelas, gráficos e conferências.",
        )
        chosen = tuple(
            st.multiselect(
                "Análises incluídas no PDF",
                available,
                default=None if pdf_key in st.session_state else available,
                format_func=lambda k: f"{k} · {TITLES.get(k, 'Situação geral do departamento')}",
                key=pdf_key,
                placeholder="Escolha ao menos uma análise",
            )
        )
        with st.container(horizontal=True, vertical_alignment="center"):
            if chosen:
                complete = len(chosen) == len(COMPLETE_CODES)
                download_button(
                    "Baixar relatório completo (PDF)"
                    if complete
                    else "Baixar relatório das análises selecionadas (PDF)",
                    lambda: report_pdf(package(chosen), branding, selected=chosen),
                    file_name=f"vrac-{'-'.join(chosen)}-{stamp}.pdf",
                    mime="application/pdf",
                    key=f"{prefix}_download_pdf_" + "_".join(chosen),
                    type="primary",
                    on_click="ignore",
                )
            download_button(
                "Baixar pacote (ZIP)",
                package,
                file_name=f"vrac-analises-sinteticas-{stamp}.zip",
                mime="application/zip",
                key=f"{prefix}_download_all",
                on_click="ignore",
            )
            if set(available) != set(COMPLETE_CODES):
                st.button(
                    "Preparar relatório completo (R01–R06)",
                    key=f"{prefix}_complete_report",
                    type="tertiary",
                    on_click=_request_complete_report,
                    help="Abre Docentes › Relatório completo e calcula os seis roteiros "
                    "com o recorte de Docentes.",
                )
        if not chosen:
            st.caption("Escolha ao menos uma análise para liberar o PDF; o ZIP segue disponível.")


def workbench(
    settings: Settings,
    branding: Branding,
    options: DemoOptions,
    *,
    codes: tuple[str, ...],
    label: str,
    prefix: str = "suite",
    active: bool = True,
) -> None:
    """Recorte, filtros e resultados das análises escolhidas na aba.

    A base é lida automaticamente quando a aba está aberta; fora dela, só o recorte
    é desenhado, para preservar as escolhas sem consultar a origem.
    """
    kinds = frozenset(codes)
    with st.container(key=f"vrac-panel-{prefix}-filters"):
        step(1, "Defina o recorte")
        try:
            hierarchy = load_department_hierarchy(settings)
        except DemoDataError as error:
            _clear(source=True, prefix=prefix)
            st.error(str(error))
            return
        scope = organisation_filters(
            hierarchy, prefix=prefix, department_label="Departamento das análises"
        )
        department = scope.department
        source_key = (settings.demo_source, scope)
        if st.session_state.get(f"{prefix}_source_key") != source_key:
            _clear(source=True, prefix=prefix)
            st.session_state[f"{prefix}_source_key"] = source_key
        if active and f"{prefix}_source" not in st.session_state:
            try:
                with st.spinner("Lendo as fontes sintéticas..."):
                    st.session_state[f"{prefix}_source"] = load_academic_source(
                        settings, **scope.source_arguments
                    )
                    st.session_state[f"{prefix}_loaded_at"] = datetime.now(UTC)
            except (DemoDataError, ValueError) as error:
                st.error(str(error))
                return
        source: AcademicSource | None = st.session_state.get(f"{prefix}_source")
        if source is None:
            return
        loaded_at = st.session_state[f"{prefix}_loaded_at"]
        with st.container(horizontal=True, vertical_alignment="center"):
            st.caption(f"Dados sintéticos lidos em {loaded_at:%d/%m/%Y %H:%M:%S} UTC.")
            # O clique descarta a base; a aba aberta lê de novo na mesma execução.
            st.button(
                "Atualizar dados",
                key=f"{prefix}_load",
                type="tertiary",
                on_click=_clear,
                kwargs={"source": True, "prefix": prefix},
                help=(
                    "Lê novamente somente a origem sintética selecionada. "
                    "Uma atualização remove o cálculo anterior."
                ),
            )
        for text in source.errors:
            st.warning(text)
        checks = inspect_source(source)
        step(2, "Refine os filtros, se precisar, e calcule")
        filters = _filters(source, kinds, prefix)
        descriptions = {
            "Centro": scope.center,
            "Departamento": department,
            "Departamentos efetivos": ", ".join(scope.departments),
            "Origem": source.faculty.source,
            "Referência inicial": filters.first_period,
            "Referência final": filters.last_period,
            "Semestre da carga": filters.workload_period,
            "Grupo QP selecionado": ", ".join(filters.qp_cadres) or "Não selecionado",
            "Quadros": ", ".join(filters.cadres) or "Todos",
            "Categorias": ", ".join(filters.categories) or "Todas",
            "Cursos": ", ".join(filters.courses) or "Todos",
            "Habilitações": ", ".join(filters.qualifications) or "Todas",
            "Turnos": ", ".join(filters.shifts) or "Todos",
            "Níveis": ", ".join(filters.levels) or "Todos",
            "Formas de ingresso": ", ".join(filters.entry_kinds) or "Todas",
        }
        key = (codes, source.fingerprint, filters)
        if st.session_state.get(f"{prefix}_result_key") != key:
            _clear(prefix=prefix)
        with st.container(horizontal=True, vertical_alignment="center"):
            run = st.button("Calcular resultados", type="primary", key=f"{prefix}_run")
            st.button(
                "Limpar filtros",
                key=f"{prefix}_reset_filters",
                type="tertiary",
                on_click=_reset_filters,
                args=(prefix,),
                help="Restaura o intervalo completo e as seleções iniciais, "
                "mantendo a base carregada.",
            )
        run = st.session_state.pop(f"{prefix}_autorun", False) or run
        review, quality = st.columns(2, gap="medium")
        with review, st.expander("Conferir filtros selecionados", expanded=False):
            st.markdown(
                "| Filtro | Valor |\n|---|---|\n"
                + "\n".join(
                    f"| {name} | {str(value).replace('|', ' / ').replace(chr(10), ' ')} |"
                    for name, value in descriptions.items()
                )
            )
        with quality, st.expander("Qualidade e cobertura dos dados", expanded=False):
            st.caption(
                "Conferências sobre o snapshot completo, antes dos filtros de análise; "
                "não aprovam regras institucionais."
            )
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Código": c.identifier,
                            "Motivo para conferência": c.description,
                            "Evidência: ocorrências": c.count,
                            "Tipo": c.level,
                            "Limitação e tratamento": c.consequence,
                        }
                        for c in checks
                    ]
                ).map(_format),
                hide_index=True,
                width="stretch",
            )
    if run:
        try:
            with st.spinner("Calculando as análises..."):
                results = tuple(
                    calculate(AnalysisKind(code), source, filters)
                    for code in codes
                    if code != "R01"
                )
                st.session_state[f"{prefix}_results"] = results
                st.session_state[f"{prefix}_result_key"] = key
                st.session_state[f"{prefix}_generated"] = datetime.now(UTC)
                st.session_state[f"{prefix}_execution_id"] = str(uuid4())
        except ValueError as error:
            _clear(prefix=prefix)
            st.error(str(error))
            return
    results = st.session_state.get(f"{prefix}_results")
    if results is None:
        with st.container(key=f"vrac-empty-{prefix}"):
            st.info(
                "Recorte pronto. Clique em Calcular resultados para ver os gráficos "
                "e liberar os arquivos deste recorte."
            )
        return
    generated_at = st.session_state[f"{prefix}_generated"]
    panel = st.container(key=f"vrac-panel-{prefix}-results")
    panel.subheader("Resultados calculados")
    panel.caption(
        f"Recorte: {scope.label} · {filters.first_period} a {filters.last_period}. "
        "Os resultados abaixo correspondem ao último cálculo com estes filtros."
    )
    with panel.expander("Filtros usados neste resultado", expanded=False):
        st.table(
            pd.DataFrame([{"Filtro": name, "Valor": value} for name, value in descriptions.items()])
        )
        st.caption(
            f"Versão dos dados: {source.faculty.version} · snapshot {source.fingerprint[:12]} · "
            f"extração {loaded_at:%d/%m/%Y %H:%M:%S} UTC · "
            f"cálculo {generated_at:%d/%m/%Y %H:%M:%S} UTC · atualização da fonte: não disponível"
        )
    export_context = {
        "Execução": st.session_state[f"{prefix}_execution_id"],
        **descriptions,
        "Extração (UTC)": loaded_at.isoformat(),
        "Cálculo (UTC)": generated_at.isoformat(),
        "Versão dos dados": source.faculty.version,
        "Snapshot acadêmico": source.fingerprint,
        "Atualização da fonte": "não disponível",
    }
    export_slot = panel.container()
    show_overview = "R01" in kinds
    labels = (["R01 · Situação geral"] if show_overview else []) + [
        f"{r.kind} · {r.title}" for r in results
    ]
    # Uma análise só dispensa abas internas; várias ficam lado a lado.
    tabs = panel.tabs(labels) if len(labels) > 1 else [panel.container()]
    files, images = {}, {}
    quality_rows = [asdict(c) for c in checks]
    files["conferencias-programadas.csv"] = _write(
        [["Contexto", key, value] for key, value in export_context.items()]
        + [[]]
        + [["Natureza", "Snapshot", *quality_rows[0]]]
        + [
            ["DEMONSTRAÇÃO — dados sintéticos", source.fingerprint, *row.values()]
            for row in quality_rows
        ]
    )
    overview_manifest = None
    if show_overview:
        with tabs[0]:
            overview_files, overview_manifest = _render_overview(
                source, filters, branding, generated_at, export_context, prefix
            )
            files.update(overview_files)
    for tab, result in zip(tabs[1:] if show_overview else tabs, results, strict=True):
        with tab:
            images.update(
                _render_result(
                    result, branding, generated_at, prefix=prefix, export_context=export_context
                )
            )

    def package(include: tuple[str, ...] | None = None) -> bytes:
        """Montado no clique: desenha os gráficos só para quem pedir o pacote."""

        def included(name: str) -> bool:
            return include is None or name.split("/")[0] in include

        return report_zip(
            tuple(r for r in results if include is None or r.kind in include),
            generated_at,
            {name: build() for name, build in images.items() if included(name)},
            {
                name: data() if callable(data) else data
                for name, data in files.items()
                if included(name)
            },
            export_context,
            additional_analyses=(overview_manifest,)
            if overview_manifest and (include is None or "R01" in include)
            else (),
        )

    export_box(
        export_slot,
        prefix=prefix,
        available=(*(("R01",) if show_overview else ()), *(str(r.kind) for r in results)),
        package=package,
        branding=branding,
        generated_at=generated_at,
    )
    status = "; ".join(
        ([f"R01: {overview_manifest['status']}"] if overview_manifest else [])
        + [f"{r.kind}: {r.status}" for r in results]
    )
    _render_verification(settings, label, kinds, scope, filters, source, prefix)
    render_feedback(
        st.session_state[f"{prefix}_execution_id"], label, status, generated_at, prefix=prefix
    )
    if run:
        scroll_to(f"vrac-panel-{prefix}-results")


def _render_verification(
    settings: Settings,
    label: str,
    kinds: frozenset[str],
    scope: OrganisationScope,
    filters: AnalysisFilters,
    source: AcademicSource,
    prefix: str,
) -> None:
    from vrac.db.synthetic_postgres import query_missing_classification

    if "R04" not in kinds:
        return
    if settings.demo_source == DemoSource.SUPABASE:
        st.caption(
            "E01 experimental disponível somente na base local; "
            "conferências do snapshot preservadas."
        )
        return

    with st.expander("Pontos para conferência adicionais — experimento sintético"):
        st.caption(
            "As dez conferências de qualidade acima usam o snapshot já carregado. "
            "Este aprofundamento pode consultar novamente o PostgreSQL sintético; "
            "a identidade local simulada não substitui acesso institucional."
        )
        st.write(
            "E01 v1 · Classificação ausente em alocações no semestre e departamentos "
            "selecionados. A consulta é experimental, sem regra institucional aprovada. "
            "Limites: uma verificação, até cinco departamentos e 5.000 alocações; "
            "até 61 comandos de leitura incluindo a revalidação, com até 5 segundos por comando."
        )
        enabled = st.checkbox("Habilitar E01 para esta demonstração", key=f"{prefix}_check_enable")
        mode = st.radio(
            "Modo de execução", ("Sob aprovação", "Automático"), key=f"{prefix}_check_mode"
        )
        session = st.session_state.setdefault(f"{prefix}_verification", VerificationSession())
        context = Context(
            identity=IDENTITY,
            analysis=label,
            filters=filters,
            department=scope.label,
            departments=scope.departments,
            source_arguments=tuple(sorted(scope.source_arguments.items())),
            reference=source.fingerprint,
        )
        session.select(context)
        applicable = "allocations" in source.available
        outcome = session.run(
            settings,
            automatic=False,
            enabled=frozenset(),
            applicable=applicable,
            query=lambda ctx: query_missing_classification(settings, ctx),
        )
        existing = session.outcomes.get(RULE_ID)
        if existing is not None:
            outcome = existing
        if enabled and mode == "Sob aprovação" and outcome.status == Status.SUGGESTED:
            approve, decline = st.columns(2)
            if approve.button("Autorizar consulta experimental", key=f"{prefix}_check_approve"):
                session.decide(True)
                outcome = session.outcomes[RULE_ID]
            if decline.button("Recusar consulta", key=f"{prefix}_check_decline"):
                session.decide(False)
                outcome = session.outcomes[RULE_ID]
        execute = enabled and mode == "Automático"
        if enabled and mode == "Sob aprovação" and outcome.status == Status.APPROVED:
            execute = st.button("Executar consulta autorizada", key=f"{prefix}_check_execute")
        if execute:
            outcome = session.run(
                settings,
                automatic=mode == "Automático",
                enabled=frozenset({RULE_ID}),
                applicable=applicable,
                query=lambda ctx: query_missing_classification(settings, ctx),
            )
        st.write(f"Estado: **{outcome.status.value}**. {outcome.reason}")
        if outcome.evidence:
            st.write(f"Evidência: {outcome.evidence}")
        if outcome.limitation:
            st.write(f"Limitação: {outcome.limitation}")
