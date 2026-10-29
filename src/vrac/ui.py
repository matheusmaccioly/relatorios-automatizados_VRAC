"""Tela em português: composição docente pelo fluxo da fase 3 e fixture da fase 0.

A tela não calcula: monta a solicitação, chama o cálculo e apresenta o estado que o
resultado declara. Nenhuma regra é escolhida aqui — a regra candidata é um filtro
explícito e permanece identificada como não aprovada.
"""

from dataclasses import asdict
from datetime import date

import pandas as pd
import streamlit as st

from vrac.analyses.catalog import AnalysisCatalog, load_catalog
from vrac.analyses.contracts import (
    AcademicPeriod,
    AnalysisId,
    AnalysisRequest,
    AnalysisResult,
    ContractError,
    EntityKey,
    EntityKind,
    TemporalBasis,
)
from vrac.analyses.faculty import faculty_result
from vrac.analyses.repository import RealAdapterBlocked, select_repository
from vrac.analyses.rules import CANDIDATE_FACULTY_RULES, FacultyRule, rule_blockers
from vrac.authorization import authorize_data_access
from vrac.branding import Branding, load_branding
from vrac.exports import ExportBlocked, export_filename, result_csv, result_json
from vrac.presentation import (
    ViewState,
    build_view,
    composition_chart,
    filters_table,
    metadata_table,
    result_table,
)
from vrac.settings import ConfigurationError, Settings, load_settings
from vrac.synthetic import (
    DEPARTMENTS,
    PERIODS,
    SyntheticDataset,
    demo_period,
    load_demo_data,
    select_demo_data,
)

_GROUPINGS = {
    "Sem distribuição": None,
    "Categoria do vínculo": EntityKind.EMPLOYMENT_CATEGORY,
    "Quadro": EntityKind.CADRE,
    "Categoria funcional": EntityKind.FUNCTIONAL_CATEGORY,
    "Situação do vínculo": EntityKind.STATUS,
}


def main() -> None:
    branding = load_branding()
    st.set_page_config(page_title="VRAC | Demonstração", layout="wide")
    st.html(branding.styles)
    st.image(
        str(branding.logo),
        width=branding.tokens["marks"]["display_width"],
        caption=None,
    )
    st.title("Análises acadêmicas da VRAC")
    st.caption(
        "Identidade visual aplicada aos materiais fornecidos · revisão institucional pendente"
    )
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

    _fixture_section(settings)
    st.divider()
    _faculty_section(settings, branding)


def _fixture_section(settings: Settings) -> None:
    """Seção da fase 0: registros fictícios sem consolidação nem cálculo."""
    st.caption("Preparação do projeto · fase 0 · nenhuma fonte institucional conectada")
    st.subheader("Registros fictícios da fundação")
    st.info(
        "Esta seção mostra os registros fictícios sem nenhuma consolidação, para "
        "conferir a tela. A composição docente calculada fica na seção seguinte."
    )
    department = st.selectbox("Departamento fictício", DEPARTMENTS)
    period = st.selectbox("Período fictício", PERIODS, index=1)
    filters = (department, period)
    if st.session_state.get("demo_filters") != filters:
        st.session_state.pop("demo_data", None)
        st.session_state.pop("demo_filters", None)

    if st.button("Mostrar dados de demonstração", type="primary"):
        data = load_demo_data(settings)
        st.session_state["demo_data"] = select_demo_data(data, department=department, period=period)
        st.session_state["demo_filters"] = filters

    data = st.session_state.get("demo_data")
    if data is None:
        st.caption("Escolha os filtros e mostre os dados fictícios.")
        return

    st.subheader("Filtros usados na demonstração")
    st.table(pd.DataFrame([{"Departamento": department, "Período": period, "Modo": "Sintético"}]))
    st.caption(
        f"Dados fictícios · versão {data.version} · atualização institucional: não se aplica"
    )
    if not data.faculty and not data.allocations:
        st.info("Sem dados sintéticos para este recorte. Ausência de registros não significa zero.")
        return

    _fixture_tables(data)


def _fixture_tables(data: SyntheticDataset) -> None:
    st.subheader("Registros docentes fictícios")
    st.dataframe(
        pd.DataFrame([asdict(row) for row in data.faculty]).rename(
            columns={
                "department": "Departamento do vínculo",
                "period": "Período",
                "reference_month": "Mês de referência",
                "teacher_id": "Docente fictício",
                "contract_id": "Vínculo fictício",
                "employment_type": "Tipo de vínculo fictício",
                "real_hours": "Horas Reais fictícias (h/semana)",
            }
        ),
        hide_index=True,
    )
    st.subheader("Alocações fictícias por turma e currículo")
    st.dataframe(
        pd.DataFrame([asdict(row) for row in data.allocations]).rename(
            columns={
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
        ),
        hide_index=True,
    )
    st.caption(
        "Os exemplos incluem vínculos e meses repetidos, compartilhamento e atuação em outro "
        "departamento. Célula vazia significa informação ausente. Não há consolidação docente "
        "ou cálculo oficial de carga horária nesta demonstração."
    )


def _faculty_section(settings: Settings, branding: Branding) -> None:
    """Fluxo de composição docente: filtros, regra candidata, cálculo e estados."""
    st.subheader("Análises disponíveis · composição docente")
    catalog = load_catalog()
    st.caption(
        "Fluxo completo com dados fictícios. A definição institucional da contagem "
        "continua pendente; nenhum número desta seção tem validade institucional."
    )

    department = st.selectbox("Departamento do vínculo", DEPARTMENTS, key="faculty_department")
    period_id = st.selectbox("Período", PERIODS, index=1, key="faculty_period")
    period = demo_period(period_id)
    rule = _rule_selector()
    grouping_label = st.selectbox("Distribuição", tuple(_GROUPINGS), key="faculty_grouping")
    grouping = _GROUPINGS[grouping_label]
    snapshot = _snapshot_selector(rule, period)

    blockers = rule_blockers(rule, catalog)
    if blockers:
        st.info(
            "Esta regra ainda não está aprovada. Pendências registradas: "
            + ", ".join(blockers)
            + ". O resultado será apresentado como parcial."
        )

    signature = (department, period_id, rule.rule_id, grouping_label, str(snapshot))
    if st.session_state.get("faculty_signature") != signature:
        st.session_state.pop("faculty_result", None)
        st.session_state.pop("faculty_signature", None)

    if st.button("Calcular composição docente", type="primary", key="faculty_run"):
        with st.spinner("Executando o cálculo no recorte informado…"):
            outcome = _run_faculty(
                settings=settings,
                catalog=catalog,
                department=department,
                period_id=period_id,
                rule=rule,
                grouping=grouping,
                snapshot=snapshot,
            )
        if isinstance(outcome, str):
            st.error(outcome)
            return
        st.session_state["faculty_result"] = outcome
        st.session_state["faculty_signature"] = signature

    result = st.session_state.get("faculty_result")
    if result is None:
        st.caption("Escolha o recorte e a regra, depois calcule. Nada é executado antes disso.")
        return
    _render_faculty(result, rule, branding)


def _rule_selector() -> FacultyRule:
    labels = {f"{item.label} — NÃO APROVADA": item for item in CANDIDATE_FACULTY_RULES}
    chosen = st.selectbox(
        "Regra candidata de contagem",
        tuple(labels),
        key="faculty_rule",
        help=(
            "As quatro candidatas vêm da documentação dos painéis. A escolha "
            "institucional depende de Talita e do responsável pela fonte."
        ),
    )
    return labels[chosen]


def _snapshot_selector(rule: FacultyRule, period: AcademicPeriod) -> date | None:
    """Foto exige data explícita dentro do período; nada é presumido."""
    if rule.temporal_basis != TemporalBasis.SNAPSHOT:
        return None
    return st.date_input(
        "Data da foto",
        value=period.starts_on,
        min_value=period.starts_on,
        max_value=period.ends_on,
        key="faculty_snapshot",
        format="DD/MM/YYYY",
    )


def _run_faculty(
    *,
    settings: Settings,
    catalog: AnalysisCatalog,
    department: str,
    period_id: str,
    rule: FacultyRule,
    grouping: EntityKind | None,
    snapshot: date | None,
) -> AnalysisResult | str:
    """Erro técnico não vira resultado; devolve a mensagem para o estado de erro."""
    try:
        request = AnalysisRequest(
            analysis_id=AnalysisId.FACULTY,
            period=demo_period(period_id),
            filters=(EntityKey(EntityKind.EMPLOYMENT_DEPARTMENT, department),),
            mode=settings.data_mode,
            temporal_basis=rule.temporal_basis,
            snapshot_on=snapshot,
            faculty_counting_basis=rule.counting_basis,
            semantic_variant_id=rule.semantic_variant_id,
        )
        dataset = load_demo_data(settings)
        repository = select_repository(request, dataset)
        return faculty_result(request, rule, catalog, repository, grouping=grouping)
    except RealAdapterBlocked as error:
        return str(error)
    except (ContractError, ValueError):
        return (
            "Não foi possível concluir o cálculo com os parâmetros informados. "
            "Nenhum resultado foi apresentado."
        )


def _render_faculty(result: AnalysisResult, rule: FacultyRule, branding: Branding) -> None:
    view = build_view(result)
    if view.state == ViewState.BLOCKED:
        st.error(view.headline)
    elif view.state == ViewState.ERROR:
        st.error(view.headline)
    elif view.state == ViewState.EMPTY:
        st.info(view.headline)
    elif view.state == ViewState.PARTIAL:
        st.warning(view.headline)
    else:
        st.success(view.headline)

    st.caption(f"Estado da tela: {view.state.value}")

    if result.data:
        st.subheader("Resultados calculados")
        st.dataframe(result_table(result), hide_index=True)
        figure = composition_chart(result, branding.tokens)
        if figure is not None:
            st.pyplot(figure)

    st.subheader("Filtros efetivos")
    st.table(filters_table(result.request, rule))
    st.subheader("Origem, versões e execução")
    st.table(metadata_table(result))

    if result.warnings:
        st.subheader("Limitações e avisos")
        for warning in result.warnings:
            st.markdown(f"- {warning}")

    _downloads(result, rule)


def _downloads(result: AnalysisResult, rule: FacultyRule) -> None:
    try:
        csv_bytes = result_csv(result, rule)
        json_bytes = result_json(result, rule)
    except ExportBlocked as error:
        st.caption(str(error))
        return
    st.subheader("Baixar o resultado exibido")
    st.caption(
        "Os arquivos repetem recorte, versões e avisos, para que o número não circule "
        "sem suas limitações."
    )
    left, right = st.columns(2)
    left.download_button(
        "Baixar CSV",
        data=csv_bytes,
        file_name=export_filename(result, "csv"),
        mime="text/csv",
    )
    right.download_button(
        "Baixar JSON",
        data=json_bytes,
        file_name=export_filename(result, "json"),
        mime="application/json",
    )
