"""Demonstração com origem sintética explícita e consultas locais de leitura."""

import hashlib
import json
import math
from dataclasses import asdict, replace
from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd
import streamlit as st

from vrac.academic_ui import (
    _clear,
    _render_result,
    complete_report_pdf,
    export_box,
    workbench,
)
from vrac.analyses.academic import (
    DEFAULT_STATUS,
    OVERVIEW_FOLDER,
    AnalysisFilters,
    AnalysisKind,
    calculate,
)
from vrac.analyses.academic_data import ALL_DEPARTMENTS
from vrac.analyses.academic_export import report_zip
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
from vrac.department_hierarchy import ALL_CENTERS
from vrac.faculty_presentation import (
    render_composition,
    render_faculty_details,
    render_faculty_metric,
)
from vrac.feedback import OVERVIEW_STATUS
from vrac.feedback_ui import render_feedback
from vrac.navigation import (
    ALL_FACULTY,
    AREAS,
    COMPLETE_CODES,
    FACULTY,
    FACULTY_PICKER,
    PANORAMA,
    STUDENTS,
    VIEW_KEY,
    Area,
    area_of,
    codes_for,
)
from vrac.organisation_ui import OrganisationScope, organisation_filters
from vrac.provenance import INSTITUTIONAL_SOURCE, nature
from vrac.settings import ConfigurationError, DataMode, DemoSource, Settings, load_settings
from vrac.ui_kit import (
    data_table,
    download_button,
    info_button,
    scroll_to,
    step,
    used_filters,
)
from vrac.web_charts import warm_up

MISSING_LABEL = "ausente"

VIEW_HOME = "Início"
VIEWS = (VIEW_HOME, *(area.tab for area in AREAS))
RECORDS_TITLE = "Conferir dados sintéticos"
# Prefixo das chaves de cada tela; o panorama tem formulário próprio.
PREFIXES = {PANORAMA: "overview", **dict.fromkeys((*COMPLETE_CODES[:-1], ALL_FACULTY), "suite")}
STUDENTS_PREFIX = "alunos"

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
            '<div class="vrac-marca" data-vrac-release="0.1.7">'
            f'<img src="{branding.logo_url}" alt="{marks["logo_alt"]}" '
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
    from vrac.student_general_ui import clear as clear_students

    clear_students()
    for key in ("demo_data", "demo_filters"):
        st.session_state.pop(key, None)
    _clear_overview()
    _clear(source=True)
    _clear(source=True, prefix=STUDENTS_PREFIX)


def main() -> None:
    warm_up()
    branding = load_branding()
    st.set_page_config(page_title="VRAC | Demonstração", layout="wide")
    st.html(branding.styles)
    notice = st.container(key="vrac-aviso")
    _header(branding)
    _content(branding, notice)
    _footer()


def _open_analysis(code: str, department: str | None = None, *, run: bool = False) -> None:
    """Executado antes dos widgets: abre a aba da área e já prepara a análise escolhida."""
    area = area_of(code)
    st.session_state[VIEW_KEY] = area.tab
    if area is FACULTY:
        st.session_state[FACULTY_PICKER] = code
    prefix = PREFIXES.get(code, STUDENTS_PREFIX)
    if department is not None:
        st.session_state[f"{prefix}_center"] = ALL_CENTERS
        st.session_state[f"{prefix}_department"] = department
    if run:
        st.session_state[f"{prefix}_autorun"] = True


def _quick_start() -> None:
    _open_analysis(st.session_state["home_analysis"], st.session_state["home_department"], run=True)


def _slug(text: str) -> str:
    """Nome de arquivo legível, sem acentos nem espaços."""
    from unicodedata import normalize

    plain = normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "-".join("".join(c if c.isalnum() else " " for c in plain).lower().split())


def _go_home() -> None:
    st.session_state[VIEW_KEY] = VIEW_HOME


def _analysis_label(code: str) -> str:
    area = area_of(code)
    return f"{area.title} · {area.analysis(code).name}"


def _home_scope(hierarchy, department: str) -> OrganisationScope:
    """Atalho do Início: departamento escolhido, sem recorte por centro."""
    if department == ALL_DEPARTMENTS:
        return OrganisationScope(ALL_CENTERS, department, hierarchy.departments_for(ALL_CENTERS))
    return OrganisationScope(ALL_CENTERS, department, (department,))


def _home(settings: Settings, branding: Branding) -> None:
    """Porta de entrada: atalho que já calcula e áreas que levam a cada análise."""
    with st.container(key="vrac-home-hero"):
        text, start = st.columns([1.3, 1], gap="large")
        with text:
            st.html(
                '<div class="vrac-hero"><p class="vrac-kicker">Análises disponíveis</p>'
                "<h1>O que você quer analisar?</h1>"
                '<p class="lead">Escolha uma área nas abas acima ou use o atalho Comece rápido: '
                "indique a análise e o departamento e veja os resultados calculados, com "
                "gráficos, tabelas e arquivos para baixar.</p></div>"
            )
        with start, st.container(key="vrac-home-start"):
            st.html('<p class="vrac-start-title">Comece rápido</p>')
            try:
                hierarchy = load_department_hierarchy(settings)
            except DemoDataError as error:
                st.error(str(error))
            else:
                st.selectbox(
                    "Análise",
                    [item.code for area in AREAS for item in area.analyses],
                    format_func=_analysis_label,
                    key="home_analysis",
                )
                department = st.selectbox(
                    "Departamento",
                    (*hierarchy.departments_for(ALL_CENTERS), ALL_DEPARTMENTS),
                    key="home_department",
                )
                st.button(
                    "Ver resultados",
                    type="primary",
                    width="stretch",
                    key="home_start",
                    on_click=_quick_start,
                )
                st.html('<p class="vrac-start-ou">ou</p>')
                scope = _home_scope(hierarchy, department)
                download_button(
                    "Gerar relatório completo (R01–R06)",
                    lambda: complete_report_pdf(settings, branding, scope),
                    file_name=f"vrac-relatorio-completo-{_slug(department)}-"
                    f"{datetime.now(UTC):%Y%m%d}.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key="home_complete",
                    icon=":material/picture_as_pdf:",
                    on_click="ignore",
                    help="Calcula as seis análises do departamento escolhido e baixa o PDF "
                    "na hora, com o intervalo completo e os filtros iniciais.",
                )
    st.html(
        '<div class="vrac-section-title"><h2>Explore por área</h2>'
        "<p>Cada área reúne as análises de um mesmo tema. Clique em uma para abri-la.</p></div>"
    )
    with st.container(key="vrac-home-areas"):
        for column, area in zip(st.columns(len(AREAS), gap="medium"), AREAS, strict=True):
            with column, st.container(key=f"vrac-area-{area.key}"):
                count = len(area.analyses)
                seal = f"{count} {'análise' if count == 1 else 'análises'}" if count else "Em breve"
                st.html(
                    f'<div class="vrac-capa {area.color}"><span class="selo">{seal}</span>'
                    f'<span class="capa-nome">{area.title}</span></div>'
                    f'<div class="vrac-card-body"><p>{area.summary}</p></div>'
                )
                for item in area.analyses:
                    st.button(
                        f"{item.name} →",
                        key=f"home_open_{item.code}",
                        type="tertiary",
                        help=item.question,
                        on_click=_open_analysis,
                        args=(item.code,),
                    )
                if not area.available:
                    st.button("Em breve", key=f"home_soon_{area.key}", disabled=True)
    st.html(
        '<div class="vrac-section-title"><h2>Como funciona</h2></div>'
        '<ol class="vrac-passos">'
        '<li><span class="vrac-n">1</span><span><b>Escolha a área e a análise</b>'
        "Pelas abas no topo ou pelos atalhos desta página.</span></li>"
        '<li><span class="vrac-n">2</span><span><b>Defina o recorte e calcule</b>'
        "Só aparecem os filtros que afetam a análise.</span></li>"
        '<li><span class="vrac-n">3</span><span><b>Explore e exporte os resultados</b>'
        "Passe o cursor nos gráficos e baixe tabelas e imagens.</span></li></ol>"
    )


def _area_intro(area: Area) -> None:
    st.html(
        f'<div class="vrac-area-intro"><p class="vrac-kicker">Análises disponíveis</p>'
        f'<h1>{area.title}</h1><p class="lead">{area.summary}</p></div>'
    )


def _question(question: str, description: str) -> None:
    st.markdown(f"**{question}**")
    st.caption(description)


def _faculty_area(
    settings: Settings, branding: Branding, options: DemoOptions, *, active: bool
) -> None:
    _area_intro(FACULTY)
    names = {item.code: item.name for item in FACULTY.analyses}
    if st.session_state.get(FACULTY_PICKER) not in names:
        st.session_state[FACULTY_PICKER] = PANORAMA
    code = (
        st.segmented_control(
            "Escolha a análise",
            tuple(names),
            format_func=names.__getitem__,
            key=FACULTY_PICKER,
            required=True,
        )
        or PANORAMA
    )
    analysis = FACULTY.analysis(code)
    _question(analysis.question, analysis.description)
    if code == PANORAMA:
        _faculty_overview(settings, branding, options)
        return
    workbench(
        settings,
        branding,
        options,
        codes=codes_for(code),
        label=analysis.name,
        active=active,
    )


def _students_area(
    settings: Settings, branding: Branding, options: DemoOptions, *, active: bool
) -> None:
    _area_intro(STUDENTS)
    if settings.data_mode == DataMode.PSEUDONYMIZED:
        from vrac.student_general_ui import DESCRIPTION, QUESTION, render

        _question(QUESTION, DESCRIPTION)
        render(branding, active=active)
        return
    (analysis,) = STUDENTS.analyses
    _question(analysis.question, analysis.description)
    workbench(
        settings,
        branding,
        options,
        codes=codes_for(analysis.code),
        label=analysis.name,
        prefix=STUDENTS_PREFIX,
        active=active,
    )


def _coming_soon(area: Area) -> None:
    with st.container(key=f"vrac-soon-{area.key}"):
        st.html(
            '<div class="vrac-area-intro"><span class="vrac-breve">Em breve</span>'
            f'<h1>{area.title}</h1><p class="lead">{area.summary}</p></div>'
        )
        st.button("Voltar ao início", key=f"{area.key}_home", on_click=_go_home)


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

        if settings.data_mode == DataMode.REAL:
            st.error(authorize_data_access(settings).reason)
            st.stop()
        # Na hospedagem, a origem é sempre a institucional pseudonimizada, sem seletor;
        # a demonstração sintética segue disponível só na execução local em memória.
        settings = replace(settings, data_mode=DataMode.PSEUDONYMIZED)
        try:
            session = require_login(settings.data_mode)
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
    if settings.data_mode == DataMode.PSEUDONYMIZED:
        from vrac.supabase_auth import current_session

        origin_key += (current_session().batch, current_session().departments)
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
        notice.warning(
            nature(INSTITUTIONAL_SOURCE if settings.data_mode == DataMode.PSEUDONYMIZED else "")
        )
        st.error(str(error))
        st.stop()
    notice.warning(nature(options.source))

    # Todas as abas são executadas para preservar os filtros ao navegar entre elas;
    # a base de cada área só é lida enquanto a sua aba está aberta.
    home_tab, faculty_tab, students_tab, *soon_tabs = st.tabs(
        VIEWS, key=VIEW_KEY, on_change="rerun"
    )
    with home_tab:
        _home(settings, branding)
    with faculty_tab:
        _faculty_area(settings, branding, options, active=bool(faculty_tab.open))
    with students_tab:
        _students_area(settings, branding, options, active=bool(students_tab.open))
    soon = [area for area in AREAS if not area.available]
    for tab, area in zip(soon_tabs, soon, strict=True):
        with tab:
            _coming_soon(area)
    # Apoio à conferência, fora do menu: fica recolhido no fim de todas as telas.
    if settings.data_mode != DataMode.PSEUDONYMIZED:
        with st.container(key="vrac-conferencia"), st.expander(RECORDS_TITLE):
            _records(settings, options)


def _records(settings: Settings, options) -> None:
    with st.container(key="vrac-panel-records"):
        st.subheader("Registros de demonstração")
        st.info(
            "Consulte os registros sintéticos pelos filtros abaixo. "
            "A tela apresenta os dados disponíveis sem consolidar resultados."
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
    chosen = st.multiselect(label, values, key=key, placeholder="Todos", persist_state="page")
    return frozenset(chosen) if chosen else None


def _faculty_overview(settings: Settings, branding: Branding, demo_options: DemoOptions) -> None:
    with st.container(key="vrac-panel-overview-filters"):
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
                    persist_state="page",
                    help="O semestre docente segue janeiro–julho e agosto–dezembro, "
                    "conforme a regra documentada.",
                )
            with end:
                last_period = st.selectbox(
                    "Semestre final do histórico",
                    periods,
                    index=len(periods) - 1,
                    key="overview_last",
                    persist_state="page",
                )
        step(2, "Refine, se precisar, e calcule")
        with st.expander("Mais filtros · opcional", expanded=False):
            st.caption(
                "Seleção vazia inclui todas as opções disponíveis. Situação começa em ATIVO, "
                "como no painel. Situação e dupla função recortam somente o cadastro atual."
            )
            if "overview_statuses" not in st.session_state:
                st.session_state["overview_statuses"] = [
                    x for x in options.statuses if x == DEFAULT_STATUS
                ]
            columns = st.columns(2)
            with columns[0]:
                cadres = _selection("Quadro", options.cadres, "overview_cadres")
                statuses = _selection("Situação", options.statuses, "overview_statuses")
            with columns[1]:
                categories = _selection(
                    "Categoria Funcional", options.categories, "overview_categories"
                )
                dual_roles = _selection(
                    "Dupla Função (Dupla Matrícula)", options.dual_roles, "overview_dual_roles"
                )
        filters = OverviewFilters(cadres, categories, statuses, dual_roles)
        active_filters = [
            f"{label}: {', '.join(sorted(values))}"
            for label, values in (
                ("Quadro", cadres),
                ("Categoria Funcional", categories),
                ("Situação", statuses),
                ("Dupla função", dual_roles),
            )
            if values
        ]
        if active_filters:
            st.caption("Filtros adicionais ativos · " + " · ".join(active_filters))
        overview_notes = (
            f"Composição: cadastro atual, em {UNIT_LABEL}.",
            "Histórico: pessoas ativas em cada mês, com quadro e categoria próprios do mês.",
            nature(source.source),
            *source.notes,
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
            info_button(overview_notes, key="overview-fonte", title="Sobre estes dados")
        run = st.session_state.pop("overview_autorun", False) or run

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
        "Origem": source.source,
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
    export_slot, r01_charts = _overview_results(
        overview,
        branding,
        generated_at,
        center=scope.center,
        departments=scope.departments,
        export_context=export_context,
    )
    history, history_images = None, {}
    if overview_history := st.session_state.get("overview_history"):
        # O PDF leva o histórico como aparece na tela: só a série mensal, sem métricas.
        history = replace(
            overview_history,
            metrics=(),
            charts=tuple(c for c in overview_history.charts if c.table == "monthly_history"),
        )
        with st.container(key="vrac-panel-overview-history"):
            history_images = _render_result(
                history, branding, generated_at, prefix="overview", export_context=export_context
            )
    if export_slot is not None:
        r01_files = {
            f"{OVERVIEW_FOLDER}/resumo.csv": summary_csv(overview, generated_at, export_context),
            f"{OVERVIEW_FOLDER}/lista-conferencia.csv": detail_csv(
                overview, generated_at, export_context
            ),
            **r01_charts,
        }
        r01_manifest = {
            "kind": "R01",
            "status": OVERVIEW_STATUS[overview.status],
            "source": overview.source,
            "version": overview.version,
            "fingerprint": overview.fingerprint,
        }

        def package(include: tuple[str, ...] | None = None) -> bytes:
            include = include or ("R01", "R03")
            with_history = history is not None and "R03" in include
            return report_zip(
                (history,) if with_history else (),
                generated_at,
                {n: build() for n, build in history_images.items()} if with_history else {},
                {n: d() if callable(d) else d for n, d in r01_files.items()}
                if "R01" in include
                else {},
                export_context,
                additional_analyses=(r01_manifest,) if "R01" in include else (),
            )

        export_box(
            export_slot,
            prefix="overview",
            available=("R01", "R03") if history is not None else ("R01",),
            package=package,
            branding=branding,
            generated_at=generated_at,
            complete=lambda: complete_report_pdf(settings, branding, scope),
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
) -> tuple[object | None, dict]:
    """Devolve o espaço do bloco de exportação e os geradores dos gráficos da R01."""
    with st.container(key="vrac-panel-overview-results"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.subheader("Resultados calculados")
            info_button(overview.warnings, key="overview-avisos")
        st.caption(
            f"Recorte: {center} · {', '.join(departments)}. "
            "Os resultados abaixo correspondem ao último cálculo com estes filtros."
        )
        _overview_provenance(overview, generated_at, center)
        if overview.status not in {OverviewStatus.VALID, OverviewStatus.PARTIAL}:
            st.info(overview.narrative)
            return None, {}
        export_slot = st.container()
        if overview.status == OverviewStatus.PARTIAL:
            st.caption(
                "Situação: Parcial — composição calculada; fonte de Horas Reais indisponível."
            )

        figure, reading = st.columns([1, 2.4], gap="medium", vertical_alignment="center")
        with figure:
            render_faculty_metric(overview, prefix="overview")
        with reading, st.container(key="vrac-narrative-overview"):
            st.markdown(overview.narrative)

        charts = render_composition(
            overview, branding, prefix="overview", export_context=export_context
        )
        render_faculty_details(overview)
        stem = f"vrac-r01-{overview.department}-{generated_at:%Y%m%d-%H%M%S}"
        st.html('<div class="vrac-subtitle">Outros arquivos</div>')
        with st.container(horizontal=True):
            download_button(
                "Baixar resumo (CSV)",
                summary_csv(overview, generated_at, export_context),
                file_name=f"{stem}-resumo.csv",
                mime="text/csv",
                key="overview_download_summary",
                type="tertiary",
            )
            download_button(
                "Baixar lista de conferência (CSV)",
                detail_csv(overview, generated_at, export_context),
                file_name=f"{stem}-lista.csv",
                mime="text/csv",
                key="overview_download_detail",
                type="tertiary",
            )
    return export_slot, charts


def _overview_provenance(overview: FacultyOverview, generated_at: datetime, center: str) -> None:
    used_filters(
        {
            "Centro": center,
            "Departamento": overview.department,
            "Referência": "Cadastro atual",
            "Unidade": UNIT_LABEL,
            **dict(describe_filters(overview.filters)),
            "Origem": overview.source,
        },
        f"{nature(overview.source)} · versão {overview.version} · "
        f"snapshot {overview.fingerprint[:12]} · "
        f"cálculo {generated_at:%d/%m/%Y %H:%M:%S} UTC · extração: horário não registrado · "
        "atualização institucional: não disponível",
    )
