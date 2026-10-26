"""Tela mínima de fase 0; sem cálculos de análises ou conexão ao banco."""

from dataclasses import asdict

import pandas as pd
import streamlit as st

from vrac.authorization import authorize_data_access
from vrac.settings import ConfigurationError, load_settings
from vrac.synthetic import DEPARTMENTS, PERIODS, load_demo_data, select_demo_data


def main() -> None:
    st.set_page_config(page_title="VRAC | Demonstração", page_icon="📊", layout="wide")
    st.title("Análises acadêmicas da VRAC")
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
    st.caption("Preparação do projeto · fase 0 · nenhuma fonte institucional conectada")
    st.subheader("Análises disponíveis")
    st.info(
        "As análises serão disponibilizadas após a validação das fontes e das regras. "
        "Por enquanto, você pode explorar exemplos fictícios para avaliar a tela."
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
