"""Apresentação compartilhada da composição e dos detalhes docentes da R01."""

from collections.abc import Sequence
from typing import Literal

import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt

from vrac.analyses.export import DETAIL_COLUMNS
from vrac.analyses.faculty_overview import UNIT_LABEL, FacultyOverview
from vrac.branding import Branding
from vrac.charts import distribution_bars, figure_png
from vrac.web_charts import interactive_bars


def render_faculty_metric(overview: FacultyOverview) -> None:
    with st.container(horizontal_alignment="center"):
        st.metric(
            "Quantidade de professores",
            overview.total,
            border=True,
            width=340,
            help=f"Contagem de {UNIT_LABEL} no cadastro atual, como o cartão do painel.",
        )


def _format(value: object) -> str:
    if value is None or value is pd.NA or (isinstance(value, float) and pd.isna(value)):
        return "ausente"
    if isinstance(value, int | float) and not isinstance(value, bool):
        return str(value) if isinstance(value, int) else f"{value:g}".replace(".", ",")
    return str(value)


def _composition_chart(
    items: Sequence[tuple[str, int]],
    *,
    name: str,
    title: str,
    label: str,
    unit: str,
    orientation: Literal["vertical", "horizontal"],
    branding: Branding,
    prefix: str,
    context: str,
) -> bytes | None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        if not items:
            st.info("Sem registros para esta distribuição no recorte selecionado.")
            return None
        st.altair_chart(
            interactive_bars(
                items,
                label=label,
                unit=unit,
                branding=branding,
                orientation=orientation,
                color="yellow",
            ),
            width="stretch",
            theme=None,
            key=f"{prefix}_chart_{name}",
        )
        st.caption(f"Unidade: {unit}.")
        figure = distribution_bars(
            items,
            title=title,
            unit=unit,
            branding=branding,
            orientation=orientation,
            color="yellow",
        )
        try:
            figure.text(
                0.01,
                0.01,
                f"DEMONSTRAÇÃO — DADOS SINTÉTICOS | {context}",
                fontsize=7,
                family=branding.tokens["typography"]["body_family"],
            )
            figure.tight_layout(rect=(0, 0.06, 1, 1))
            png = figure_png(figure)
        finally:
            plt.close(figure)
        with st.expander("Tabela e exportação do gráfico"):
            st.dataframe(
                pd.DataFrame(items, columns=[label, "Quantidade"]),
                hide_index=True,
                width="stretch",
            )
            st.download_button(
                "Baixar gráfico (PNG)",
                png,
                file_name=f"vrac-R01-{name}.png",
                mime="image/png",
                key=f"{prefix}_png_{name}",
            )
        return png


def render_composition(
    overview: FacultyOverview, branding: Branding, *, prefix: str
) -> dict[str, bytes]:
    """Distribuições com as contagens calculadas; sem recompor totais pelas barras."""
    files: dict[str, bytes] = {}
    charts = (
        (
            "departamento",
            "Quantidade de professores por Departamento",
            "Departamento",
            overview.by_department,
            "linhas com matrícula",
            "vertical",
        ),
        (
            "quadro",
            "Quantidade de professores por Quadro",
            "Quadro",
            overview.by_cadre,
            UNIT_LABEL,
            "vertical",
        ),
        (
            "categoria",
            "Quantidade de professores por Categoria Funcional (Cargo)",
            "Categoria funcional",
            overview.by_category,
            "linhas com matrícula",
            "horizontal",
        ),
    )
    columns = st.columns(2)
    for index, (name, title, label, items, unit, orientation) in enumerate(charts):
        target = columns[index] if index < 2 else st.container()
        with target:
            png = _composition_chart(
                items,
                name=name,
                title=title,
                label=label,
                unit=unit,
                orientation=orientation,
                branding=branding,
                prefix=prefix,
                context=f"{overview.department} | Cadastro atual | {overview.fingerprint[:12]}",
            )
        if png is not None:
            files[f"R01/grafico-{name}.png"] = png
    st.caption(
        "Por quadro conta matrículas funcionais distintas; por categoria e departamento "
        "conta linhas do cadastro com matrícula, como os visuais do painel. "
        "As barras não devem ser somadas para reconstruir o total. "
        "Clique numa barra para destacar; clique duas vezes para limpar. "
        "O destaque não altera filtros, resultados ou arquivos."
    )
    return files


def _detail_frames(overview: FacultyOverview) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ordena somente para exibição e mantém linhas repetidas e estados da fonte."""
    rows = sorted(
        overview.detail,
        key=lambda row: ((row.name or "").casefold(), row.registration or ""),
    )
    labels = dict(DETAIL_COLUMNS) | {"weekly_hours": "CH contratada"}
    general = tuple(key for key, _ in DETAIL_COLUMNS[:5])
    workload = (
        "real_hours_semester",
        "department",
        "registration",
        "name",
        "cadre",
        "category",
        "indicator",
        "real_hours",
        "weekly_hours",
        "tenure_years",
        "degree",
        "dual_role",
        "extraordinary",
        "hours_state",
    )
    return tuple(
        pd.DataFrame(
            [[_format(getattr(row, key)) for key in fields] for row in rows],
            columns=[labels[key] for key in fields],
        )
        for fields in (general, workload)
    )


def render_faculty_details(overview: FacultyOverview) -> None:
    """Lista geral e detalhe das Horas Reais já calculadas, sem nova regra analítica."""
    general_tab, workload_tab = st.tabs(
        ["Informações gerais dos professores", "CH Real dos professores em disciplinas"]
    )
    general, workload = _detail_frames(overview)
    with general_tab:
        st.subheader("Informações gerais dos professores")
        if general.empty:
            st.info("Sem registros docentes para o recorte selecionado.")
        else:
            st.dataframe(general, hide_index=True, width="stretch")
        st.caption(
            "Dados fictícios do cadastro atual, ordenados por nome. "
            "Cada linha é um registro do cadastro; não representa necessariamente uma pessoa única."
        )
    with workload_tab:
        st.subheader("CH Real dos professores em disciplinas")
        if workload.empty:
            st.info("Sem registros docentes para o recorte selecionado.")
        else:
            st.dataframe(workload, hide_index=True, width="stretch")
        st.caption(
            "Dados fictícios. Horas Reais: soma da fonte dedicada no maior semestre "
            "de cada matrícula, indicado na tabela; não são reconstruídas pelas disciplinas. "
            "CH contratada corresponde à carga semanal do cadastro. "
            "A unidade institucional das Horas Reais permanece não confirmada. "
            "Zero é um valor informado; ausente pode indicar nulo na fonte, falta de registro "
            "ou fonte indisponível, conforme Estado das Horas Reais. "
            "O indicador reproduz a regra documentada e não avalia produtividade."
        )
