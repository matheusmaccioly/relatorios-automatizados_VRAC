"""Demonstração com origem sintética explícita e consultas locais de leitura."""

import hashlib
import json
import math
from dataclasses import asdict
from datetime import UTC, datetime

import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt

from vrac.academic_ui import workbench
from vrac.analyses.export import DETAIL_COLUMNS, detail_csv, summary_csv
from vrac.analyses.faculty_overview import (
    QP_BLOCK_REASON,
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
from vrac.charts import horizontal_bars
from vrac.demo_data import (
    DemoDataError,
    load_demo_options,
    load_faculty_departments,
    load_faculty_source,
    load_selected_demo,
)
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
        st.error(str(error))
        st.stop()

    access = authorize_data_access(settings)
    if not access.allowed:
        st.error(access.reason)
        st.stop()

    st.warning("DEMONSTRAÇÃO — somente dados sintéticos, sem validade institucional.")
    try:
        options = load_demo_options(settings)
    except DemoDataError as error:
        st.session_state.pop("demo_data", None)
        st.session_state.pop("demo_filters", None)
        st.error(str(error))
        st.stop()
    st.caption(f"Origem dos dados: {options.source} · somente demonstração local")

    overview_tab, analyses_tab, records_tab = st.tabs(
        ["Situação geral do departamento", "Análises por período", "Registros de demonstração"]
    )
    with overview_tab:
        _faculty_overview(settings, branding)
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


OVERVIEW_STATE = ("overview_result", "overview_key")


def _clear_overview() -> None:
    for name in OVERVIEW_STATE:
        st.session_state.pop(name, None)


def _selection(label: str, values: tuple[str, ...], key: str) -> frozenset[str] | None:
    chosen = st.multiselect(label, values, key=key, placeholder="Todos")
    return frozenset(chosen) if chosen else None


def _faculty_overview(settings: Settings, branding: Branding) -> None:
    with st.container(key="vrac-overview-filters"):
        st.subheader("Situação geral do departamento")
        st.info(
            "Reproduz a página Análise Geral do painel de professores sobre o cadastro "
            f"atual. A unidade de contagem é {UNIT_LABEL}, como no painel. A análise "
            "descreve a composição; não avalia suficiência de pessoal nem produtividade."
        )
        try:
            departments = load_faculty_departments(settings)
        except DemoDataError as error:
            _clear_overview()
            st.error(str(error))
            return
        department = st.selectbox("Departamento", departments, key="overview_department")
        try:
            source = load_faculty_source(settings, department=department)
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
        digest = hashlib.sha256(json.dumps(asdict(source), sort_keys=True).encode()).hexdigest()
        key = (settings.demo_source, department, filters, digest)
        if st.session_state.get("overview_key") != key:
            _clear_overview()
        run = st.button("Calcular resultados", type="primary", key="overview_run")

    if run:
        st.session_state["overview_result"] = compute_overview(source, filters)
        st.session_state["overview_key"] = key
    overview: FacultyOverview | None = st.session_state.get("overview_result")
    if overview is None:
        st.caption("Escolha o departamento e os filtros e calcule os resultados.")
        return
    _overview_results(overview, branding)


def _overview_results(overview: FacultyOverview, branding: Branding) -> None:
    with st.container(key="vrac-overview-results"):
        st.subheader("Resultados calculados")
        st.table(
            pd.DataFrame(
                [
                    {
                        "Departamento": overview.department,
                        "Referência": "Cadastro atual",
                        "Unidade": UNIT_LABEL,
                        **dict(describe_filters(overview.filters)),
                        "Origem": overview.source,
                    }
                ]
            )
        )
        st.caption(f"Dados fictícios · versão {overview.version}")
        if overview.status != OverviewStatus.VALID:
            st.info(overview.narrative)
            return

        st.metric(
            "Quantidade de docentes",
            overview.total,
            help=f"Contagem de {UNIT_LABEL} no cadastro atual, como o cartão do painel.",
        )
        st.markdown(overview.narrative)
        with st.expander(f"Avisos e limitações · {len(overview.warnings)}", expanded=True):
            for text in overview.warnings:
                st.warning(text)

        chart_columns = st.columns(2, gap="large")
        breakdowns = (
            ("Por quadro", "Quadro", overview.by_cadre),
            ("Por categoria funcional", "Categoria funcional", overview.by_category),
        )
        for column, (title, label, items) in zip(chart_columns, breakdowns, strict=True):
            with column:
                figure = horizontal_bars(
                    items, title=title, unit=UNIT_LABEL.capitalize(), branding=branding
                )
                st.pyplot(figure, width="stretch")
                plt.close(figure)
                st.table(pd.DataFrame(items, columns=[label, "Matrículas"]))
        st.caption(
            "Por quadro conta matrículas distintas; por categoria conta linhas do cadastro "
            "com matrícula, como os visuais do painel. Barras não são somadas entre si."
        )

        st.subheader("Geral e QP")
        st.table(
            pd.DataFrame(
                [
                    {"Resultado": "Geral", "Valor": str(overview.total), "Situação": "Calculado"},
                    {"Resultado": "QP", "Valor": "—", "Situação": "Bloqueado"},
                    {"Resultado": "Demais", "Valor": "—", "Situação": "Bloqueado"},
                    {"Resultado": "Participação do QP", "Valor": "—", "Situação": "Bloqueado"},
                ]
            )
        )
        st.info(QP_BLOCK_REASON)

        with st.expander("Lista de conferência (dados fictícios)"):
            _show_records([asdict(row) for row in overview.detail], dict(DETAIL_COLUMNS))
            st.caption(
                "Horas Reais: soma do semestre mais recente de cada matrícula na fonte "
                "própria, sem substituir por carga contratada ou horas de disciplinas."
            )

        generated_at = datetime.now(UTC)
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
