"""Demonstração com origem sintética explícita e consultas locais de leitura."""

import hashlib
import json
import math
from dataclasses import asdict, replace
from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd
import streamlit as st

from vrac.academic_ui import ALL_ANALYSES, _render_result, analysis_names, workbench
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
from vrac.feedback import OVERVIEW_STATUS
from vrac.feedback_ui import render_feedback
from vrac.organisation_ui import organisation_filters
from vrac.settings import ConfigurationError, DemoSource, Settings, load_settings
from vrac.ui_kit import data_table, download_button, scroll_to, step
from vrac.web_charts import warm_up

MISSING_LABEL = "ausente"

VIEW_KEY = "vrac-view"
VIEW_HOME = "Início"
VIEW_FACULTY = "Análise docente"
VIEW_ANALYSES = "Análises por período"
VIEWS = (VIEW_HOME, VIEW_FACULTY, VIEW_ANALYSES)
RECORDS_TITLE = "Conferir dados sintéticos"

# Tema, nome curto, pergunta, descrição, cor da capa e destino (None = tela docente).
HOME_CARDS = (
    (
        "Docentes",
        "Panorama docente",
        "Como se distribuem os docentes e como evolui o total de ativos?",
        "Composição do cadastro atual e histórico mensal no mesmo recorte.",
        "amarelo",
        None,
    ),
    (
        "Docentes",
        "Grupo QP e geral",
        "Como o grupo QP se compara ao corpo docente geral?",
        "Comparação por departamento com um grupo simulado e configurável.",
        "amarelo",
        "R02",
    ),
    (
        "Docentes",
        "Evolução docente",
        "Como o corpo docente evoluiu no período?",
        "Pessoas distintas por semestre e ativos a cada mês.",
        "amarelo",
        "R03",
    ),
    (
        "Docentes",
        "Funções",
        "Quais funções possuem evidência no período?",
        "Vigências por grupo de função no intervalo escolhido.",
        "amarelo",
        "R05",
    ),
    (
        "Carga horária",
        "Carga e alocações",
        "Como se distribuem a carga horária e as alocações?",
        "Horas Reais e horas alocadas, cada uma com sua unidade e fonte.",
        "azul",
        "R04",
    ),
    (
        "Matrículas",
        "Matrículas e alunos",
        "Como evoluíram as matrículas e os alunos?",
        "Séries por curso, habilitação, turno, nível e forma de ingresso.",
        "preto",
        "R06",
    ),
)

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
    data_table(display, numeric=numeric)


def _header(branding: Branding) -> None:
    marks = branding.tokens["marks"]
    with st.container(key="vrac-header"):
        st.html(
            f'<div class="vrac-marca"><img src="{branding.logo_url}" alt="{marks["logo_alt"]}" '
            f'width="{marks["display_width"]}"><span class="sep" aria-hidden="true"></span>'
            '<span class="nome">Análises acadêmicas'
            "<small>Vice-Reitoria para Assuntos Acadêmicos</small></span></div>"
        )


def _footer() -> None:
    st.html(
        '<footer class="vrac-footer"><div><b>Pontifícia Universidade Católica do Rio de '
        "Janeiro</b><span>Prova de conceito interna da VRAC</span></div>"
        "<div><b>Identidade visual</b><span>Aplicada às referências fornecidas · "
        "revisão institucional pendente</span></div></footer>"
    )


def _clear_all_results() -> None:
    from vrac.academic_ui import _clear

    for key in ("demo_data", "demo_filters"):
        st.session_state.pop(key, None)
    _clear_overview()
    _clear(source=True)


def main() -> None:
    warm_up()
    branding = load_branding()
    st.set_page_config(page_title="VRAC | Demonstração", layout="wide")
    st.html(branding.styles)
    notice = st.container(key="vrac-aviso")
    _header(branding)
    _content(branding, notice)
    _footer()


def _open_view(view: str, analysis: str | None = None) -> None:
    """Executado antes dos widgets: abre a tela e já prepara a análise escolhida."""
    st.session_state[VIEW_KEY] = view
    if analysis is not None:
        st.session_state["suite_analysis"] = analysis
        st.session_state["suite_autoload"] = True


def _home(settings: Settings, options: DemoOptions) -> None:
    """Porta de entrada: cada cartão é uma pergunta e leva direto à análise que a responde."""
    names = {code: name for name, code in analysis_names().items()}
    semesters = faculty_history_periods(settings, options)
    with st.container(key="vrac-home-hero"):
        text, numbers = st.columns([1.5, 1], gap="large")
        with text:
            st.html(
                '<div class="vrac-hero"><p class="vrac-kicker">Análises disponíveis</p>'
                "<h1>Comece pela pergunta que você quer responder</h1>"
                '<p class="lead">Docentes, matrículas e carga horária em gráficos, tabelas '
                "e arquivos prontos para baixar. Escolha uma análise, defina o recorte e "
                "calcule.</p></div>"
            )
            with st.container(horizontal=True):
                st.button(
                    "Abrir análise docente",
                    type="primary",
                    key="home_faculty",
                    on_click=_open_view,
                    args=(VIEW_FACULTY,),
                )
                st.button(
                    "Ver todas as análises",
                    key="home_all",
                    on_click=_open_view,
                    args=(VIEW_ANALYSES, ALL_ANALYSES),
                )
        with numbers:
            st.html(
                '<div class="vrac-bloco-num"><span class="rot">Nesta demonstração</span><dl>'
                f"<dt>{len(names)}</dt><dd>análises disponíveis</dd>"
                f"<dt>{len(options.departments)}</dt><dd>departamentos fictícios</dd>"
                f"<dt>{len(semesters)}</dt><dd>semestres fictícios</dd></dl></div>"
            )
    st.html(
        '<div class="vrac-section-title"><h2>O que você quer saber?</h2>'
        "<p>Cada cartão abre a análise com os filtros certos.</p></div>"
    )
    with st.container(key="vrac-home-cards"):
        for start in range(0, len(HOME_CARDS), 3):
            for column, card in zip(
                st.columns(3, gap="medium"), HOME_CARDS[start : start + 3], strict=True
            ):
                theme, name, question, description, color, code = card
                with column, st.container(key=f"vrac-card-{code or 'docente'}"):
                    st.html(
                        f'<div class="vrac-capa {color}"><span class="selo">{theme}</span>'
                        f'<span class="capa-nome">{name}'
                        '<span class="seta" aria-hidden="true">↗</span></span></div>'
                        f'<div class="vrac-card-body"><h3>{question}</h3>'
                        f"<p>{description}</p></div>"
                    )
                    st.button(
                        "Abrir análise",
                        key=f"home_open_{code or 'docente'}",
                        width="stretch",
                        on_click=_open_view,
                        args=(VIEW_ANALYSES, names[code]) if code else (VIEW_FACULTY,),
                    )
    st.html(
        '<div class="vrac-section-title"><h2>Como funciona</h2></div>'
        '<ol class="vrac-passos">'
        '<li><span class="vrac-n">1</span><span><b>Escolha a análise</b>'
        "Comece por um dos cartões acima.</span></li>"
        '<li><span class="vrac-n">2</span><span><b>Defina os filtros e calcule</b>'
        "Só aparecem os filtros que afetam a análise.</span></li>"
        '<li><span class="vrac-n">3</span><span><b>Explore e exporte os resultados</b>'
        "Passe o cursor nos gráficos e baixe tabelas e imagens.</span></li></ol>"
    )


def _content(branding: Branding, notice) -> None:
    try:
        settings = load_settings()
    except ConfigurationError as error:
        _clear_all_results()
        st.error(str(error))
        st.stop()

    if settings.demo_source == DemoSource.SUPABASE:
        from vrac.auth_ui import require_login
        from vrac.supabase_auth import session_scope

        try:
            session = require_login()
        except ConfigurationError as error:
            _clear_all_results()
            st.error(str(error))
            st.stop()
        with session_scope(session):
            _authorized_content(settings, branding, notice)
        return
    _authorized_content(settings, branding, notice)


def _authorized_content(settings: Settings, branding: Branding, notice) -> None:
    origin_key = (settings.data_mode, settings.demo_source)
    if st.session_state.get("ui_origin_key") != origin_key:
        _clear_all_results()
        st.session_state["ui_origin_key"] = origin_key
    access = authorize_data_access(settings)
    if not access.allowed:
        _clear_all_results()
        st.error(access.reason)
        st.stop()

    try:
        options = load_demo_options(settings)
    except DemoDataError as error:
        _clear_all_results()
        notice.warning("**DEMONSTRAÇÃO** · somente dados sintéticos, sem validade institucional.")
        st.error(str(error))
        st.stop()
    notice.warning(
        "**DEMONSTRAÇÃO** · somente dados sintéticos, sem validade institucional · "
        f"Origem dos dados: {options.source}"
    )

    # Todas as abas são executadas para preservar os filtros ao navegar entre elas.
    home_tab, overview_tab, analyses_tab = st.tabs(VIEWS, key=VIEW_KEY, on_change="rerun")
    with home_tab:
        _home(settings, options)
    with overview_tab:
        _faculty_overview(settings, branding, options)
    with analyses_tab:
        workbench(settings, branding, options)
    # Apoio à conferência, fora do menu: fica recolhido no fim de todas as telas.
    with st.container(key="vrac-conferencia"), st.expander(RECORDS_TITLE):
        _records(settings, options)


def _records(settings: Settings, options) -> None:
    with st.container(key="vrac-panel-records"):
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

    with st.container(key="vrac-panel-records-results"):
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
    "overview_execution_id",
)


def _clear_overview() -> None:
    for name in OVERVIEW_STATE:
        st.session_state.pop(name, None)


def _reset_overview_filters() -> None:
    """Executado antes dos widgets; limpa filtros e arquivos da consulta anterior."""
    for name in (
        "overview_center",
        "overview_department",
        "overview_cadres",
        "overview_categories",
        "overview_statuses",
        "overview_dual_roles",
        "overview_first",
        "overview_last",
    ):
        st.session_state.pop(name, None)
    _clear_overview()


def _selection(label: str, values: tuple[str, ...], key: str) -> frozenset[str] | None:
    if key in st.session_state:
        st.session_state[key] = [v for v in st.session_state[key] if v in values]
    chosen = st.multiselect(label, values, key=key, placeholder="Todos")
    return frozenset(chosen) if chosen else None


def _faculty_overview(settings: Settings, branding: Branding, demo_options: DemoOptions) -> None:
    with st.container(key="vrac-panel-overview-filters"):
        st.subheader("Análise docente")
        st.write("Como se distribuem os docentes e como evolui o total de ativos?")
        step(1, "Defina o recorte")
        try:
            hierarchy = load_department_hierarchy(settings)
        except DemoDataError as error:
            _clear_overview()
            st.error(str(error))
            return
        organisation, interval = st.columns(2, gap="medium")
        with organisation:
            scope = organisation_filters(hierarchy, prefix="overview")
        try:
            source = load_faculty_source(settings, **scope.source_arguments)
        except DemoDataError as error:
            _clear_overview()
            st.error(str(error))
            return
        options = filter_options(source)
        periods = faculty_history_periods(settings, demo_options)
        with interval:
            start, end = st.columns(2)
            with start:
                first_period = st.selectbox(
                    "Semestre inicial do histórico",
                    periods,
                    key="overview_first",
                    help="O semestre docente segue janeiro–julho e agosto–dezembro, "
                    "conforme a regra documentada.",
                )
            with end:
                last_period = st.selectbox(
                    "Semestre final do histórico",
                    periods,
                    index=len(periods) - 1,
                    key="overview_last",
                )
        step(2, "Refine, se precisar, e calcule")
        with st.expander("Mais filtros · opcional", expanded=False):
            st.caption(
                "Seleção vazia inclui todas as opções disponíveis. Situação e dupla função "
                "recortam somente o cadastro atual."
            )
            columns = st.columns(2)
            with columns[0]:
                cadres = _selection("Quadro", options.cadres, "overview_cadres")
                statuses = _selection("Situação", options.statuses, "overview_statuses")
            with columns[1]:
                categories = _selection(
                    "Categoria funcional", options.categories, "overview_categories"
                )
                dual_roles = _selection("Dupla função", options.dual_roles, "overview_dual_roles")
        filters = OverviewFilters(cadres, categories, statuses, dual_roles)
        active_filters = [
            f"{label}: {', '.join(sorted(values))}"
            for label, values in (
                ("Quadro", cadres),
                ("Categoria", categories),
                ("Situação", statuses),
                ("Dupla função", dual_roles),
            )
            if values
        ]
        if active_filters:
            st.caption("Filtros adicionais ativos · " + " · ".join(active_filters))
        st.caption(
            f"Composição: cadastro atual, em {UNIT_LABEL}. Histórico: pessoas ativas em cada "
            "mês, com quadro e categoria próprios do mês. Os dados são fictícios."
        )
        digest = hashlib.sha256(json.dumps(asdict(source), sort_keys=True).encode()).hexdigest()
        key = (settings.demo_source, scope, filters, digest, first_period, last_period)
        changed = "overview_key" in st.session_state and st.session_state["overview_key"] != key
        if st.session_state.get("overview_key") != key:
            _clear_overview()
        if changed:
            st.info(
                "Os filtros mudaram. Calcule novamente para atualizar os resultados e arquivos."
            )
        with st.container(horizontal=True, vertical_alignment="center"):
            run = st.button("Calcular resultados", type="primary", key="overview_run")
            st.button(
                "Limpar filtros",
                key="overview_reset",
                type="tertiary",
                on_click=_reset_overview_filters,
            )

    if run:
        _clear_overview()
        try:
            with st.spinner("Calculando a composição docente..."):
                st.session_state["overview_result"] = compute_overview(source, filters)
                st.session_state["overview_key"] = key
                st.session_state["overview_generated"] = datetime.now(UTC)
                st.session_state["overview_execution_id"] = str(uuid4())
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
        with st.container(key="vrac-empty-overview"):
            st.info(
                "Sua análise aparecerá aqui. Escolha o centro, o departamento e o intervalo "
                "do histórico; depois clique em Calcular resultados."
            )
        return
    generated_at = st.session_state["overview_generated"]
    export_context = {
        "Execução": st.session_state["overview_execution_id"],
        "Centro": scope.center,
        "Departamento": scope.department,
        "Departamentos efetivos": ", ".join(scope.departments),
        **dict(describe_filters(filters)),
        "Semestre inicial do histórico": first_period,
        "Semestre final do histórico": last_period,
        "Cálculo (UTC)": generated_at.isoformat(),
        "Extração": "horário não registrado nesta tela",
        "Atualização da fonte": "não disponível",
        "Versão dos dados": overview.version,
        "Snapshot": overview.fingerprint,
    }
    _overview_results(
        overview,
        branding,
        generated_at,
        center=scope.center,
        departments=scope.departments,
        export_context=export_context,
    )
    if overview_history := st.session_state.get("overview_history"):
        with st.container(key="vrac-panel-overview-history"):
            _render_result(
                replace(
                    overview_history,
                    metrics=(),
                    charts=tuple(
                        chart
                        for chart in overview_history.charts
                        if chart.table == "monthly_history"
                    ),
                ),
                branding,
                generated_at,
                prefix="overview",
                export_context=export_context,
            )
    if history_error := st.session_state.get("overview_history_error"):
        st.warning(f"Histórico indisponível: {history_error}")
    if run:
        scroll_to("vrac-panel-overview-results")
    render_feedback(
        st.session_state["overview_execution_id"],
        "Análise docente",
        OVERVIEW_STATUS[overview.status],
        generated_at,
        prefix="overview",
    )


def _overview_results(
    overview: FacultyOverview,
    branding: Branding,
    generated_at: datetime,
    *,
    center: str,
    departments: tuple[str, ...],
    export_context: dict[str, str],
) -> None:
    with st.container(key="vrac-panel-overview-results"):
        st.subheader("Resultados calculados")
        st.caption(f"Centro: {center} · Departamentos efetivos: {', '.join(departments)}")
        if overview.status not in {OverviewStatus.VALID, OverviewStatus.PARTIAL}:
            _overview_provenance(overview, generated_at, center)
            st.info(overview.narrative)
            return
        if overview.status == OverviewStatus.PARTIAL:
            st.warning("Parcial — composição calculada; fonte de Horas Reais indisponível.")

        figure, reading = st.columns([1, 2.4], gap="medium", vertical_alignment="center")
        with figure:
            render_faculty_metric(overview, prefix="overview")
        with reading, st.container(key="vrac-narrative-overview"):
            st.markdown(overview.narrative)

        stem = f"vrac-r01-{overview.department}-{generated_at:%Y%m%d-%H%M%S}"
        with st.container(horizontal=True):
            download_button(
                "Baixar resumo (CSV)",
                summary_csv(overview, generated_at, export_context),
                file_name=f"{stem}-resumo.csv",
                mime="text/csv",
                key="overview_download_summary",
            )
            download_button(
                "Baixar lista de conferência (CSV)",
                detail_csv(overview, generated_at, export_context),
                file_name=f"{stem}-lista.csv",
                mime="text/csv",
                key="overview_download_detail",
            )

        render_composition(overview, branding, prefix="overview", export_context=export_context)
        render_faculty_details(overview)
        with st.expander(f"Avisos e limitações · {len(overview.warnings)}", expanded=False):
            for text in overview.warnings:
                st.warning(text)
        _overview_provenance(overview, generated_at, center)


def _overview_provenance(overview: FacultyOverview, generated_at: datetime, center: str) -> None:
    with st.expander("Filtros usados e origem deste resultado", expanded=False):
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
            f"cálculo {generated_at:%d/%m/%Y %H:%M:%S} UTC · extração: horário não registrado · "
            "atualização institucional: não disponível"
        )
