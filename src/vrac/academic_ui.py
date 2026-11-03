"""Tela fechada dos roteiros acadêmicos calculados na demonstração local."""

from dataclasses import asdict, replace
from datetime import UTC, datetime

import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt

from vrac.analyses.academic import (
    TITLES,
    AnalysisFilters,
    AnalysisKind,
    CalculatedAnalysis,
    calculate,
)
from vrac.analyses.academic_data import AcademicSource
from vrac.analyses.academic_export import report_zip, summary_table, table_csv
from vrac.analyses.academic_quality import inspect_source
from vrac.analyses.export import detail_csv, summary_csv
from vrac.analyses.faculty_overview import OverviewFilters, compute_overview, filter_options
from vrac.branding import Branding
from vrac.charts import academic_chart, figure_png
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
from vrac.organisation_ui import organisation_filters
from vrac.settings import Settings
from vrac.web_charts import interactive_chart

ALL_ANALYSES = "Todos os roteiros (R01–R06)"


def _clear(*, source: bool = False) -> None:
    for key in ("suite_results", "suite_result_key", "suite_generated", "suite_overview"):
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


def _display(table) -> None:
    if not table.rows:
        st.info("Sem registros para esta tabela no recorte selecionado.")
        return
    frame = pd.DataFrame(table.rows, columns=table.columns).map(_format)
    st.dataframe(frame, hide_index=True, width="stretch")
    st.caption(f"Unidade: {table.unit}. {table.note}")


def _pick(label: str, options: set[str], key: str) -> tuple[str, ...]:
    # Remover seleções que deixaram de existir quando a origem é recarregada.
    if key in st.session_state:
        st.session_state[key] = [x for x in st.session_state[key] if x in options]
    return tuple(st.multiselect(label, sorted(options), key=key, placeholder="Todos"))


def _filters(source: AcademicSource) -> AnalysisFilters:
    periods = source.periods
    first, last, workload = st.columns(3)
    with first:
        first_period = st.selectbox("Semestre inicial", periods, key="suite_first")
    with last:
        last_period = st.selectbox(
            "Semestre final", periods, index=len(periods) - 1, key="suite_last"
        )
    with workload:
        workload_period = st.selectbox(
            "Semestre da carga horária",
            periods,
            index=len(periods) - 1,
            key="suite_workload_period",
        )
    from vrac.analyses.faculty_overview import NOT_INFORMED

    cadres = {
        r.cadre or NOT_INFORMED
        for r in (*source.faculty.register, *source.history, *source.workloads)
    }
    categories = {r.category or NOT_INFORMED for r in (*source.faculty.register, *source.history)}
    with st.expander("Filtros docentes e grupo de comparação", expanded=False):
        staff_cadres = _pick("Quadros docentes", cadres, "suite_cadres")
        staff_categories = _pick("Categorias funcionais", categories, "suite_categories")
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
            "O grupo inicial é apenas um exemplo de simulação, sem definição institucional de QP. "
            "Seus quadros ficam registrados nos filtros e nas exportações. Na R03, o filtro "
            "de quadros controla as séries exibidas e preserva o total; "
            "na R04/R05 filtra a população."
            " Na R02, Quadros docentes não recorta o geral: use o grupo QP para a comparação."
        )
    with st.expander("Filtros acadêmicos", expanded=False):
        student_rows = (*source.students, *source.student_history)
        courses = _pick(
            "Cursos (códigos separados)", {r.course for r in student_rows}, "suite_courses"
        )
        qualifications = _pick(
            "Habilitações",
            {r.qualification for r in student_rows if r.qualification},
            "suite_qualifications",
        )
        shifts = _pick("Turnos", {r.shift for r in student_rows if r.shift}, "suite_shifts")
        levels = _pick("Níveis", {r.level for r in student_rows if r.level}, "suite_levels")
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


def _render_result(
    result: CalculatedAnalysis, branding: Branding, generated_at: datetime, *, prefix: str = "suite"
) -> dict[str, bytes]:
    st.subheader(result.title)
    st.caption(f"{result.kind} · Situação: {result.status} · Origem: {result.source}")
    st.write(result.narrative)
    if result.metrics:
        columns = st.columns(min(len(result.metrics), 4))
        for index, metric in enumerate(result.metrics):
            with columns[index % len(columns)]:
                st.metric(
                    metric.label,
                    "—" if metric.value is None else _format(metric.value),
                    help=f"{metric.unit}. {metric.status}. {metric.note}",
                )
    with st.expander(
        "Regras, avisos e limitações", expanded=result.status in {"Bloqueado", "Parcial"}
    ):
        for note in result.notes:
            st.write(f"• {note}")
    images = {}
    for index, specification in enumerate(result.charts):
        table = next(t for t in result.tables if t.key == specification.table)
        if not table.rows or all(
            row[table.columns.index(s)] is None for row in table.rows for s in specification.series
        ):
            continue
        figure = academic_chart(result, specification, branding)
        png = figure_png(figure)
        if result.kind == AnalysisKind.STUDENTS:
            st.pyplot(figure, width="stretch")
        else:
            with st.container(border=True):
                st.markdown(f"**{specification.title}**")
                st.altair_chart(
                    interactive_chart(result, specification, branding),
                    width="stretch",
                    theme=None,
                    key=f"{prefix}_{result.kind}_chart_{index}",
                )
                st.caption(
                    "Passe o cursor para valor, referência e unidade. Clique na legenda para "
                    "destacar séries (Shift permite várias); clique novamente para limpar. "
                    "O destaque não altera filtros, totais, tabelas ou downloads."
                )
                if specification.kind == "stacked_bar":
                    st.warning(
                        "As barras empilham presenças por quadro, com possível sobreposição. "
                        "A altura da pilha não é o total de pessoas distintas; consulte o "
                        "gráfico do total e a tabela da mesma competência ou semestre."
                    )
        plt.close(figure)
        filename = f"{result.kind}/grafico-{index + 1}.png"
        images[filename] = png
        st.download_button(
            "Baixar gráfico (PNG)",
            png,
            file_name=f"vrac-{result.kind}-grafico-{index + 1}.png",
            mime="image/png",
            key=f"{prefix}_{result.kind}_png_{index}",
        )
    for table in (summary_table(result), *result.tables):
        with st.expander(
            table.title, expanded=table.key in {"summary", "history", "students", "workload"}
        ):
            _display(table)
            st.download_button(
                "Baixar tabela (CSV)",
                table_csv(result, table, generated_at),
                file_name=f"vrac-{result.kind}-{table.key}.csv",
                mime="text/csv",
                key=f"{prefix}_{result.kind}_{table.key}_csv",
            )
    return images


def _render_overview(
    source: AcademicSource, filters: AnalysisFilters, branding: Branding, generated_at: datetime
) -> dict[str, bytes]:
    if "register" not in source.available:
        st.error("R01 indisponível: o cadastro docente não pôde ser consultado neste snapshot.")
        return {
            "R01/indisponivel.txt": b"DEMONSTRACAO: cadastro docente indisponivel; sem resultado."
        }
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
        render_faculty_metric(result)
    for note in result.warnings:
        st.caption(note)
    files = {
        "R01/resumo.csv": summary_csv(result, generated_at),
        "R01/lista-conferencia.csv": detail_csv(result, generated_at),
    }
    files.update(render_composition(result, branding, prefix="suite_r01"))
    render_faculty_details(result)
    for name, data in tuple(files.items()):
        if name.endswith(".csv"):
            st.download_button(
                "Baixar " + name.removeprefix("R01/"),
                data,
                file_name="vrac-" + name.replace("/", "-"),
                mime="text/csv",
                key="suite_" + name,
            )
    st.caption(
        "A referência da R01 é o cadastro atual. A R02 trata separadamente o grupo QP simulado."
    )
    return files


def workbench(settings: Settings, branding: Branding, options: DemoOptions) -> None:
    st.subheader("Análises disponíveis por período")
    st.info(
        "Carregue a base sintética e calcule um roteiro ou os seis em conjunto. "
        "Todos os resultados e arquivos permanecem identificados como demonstração."
    )
    names = {
        "R01 · Situação geral do departamento": "R01",
        **{f"{key} · {value}": key for key, value in TITLES.items()},
    }
    selected = st.selectbox("Análise", (ALL_ANALYSES, *names), key="suite_analysis")
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
        _clear(source=True)
        st.session_state["suite_source_key"] = source_key
    if st.button("Carregar ou atualizar dados", key="suite_load"):
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
        st.caption("Carregue os dados para escolher os filtros e calcular os roteiros.")
        return
    loaded_at = st.session_state["suite_loaded_at"]
    st.caption(
        f"Snapshot sintético carregado em {loaded_at:%d/%m/%Y %H:%M:%S} UTC. "
        "Use atualizar dados para consultar uma nova versão da base."
    )
    for text in source.errors:
        st.warning(text)
    checks = inspect_source(source)
    with st.expander("Qualidade e cobertura dos dados", expanded=False):
        st.caption(
            "Conferências sobre o snapshot completo, antes dos filtros de análise; "
            "não aprovam regras institucionais."
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Código": c.identifier,
                        "Conferência": c.description,
                        "Ocorrências": c.count,
                        "Tipo": c.level,
                        "Tratamento": c.consequence,
                    }
                    for c in checks
                ]
            ).map(_format),
            hide_index=True,
            width="stretch",
        )
    filters = _filters(source)
    key = (selected, source.fingerprint, filters)
    if st.session_state.get("suite_result_key") != key:
        _clear()
    if st.button("Calcular análises selecionadas", type="primary", key="suite_run"):
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
        except ValueError as error:
            _clear()
            st.error(str(error))
            return
    results = st.session_state.get("suite_results")
    if results is None:
        return
    generated_at = st.session_state["suite_generated"]
    st.subheader("Resultados calculados")
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
    st.table(pd.DataFrame([{"Filtro": key, "Valor": value} for key, value in descriptions.items()]))
    st.caption(
        f"Versão dos dados: {source.faculty.version} · snapshot {source.fingerprint[:12]} · "
        f"extração {loaded_at:%d/%m/%Y %H:%M:%S} UTC · "
        f"cálculo {generated_at:%d/%m/%Y %H:%M:%S} UTC · atualização da fonte: não disponível"
    )
    show_overview = selected == ALL_ANALYSES or names.get(selected) == "R01"
    labels = (["R01 · Situação geral"] if show_overview else []) + [
        f"{r.kind} · {r.title}" for r in results
    ]
    tabs = st.tabs(labels)
    files, images = {}, {}
    quality = pd.DataFrame([asdict(c) for c in checks])
    quality.insert(0, "Natureza", "DEMONSTRAÇÃO — dados sintéticos")
    quality.insert(1, "Snapshot", source.fingerprint)
    files["conferencias-programadas.csv"] = quality.to_csv(
        index=False, sep=";", na_rep="ausente"
    ).encode("utf-8-sig")
    if show_overview:
        with tabs[0]:
            files.update(_render_overview(source, filters, branding, generated_at))
    for tab, result in zip(tabs[1:] if show_overview else tabs, results, strict=True):
        with tab:
            images.update(_render_result(result, branding, generated_at))
    st.download_button(
        "Baixar pacote das análises (ZIP)",
        report_zip(results, generated_at, images, files),
        file_name=f"vrac-analises-sinteticas-{generated_at:%Y%m%d-%H%M%S}.zip",
        mime="application/zip",
        key="suite_download_all",
    )
