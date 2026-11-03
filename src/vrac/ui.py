"""Demonstração com origem sintética explícita e consultas locais de leitura."""

import hashlib
import json
import math
from dataclasses import asdict, replace
from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from vrac.academic_ui import _render_result, workbench
from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.export import detail_csv, summary_csv
from vrac.analyses.faculty_overview import (
    UNIT_LABEL,
    FacultyOverview,
    OverviewFilters,
    OverviewStatus,
    compute_overview,
    describe_filters,
    filter_options,
)
from vrac.authorization import authorize_data_access
from vrac.branding import Branding, load_branding
from vrac.demo_data import (
    DemoDataError,
    DemoOptions,
    faculty_history_periods,
    load_academic_source,
    load_demo_options,
    load_department_hierarchy,
    load_faculty_source,
    load_selected_demo,
)
from vrac.faculty_presentation import (
    render_composition,
    render_faculty_details,
    render_faculty_metric,
)
from vrac.organisation_ui import organisation_filters
from vrac.settings import ConfigurationError, Settings, load_settings

MISSING_LABEL = "ausente"

FACULTY_COLUMNS = {
    "department": "Departamento do vínculo",
    "period": "Período",
    "reference_month": "Mês de referência",
    "teacher_id": "Docente fictício",
    "contract_id": "Vínculo fictício",
    "employment_type": "Tipo de vínculo fictício",
    "real_hours": "Horas Reais fictícias (h/semana)",
}
ALLOCATION_COLUMNS = {
    "department": "Departamento do vínculo",
    "teaching_department": "Departamento da disciplina",
    "period": "Período",
    "teacher_id": "Docente fictício",
    "class_id": "Turma fictícia",
    "curriculum_id": "Currículo fictício",
    "sharing_id": "Compartilhamento fictício",
    "allocated_hours": "Horas alocadas fictícias (h/semana)",
    "students": "Matrículas fictícias",
    "classification": "Classificação fictícia",
}


def _display_value(value: object) -> str:
    """Ausente é exibido por texto e nunca vira zero; números em formato brasileiro."""
    if value is None or value is pd.NA or (isinstance(value, float) and math.isnan(value)):
        return MISSING_LABEL
    if isinstance(value, float | int) and not isinstance(value, bool):
        return str(value) if isinstance(value, int) else f"{value:g}".replace(".", ",")
    return str(value)


def _show_records(rows: list[dict], columns: dict[str, str]) -> None:
    """Tabela somente de exibição, sem agregação ou deduplicação dos registros."""
    if not rows:
        st.info("Sem registros sintéticos para esta tabela no recorte selecionado.")
        return
    frame = pd.DataFrame(rows)
    is_numeric = pd.api.types.is_numeric_dtype
    numeric = [columns[name] for name in frame.columns if is_numeric(frame[name])]
    display = frame.map(_display_value).rename(columns=columns)
    st.dataframe(
        display,
        hide_index=True,
        column_config={name: st.column_config.TextColumn(alignment="right") for name in numeric},
    )


def _header(branding: Branding) -> None:
    with st.container(key="vrac-header"):
        logo, title = st.columns([1, 4], vertical_alignment="center", gap="medium")
        with logo:
            st.image(
                str(branding.logo),
                width=branding.tokens["marks"]["display_width"],
                caption=None,
            )
        with title:
            st.html('<p class="vrac-eyebrow">PUC-Rio · VRAC</p>')
            st.title("Análises acadêmicas")
            st.caption(
                "Identidade visual aplicada aos materiais fornecidos · "
                "revisão institucional pendente"
            )
        # Faixa com as cores fornecidas; composição de layout, não elemento de marca.
        st.html('<div class="vrac-stripe"><span></span><span></span><span></span></div>')


def _footer() -> None:
    st.html(
        '<div class="vrac-footer">Pontifícia Universidade Católica do Rio de Janeiro · '
        "Prova de conceito interna da VRAC</div>"
    )


def _clear_all_results() -> None:
    from vrac.academic_ui import _clear

    for key in ("demo_data", "demo_filters"):
        st.session_state.pop(key, None)
    _clear_overview()
    _clear(source=True)


def main() -> None:
    branding = load_branding()
    st.set_page_config(page_title="VRAC | Demonstração", layout="wide")
    st.html(branding.styles)
    _header(branding)
    _content(branding)
    _footer()


def _content(branding: Branding) -> None:
    try:
        settings = load_settings()
    except ConfigurationError as error:
        _clear_all_results()
        st.error(str(error))
        st.stop()

    origin_key = (settings.data_mode, settings.demo_source)
    if st.session_state.get("ui_origin_key") != origin_key:
        _clear_all_results()
        st.session_state["ui_origin_key"] = origin_key
    access = authorize_data_access(settings)
    if not access.allowed:
        _clear_all_results()
        st.error(access.reason)
        st.stop()

    st.warning("DEMONSTRAÇÃO — somente dados sintéticos, sem validade institucional.")
    try:
        options = load_demo_options(settings)
    except DemoDataError as error:
        _clear_all_results()
        st.error(str(error))
        st.stop()
    st.caption(f"Origem dos dados: {options.source} · somente demonstração local")

    overview_tab, analyses_tab, records_tab = st.tabs(
        ["Análise docente", "Análises por período", "Registros de demonstração"]
    )
    with overview_tab:
        _faculty_overview(settings, branding, options)
    with analyses_tab:
        workbench(settings, branding, options)
    with records_tab:
        _records(settings, options)


def _records(settings: Settings, options) -> None:
    with st.container(key="vrac-filters"):
        st.subheader("Registros de demonstração")
        st.info(
            "Consulte os registros sintéticos pelos filtros abaixo. "
            "A tela apresenta os dados disponíveis sem consolidar indicadores."
        )
        department_column, period_column, action_column = st.columns(
            [2, 2, 1.4], vertical_alignment="bottom"
        )
        with department_column:
            department = st.selectbox(
                "Departamento fictício", options.departments, key="demo_department"
            )
        with period_column:
            period = st.selectbox(
                "Período fictício",
                options.periods,
                index=options.periods.index(options.default_period),
                key="demo_period",
            )
        filters = (settings.demo_source, department, period)
        if st.session_state.get("demo_filters") != filters:
            st.session_state.pop("demo_data", None)
            st.session_state.pop("demo_filters", None)
        with action_column:
            show = st.button(
                "Mostrar dados de demonstração", type="primary", width="stretch", key="demo_show"
            )

    if show:
        try:
            data = load_selected_demo(settings, department=department, period=period)
        except DemoDataError as error:
            st.session_state.pop("demo_data", None)
            st.session_state.pop("demo_filters", None)
            st.error(str(error))
            return
        st.session_state["demo_data"] = data
        st.session_state["demo_filters"] = filters

    data = st.session_state.get("demo_data")
    if data is None:
        st.caption("Escolha os filtros acima e mostre os dados fictícios.")
        return

    with st.container(key="vrac-results"):
        st.subheader("Filtros usados na demonstração")
        st.table(
            pd.DataFrame(
                [
                    {
                        "Departamento": department,
                        "Período": period,
                        "Modo": "Sintético",
                        "Origem": data.source,
                    }
                ]
            )
        )
        st.caption(
            f"Dados fictícios · versão {data.version} · atualização institucional: não se aplica"
        )
        if data.loaded_at is not None:
            st.caption(f"Consulta à base sintética: {data.loaded_at:%d/%m/%Y %H:%M:%S} UTC")
        if not data.faculty and not data.allocations:
            st.info(
                "Sem dados sintéticos para este recorte. Ausência de registros não significa zero."
            )
            return

        faculty_tab, allocation_tab = st.tabs(
            [
                f"Registros docentes fictícios · {len(data.faculty)} linhas",
                f"Alocações por turma · {len(data.allocations)} linhas",
            ]
        )
        with faculty_tab:
            faculty_columns = FACULTY_COLUMNS
            if data.source == "PostgreSQL sintético":
                faculty_columns = FACULTY_COLUMNS | {"real_hours": "Horas Reais fictícias"}
            _show_records([asdict(row) for row in data.faculty], faculty_columns)
        with allocation_tab:
            allocation_columns = ALLOCATION_COLUMNS
            if data.source == "PostgreSQL sintético":
                allocation_columns = ALLOCATION_COLUMNS | {
                    "allocated_hours": "Horas alocadas fictícias",
                    "students": "Vagas preenchidas fictícias",
                }
            _show_records([asdict(row) for row in data.allocations], allocation_columns)
        st.caption(
            "Os exemplos incluem vínculos e meses repetidos, compartilhamento e atuação em outro "
            f"departamento. “{MISSING_LABEL}” indica informação não registrada, diferente de zero. "
            "Linhas são registros, não docentes únicos. Não há consolidação docente ou cálculo "
            "oficial de carga horária nesta demonstração."
        )
        if data.source == "PostgreSQL sintético":
            st.caption(
                "Currículo e identificador do grupo de compartilhamento não foram informados "
                "na fonte consultada. Horas Reais são semestrais por vínculo e reaparecem nas "
                "linhas mensais; essas linhas não devem ser somadas. A unidade das horas "
                "não é inferida nesta visualização."
            )


OVERVIEW_STATE = (
    "overview_result",
    "overview_key",
    "overview_generated",
    "overview_history",
    "overview_history_error",
)


def _clear_overview() -> None:
    for name in OVERVIEW_STATE:
        st.session_state.pop(name, None)


def _selection(label: str, values: tuple[str, ...], key: str) -> frozenset[str] | None:
    if key in st.session_state:
        st.session_state[key] = [v for v in st.session_state[key] if v in values]
    chosen = st.multiselect(label, values, key=key, placeholder="Todos")
    return frozenset(chosen) if chosen else None


def _faculty_overview(settings: Settings, branding: Branding, demo_options: DemoOptions) -> None:
    with st.container(key="vrac-overview-filters"):
        st.subheader("Análise docente")
        st.info(
            "Reproduz a página Análise Geral do painel de professores sobre o cadastro "
            f"atual. A unidade de contagem é {UNIT_LABEL}, como no painel. A análise "
            "descreve a composição; não avalia suficiência de pessoal nem produtividade."
        )
        try:
            hierarchy = load_department_hierarchy(settings)
        except DemoDataError as error:
            _clear_overview()
            st.error(str(error))
            return
        scope = organisation_filters(hierarchy, prefix="overview")
        try:
            source = load_faculty_source(settings, **scope.source_arguments)
        except DemoDataError as error:
            _clear_overview()
            st.error(str(error))
            return
        options = filter_options(source)
        columns = st.columns(4)
        with columns[0]:
            cadres = _selection("Quadro", options.cadres, "overview_cadres")
        with columns[1]:
            categories = _selection(
                "Categoria funcional", options.categories, "overview_categories"
            )
        with columns[2]:
            statuses = _selection("Situação", options.statuses, "overview_statuses")
        with columns[3]:
            dual_roles = _selection("Dupla função", options.dual_roles, "overview_dual_roles")
        filters = OverviewFilters(cadres, categories, statuses, dual_roles)
        start, end = st.columns(2)
        periods = faculty_history_periods(settings, demo_options)
        with start:
            first_period = st.selectbox(
                "Semestre inicial do histórico", periods, key="overview_first"
            )
        with end:
            last_period = st.selectbox(
                "Semestre final do histórico", periods, index=len(periods) - 1, key="overview_last"
            )
        st.caption(
            "Composição: cadastro atual. Histórico: pessoas ativas em cada competência, "
            "com quadro e categoria próprios do mês. Situação e dupla função acima "
            "recortam somente o cadastro atual. O semestre docente segue janeiro–julho "
            "e agosto–dezembro, conforme a regra documentada."
        )
        digest = hashlib.sha256(json.dumps(asdict(source), sort_keys=True).encode()).hexdigest()
        key = (settings.demo_source, scope, filters, digest, first_period, last_period)
        if st.session_state.get("overview_key") != key:
            _clear_overview()
        run = st.button("Calcular resultados", type="primary", key="overview_run")

    if run:
        _clear_overview()
        try:
            with st.spinner("Calculando a composição docente..."):
                st.session_state["overview_result"] = compute_overview(source, filters)
                st.session_state["overview_key"] = key
                st.session_state["overview_generated"] = datetime.now(UTC)
        except ValueError as error:
            _clear_overview()
            st.error(str(error))
            return
        try:
            history_source = load_academic_source(settings, **scope.source_arguments)
            # Filtros com referência ao cadastro não são aplicados a uma fonte histórica.
            history_filters = AnalysisFilters(
                first_period,
                last_period,
                last_period,
                cadres=tuple(sorted(cadres or ())),
                categories=tuple(sorted(categories or ())),
            )
            st.session_state["overview_history"] = calculate(
                AnalysisKind.HISTORY, history_source, history_filters
            )
        except (DemoDataError, ValueError) as error:
            st.session_state["overview_history_error"] = str(error)
    overview: FacultyOverview | None = st.session_state.get("overview_result")
    if overview is None:
        st.caption("Escolha o departamento e os filtros e calcule os resultados.")
        return
    st.caption(f"Centro: {scope.center} · Departamentos efetivos: {', '.join(scope.departments)}")
    generated_at = st.session_state["overview_generated"]
    _overview_results(overview, branding, generated_at, center=scope.center)
    if overview_history := st.session_state.get("overview_history"):
        _render_result(
            replace(
                overview_history,
                metrics=(),
                charts=tuple(
                    chart for chart in overview_history.charts if chart.table == "monthly_history"
                ),
            ),
            branding,
            generated_at,
            prefix="overview",
        )
    if history_error := st.session_state.get("overview_history_error"):
        st.warning(f"Histórico indisponível: {history_error}")


def _overview_results(
    overview: FacultyOverview, branding: Branding, generated_at: datetime, *, center: str
) -> None:
    with st.container(key="vrac-overview-results"):
        st.subheader("Resultados calculados")
        st.table(
            pd.DataFrame(
                [
                    {
                        "Centro": center,
                        "Departamento": overview.department,
                        "Referência": "Cadastro atual",
                        "Unidade": UNIT_LABEL,
                        **dict(describe_filters(overview.filters)),
                        "Origem": overview.source,
                    }
                ]
            )
        )
        st.caption(
            f"Dados fictícios · versão {overview.version} · snapshot {overview.fingerprint[:12]} · "
            f"extração/cálculo {generated_at:%d/%m/%Y %H:%M:%S} UTC · "
            "atualização institucional: não disponível"
        )
        if overview.status not in {OverviewStatus.VALID, OverviewStatus.PARTIAL}:
            st.info(overview.narrative)
            return
        if overview.status == OverviewStatus.PARTIAL:
            st.warning("Parcial — composição calculada; fonte de Horas Reais indisponível.")

        render_faculty_metric(overview)
        st.markdown(overview.narrative)
        with st.expander(f"Avisos e limitações · {len(overview.warnings)}", expanded=False):
            for text in overview.warnings:
                st.warning(text)

        render_composition(overview, branding, prefix="overview")
        render_faculty_details(overview)

        stem = f"vrac-r01-{overview.department}-{generated_at:%Y%m%d-%H%M%S}"
        download_columns = st.columns(2)
        with download_columns[0]:
            st.download_button(
                "Baixar resumo (CSV)",
                summary_csv(overview, generated_at),
                file_name=f"{stem}-resumo.csv",
                mime="text/csv",
                key="overview_download_summary",
            )
        with download_columns[1]:
            st.download_button(
                "Baixar lista de conferência (CSV)",
                detail_csv(overview, generated_at),
                file_name=f"{stem}-lista.csv",
                mime="text/csv",
                key="overview_download_detail",
            )
