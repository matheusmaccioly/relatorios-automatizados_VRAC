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
from vrac.organisation_ui import OrganisationScope, organisation_filters
from vrac.settings import DemoSource, Settings
from vrac.ui_kit import card_title, data_table, download_button, scroll_to, show_chart, step
from vrac.web_charts import interactive_chart

ALL_ANALYSES = "Todos os roteiros (R01–R06)"

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

# Filtros que cada análise realmente usa; a visão conjunta (None) mostra todos.
# Os ocultos mantêm o valor inicial do formulário, sem alterar o cálculo daquela análise.
INTERVAL_ANALYSES = {None, "R03", "R05", "R06"}
WORKLOAD_ANALYSES = {None, "R04"}
CADRE_ANALYSES = {None, "R01", "R03", "R04", "R05"}
CATEGORY_ANALYSES = {None, "R01", "R02", "R03", "R04", "R05"}
QP_ANALYSES = {None, "R02"}
ACADEMIC_ANALYSES = {None, "R06"}

FILTER_WIDGET_KEYS = (
    "suite_first",
    "suite_last",
    "suite_workload_period",
    "suite_cadres",
    "suite_categories",
    "suite_qp",
    "suite_courses",
    "suite_qualifications",
    "suite_shifts",
    "suite_levels",
    "suite_entries",
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


def _clear(*, source: bool = False) -> None:
    for key in (
        "suite_results",
        "suite_result_key",
        "suite_generated",
        "suite_overview",
        "suite_verification",
        "suite_execution_id",
    ):
        st.session_state.pop(key, None)
    if source:
        st.session_state.pop("suite_source", None)
        st.session_state.pop("suite_loaded_at", None)


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
    return tuple(st.multiselect(label, sorted(options), key=key, placeholder="Todos"))


def _reset_filters() -> None:
    """Limpa somente o recorte analítico, preservando a origem explicitamente carregada."""
    _clear()
    for key in FILTER_WIDGET_KEYS:
        st.session_state.pop(key, None)


def _filters(source: AcademicSource, selected_kind: str | None = None) -> AnalysisFilters:
    periods = source.periods
    first_period, last_period, workload_period = periods[0], periods[-1], periods[-1]
    st.caption(
        "Seleções vazias incluem todos os valores disponíveis. "
        "Ao mudar um filtro, calcule novamente para atualizar resultados e arquivos."
    )
    show_interval = selected_kind in INTERVAL_ANALYSES
    show_workload = selected_kind in WORKLOAD_ANALYSES
    if show_interval or show_workload:
        fields = iter(st.columns(3 if show_interval and show_workload else 2))
    if show_interval:
        with next(fields):
            first_period = st.selectbox(
                "Semestre inicial",
                periods,
                key="suite_first",
                help="Início do intervalo usado no histórico docente, funções e matrículas.",
            )
        with next(fields):
            last_period = st.selectbox(
                "Semestre final",
                periods,
                index=len(periods) - 1,
                key="suite_last",
                help="Fim do intervalo, incluindo o semestre selecionado.",
            )
    if show_workload:
        with next(fields):
            workload_period = st.selectbox(
                "Semestre da carga horária",
                periods,
                index=len(periods) - 1,
                key="suite_workload_period",
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
    if selected_kind in CATEGORY_ANALYSES:
        with st.expander(
            "Filtros docentes e grupo de comparação",
            expanded=selected_kind in {"R01", "R02", "R03", "R04", "R05"},
        ):
            first, second = st.columns(2)
            if selected_kind in CADRE_ANALYSES:
                with first:
                    staff_cadres = _pick("Quadros docentes", cadres, "suite_cadres")
            with second if selected_kind in CADRE_ANALYSES else first:
                staff_categories = _pick("Categorias funcionais", categories, "suite_categories")
            if selected_kind in QP_ANALYSES:
                qp_options = sorted({r.cadre for r in source.faculty.register if r.cadre})
                defaults = [x for x in qp_options if x in {"PROF PRINCIPAL", "PRINCIPAL"}]
                if "suite_qp" in st.session_state:
                    st.session_state["suite_qp"] = [
                        x for x in st.session_state["suite_qp"] if x in qp_options
                    ]
                else:
                    st.session_state["suite_qp"] = defaults
                qp = tuple(
                    st.multiselect(
                        "Quadros do grupo QP — simulação configurável",
                        qp_options,
                        key="suite_qp",
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
    if selected_kind in ACADEMIC_ANALYSES:
        with st.expander("Filtros acadêmicos", expanded=selected_kind == "R06"):
            student_rows = (*source.students, *source.student_history)
            courses = _pick(
                "Cursos (códigos separados)", {r.course for r in student_rows}, "suite_courses"
            )
            first, second = st.columns(2)
            with first:
                qualifications = _pick(
                    "Habilitações",
                    {r.qualification for r in student_rows if r.qualification},
                    "suite_qualifications",
                )
                levels = _pick("Níveis", {r.level for r in student_rows if r.level}, "suite_levels")
            with second:
                shifts = _pick("Turnos", {r.shift for r in student_rows if r.shift}, "suite_shifts")
                entries = _pick(
                    "Formas de ingresso",
                    {r.entry_kind for r in student_rows if r.entry_kind},
                    "suite_entries",
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
        render_faculty_metric(result, prefix="suite")
    for note in result.warnings:
        st.caption(note)
    files = {
        "R01/resumo.csv": summary_csv(result, generated_at, export_context),
        "R01/lista-conferencia.csv": detail_csv(result, generated_at, export_context),
    }
    files.update(
        render_composition(result, branding, prefix="suite_r01", export_context=export_context)
    )
    render_faculty_details(result)
    for name, data in tuple(files.items()):
        if name.endswith(".csv"):
            download_button(
                "Baixar " + name.removeprefix("R01/"),
                data,
                file_name="vrac-" + name.replace("/", "-"),
                mime="text/csv",
                key="suite_" + name,
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


def workbench(settings: Settings, branding: Branding, options: DemoOptions) -> None:
    names = analysis_names()
    with st.container(key="vrac-panel-suite-filters"):
        st.subheader("Análises disponíveis por período")
        step(1, "Escolha a análise")
        selected = st.selectbox(
            "Análise",
            (ALL_ANALYSES, *names),
            key="suite_analysis",
            help="Escolha uma consulta para começar ou calcule os seis roteiros em conjunto.",
        )
        selected_kind = names.get(selected)
        if selected_kind is not None:
            question, explanation = ANALYSIS_GUIDE[selected_kind]
            st.markdown(f"**{question}**")
            st.caption(explanation)
        else:
            st.caption(
                "Visão conjunta: composição docente, comparação QP, histórico, carga horária, "
                "funções e matrículas. Cada análise informa sua referência e suas limitações."
            )
        step(2, "Defina o recorte")
        try:
            hierarchy = load_department_hierarchy(settings)
        except DemoDataError as error:
            _clear(source=True)
            st.error(str(error))
            return
        scope = organisation_filters(
            hierarchy, prefix="suite", department_label="Departamento das análises"
        )
        department = scope.department
        source_key = (settings.demo_source, scope)
        if st.session_state.get("suite_source_key") != source_key:
            # Com a base já aberta, trocar a unidade recarrega sem exigir outro clique.
            reload_source = "suite_source" in st.session_state
            _clear(source=True)
            st.session_state["suite_source_key"] = source_key
            if reload_source:
                st.session_state["suite_autoload"] = True
        loaded = "suite_source" in st.session_state
        clicked = st.button(
            "Atualizar dados" if loaded else "Carregar dados",
            key="suite_load",
            type="tertiary" if loaded else "primary",
            help=(
                "Lê somente a origem sintética selecionada. "
                "Uma atualização remove o cálculo anterior."
            ),
        )
        automatic = st.session_state.pop("suite_autoload", False) and not loaded
        if clicked or automatic:
            _clear(source=True)
            try:
                with st.spinner("Lendo as fontes sintéticas..."):
                    st.session_state["suite_source"] = load_academic_source(
                        settings, **scope.source_arguments
                    )
                    st.session_state["suite_loaded_at"] = datetime.now(UTC)
            except (DemoDataError, ValueError) as error:
                st.error(str(error))
                return
        source: AcademicSource | None = st.session_state.get("suite_source")
        if source is None:
            st.info(
                "Próximo passo: clique em Carregar dados. "
                "Depois você poderá escolher os semestres e refinar os filtros."
            )
            return
        loaded_at = st.session_state["suite_loaded_at"]
        st.caption(
            f"Snapshot sintético carregado em {loaded_at:%d/%m/%Y %H:%M:%S} UTC. "
            "Use atualizar dados para consultar uma nova versão da base."
        )
        for text in source.errors:
            st.warning(text)
        checks = inspect_source(source)
        step(3, "Refine os filtros e calcule")
        filters = _filters(source, selected_kind)
        descriptions = {
            "Centro": scope.center,
            "Departamento": department,
            "Departamentos efetivos": ", ".join(scope.departments),
            "Origem": source.faculty.source,
            "Referência inicial": filters.first_period,
            "Referência final": filters.last_period,
            "Semestre da carga": filters.workload_period,
            "Grupo QP simulado": ", ".join(filters.qp_cadres) or "Não selecionado",
            "Quadros": ", ".join(filters.cadres) or "Todos",
            "Categorias": ", ".join(filters.categories) or "Todas",
            "Cursos": ", ".join(filters.courses) or "Todos",
            "Habilitações": ", ".join(filters.qualifications) or "Todas",
            "Turnos": ", ".join(filters.shifts) or "Todos",
            "Níveis": ", ".join(filters.levels) or "Todos",
            "Formas de ingresso": ", ".join(filters.entry_kinds) or "Todas",
        }
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
        key = (selected, source.fingerprint, filters)
        if st.session_state.get("suite_result_key") != key:
            _clear()
        with st.container(horizontal=True, vertical_alignment="center"):
            run = st.button("Calcular análises selecionadas", type="primary", key="suite_run")
            st.button(
                "Limpar filtros",
                key="suite_reset_filters",
                type="tertiary",
                on_click=_reset_filters,
                help="Restaura o intervalo completo e as seleções iniciais, "
                "mantendo a base carregada.",
            )
    if run:
        try:
            with st.spinner("Calculando os roteiros..."):
                kinds = (
                    tuple(AnalysisKind)
                    if selected == ALL_ANALYSES
                    else (() if names[selected] == "R01" else (names[selected],))
                )
                results = tuple(calculate(kind, source, filters) for kind in kinds)
                st.session_state["suite_results"] = results
                st.session_state["suite_result_key"] = key
                st.session_state["suite_generated"] = datetime.now(UTC)
                st.session_state["suite_execution_id"] = str(uuid4())
        except ValueError as error:
            _clear()
            st.error(str(error))
            return
    results = st.session_state.get("suite_results")
    if results is None:
        with st.container(key="vrac-empty-suite"):
            st.info(
                "Recorte pronto para consulta. Clique em Calcular análises selecionadas "
                "para ver os resultados e liberar os arquivos deste recorte."
            )
        return
    generated_at = st.session_state["suite_generated"]
    panel = st.container(key="vrac-panel-suite-results")
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
        "Execução": st.session_state["suite_execution_id"],
        **descriptions,
        "Extração (UTC)": loaded_at.isoformat(),
        "Cálculo (UTC)": generated_at.isoformat(),
        "Versão dos dados": source.faculty.version,
        "Snapshot acadêmico": source.fingerprint,
        "Atualização da fonte": "não disponível",
    }
    show_overview = selected == ALL_ANALYSES or names.get(selected) == "R01"
    labels = (["R01 · Situação geral"] if show_overview else []) + [
        f"{r.kind} · {r.title}" for r in results
    ]
    tabs = panel.tabs(labels)
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
                source, filters, branding, generated_at, export_context
            )
            files.update(overview_files)
    for tab, result in zip(tabs[1:] if show_overview else tabs, results, strict=True):
        with tab:
            images.update(
                _render_result(result, branding, generated_at, export_context=export_context)
            )

    def package() -> bytes:
        """Montado no clique: desenha os gráficos só para quem pedir o pacote."""
        return report_zip(
            results,
            generated_at,
            {name: build() for name, build in images.items()},
            {name: data() if callable(data) else data for name, data in files.items()},
            export_context,
            additional_analyses=(overview_manifest,) if overview_manifest else (),
        )

    with panel:
        download_button(
            "Baixar pacote das análises (ZIP)",
            package,
            file_name=f"vrac-analises-sinteticas-{generated_at:%Y%m%d-%H%M%S}.zip",
            mime="application/zip",
            key="suite_download_all",
            on_click="ignore",
        )
    status = "; ".join(
        ([f"R01: {overview_manifest['status']}"] if overview_manifest else [])
        + [f"{r.kind}: {r.status}" for r in results]
    )
    _render_verification(settings, selected, scope, filters, source)
    render_feedback(st.session_state["suite_execution_id"], selected, status, generated_at)
    if run:
        scroll_to("vrac-panel-suite-results")


def _render_verification(
    settings: Settings,
    selected: str,
    scope: OrganisationScope,
    filters: AnalysisFilters,
    source: AcademicSource,
) -> None:
    from vrac.db.synthetic_postgres import query_missing_classification

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
        enabled = st.checkbox("Habilitar E01 para esta demonstração", key="suite_check_enable")
        mode = st.radio("Modo de execução", ("Sob aprovação", "Automático"), key="suite_check_mode")
        session = st.session_state.setdefault("suite_verification", VerificationSession())
        context = Context(
            identity=IDENTITY,
            analysis=selected,
            filters=filters,
            department=scope.label,
            departments=scope.departments,
            source_arguments=tuple(sorted(scope.source_arguments.items())),
            reference=source.fingerprint,
        )
        session.select(context)
        applicable = (
            selected == ALL_ANALYSES or selected.startswith("R04 ·")
        ) and "allocations" in source.available
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
            if approve.button("Autorizar consulta experimental", key="suite_check_approve"):
                session.decide(True)
                outcome = session.outcomes[RULE_ID]
            if decline.button("Recusar consulta", key="suite_check_decline"):
                session.decide(False)
                outcome = session.outcomes[RULE_ID]
        execute = enabled and mode == "Automático"
        if enabled and mode == "Sob aprovação" and outcome.status == Status.APPROVED:
            execute = st.button("Executar consulta autorizada", key="suite_check_execute")
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
