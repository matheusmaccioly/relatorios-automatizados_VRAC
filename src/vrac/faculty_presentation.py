"""Apresentação compartilhada da composição e dos detalhes docentes da R01."""

from collections.abc import Callable, Mapping, Sequence
from typing import Literal

import pandas as pd
import streamlit as st
from matplotlib.figure import Figure

from vrac.analyses.export import DETAIL_COLUMNS
from vrac.analyses.faculty_overview import UNIT_LABEL, FacultyOverview
from vrac.branding import Branding
from vrac.charts import distribution_bars, render_png
from vrac.indicators import indicator_distribution, indicator_label
from vrac.provenance import is_institutional, nature
from vrac.ui_kit import card_title, data_table, download_button, show_chart, single_value
from vrac.web_charts import interactive_bars

QUANTITY_COLUMNS = (
    "Horas Reais (semestre atual)",
    "CH contratada",
    "Tempo de casa (anos)",
)


def render_faculty_metric(overview: FacultyOverview, *, prefix: str) -> None:
    with st.container(key=f"vrac-kpi-{prefix}"):
        st.metric(
            "Quantidade de professores",
            overview.total,
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
    export_context: Mapping[str, str] | None = None,
    indicator: bool = False,
) -> Callable[[], bytes] | None:
    # O resultado segue a ordem de leitura, com símbolos só na tela: o PNG usa o texto.
    shown = [(indicator_label(key), value) for key, value in items] if indicator else items
    with st.container(border=True):
        card_title(title, f"Unidade: {unit}")
        if not items:
            st.info("Sem registros para esta distribuição no recorte selecionado.")
            return None
        if len(items) == 1:
            single_value(shown[0][1], shown[0][0])
        else:
            show_chart(
                f"{prefix}-{name}",
                export_context,
                lambda: interactive_bars(
                    shown,
                    label=label,
                    unit=unit,
                    branding=branding,
                    orientation=orientation,
                    keep_order=indicator,
                ),
                key=f"{prefix}_chart_{name}",
            )

        png = _composition_png(
            items,
            title=title,
            unit=unit,
            orientation=orientation,
            branding=branding,
            context=context,
            export_context=export_context,
            indicator=indicator,
        )
        with st.expander("Ver tabela do gráfico"):
            data_table(pd.DataFrame(shown, columns=[label, "Quantidade"]), numeric=["Quantidade"])
            download_button(
                "Baixar gráfico (PNG)",
                png,
                file_name=f"vrac-R01-{name}.png",
                mime="image/png",
                key=f"{prefix}_png_{name}",
                on_click="ignore",
            )
        return png


def _composition_png(
    items: Sequence[tuple[str, int]],
    *,
    title: str,
    unit: str,
    orientation: Literal["vertical", "horizontal"],
    branding: Branding,
    context: str,
    export_context: Mapping[str, str] | None,
    indicator: bool,
) -> Callable[[], bytes]:
    def figure() -> Figure:
        drawn = distribution_bars(
            items,
            title=title,
            unit=unit,
            branding=branding,
            orientation=orientation,
            keep_order=indicator,
        )
        drawn.text(
            0.01,
            0.01,
            f"{nature((export_context or {}).get('Origem', ''))} | {context}",
            fontsize=7,
            family=branding.tokens["typography"]["body_family"],
        )
        drawn.tight_layout(rect=(0, 0.06, 1, 1))
        return drawn

    return lambda: render_png(figure, export_context)


def _composition_charts(overview: FacultyOverview) -> tuple:
    """Nome, título, rótulo, contagens, unidade e orientação de cada distribuição da R01."""
    return (
        (
            "departamento",
            "Quantidade de professores por Departamento",
            "Departamento",
            overview.by_department,
            "linhas com matrícula",
            "horizontal",
        ),
        (
            "quadro",
            "Quantidade de professores por Quadro",
            "Quadro",
            overview.by_cadre,
            UNIT_LABEL,
            "horizontal",
        ),
        (
            "categoria",
            "Quantidade de professores por Categoria Funcional (Cargo)",
            "Categoria funcional",
            overview.by_category,
            "linhas com matrícula",
            "horizontal",
        ),
        (
            "resultado",
            "Resultado de carga dos professores",
            "Resultado de carga",
            indicator_distribution(row.indicator for row in overview.detail),
            "linhas do cadastro",
            "horizontal",
        ),
    )


def _chart_context(
    overview: FacultyOverview, export_context: Mapping[str, str], title: str, unit: str
) -> dict[str, str]:
    return dict(export_context) | {
        "Análise": "R01",
        "Gráfico": title,
        "Unidade": unit,
        "Avisos": " | ".join(overview.warnings),
    }


def composition_pngs(
    overview: FacultyOverview,
    branding: Branding,
    export_context: Mapping[str, str] | None = None,
) -> dict[str, Callable[[], bytes]]:
    """Mesmos PNG da tela, sem desenhá-la; usados pelo relatório completo do Início."""
    export_context = dict(export_context or {}) | {"Origem": overview.source}
    return {
        f"R01/grafico-{name}.png": _composition_png(
            items,
            title=title,
            unit=unit,
            orientation=orientation,
            branding=branding,
            context=f"{overview.department} | Cadastro atual | {overview.fingerprint[:12]}",
            export_context=_chart_context(overview, export_context, title, unit),
            indicator=name == "resultado",
        )
        for name, title, _, items, unit, orientation in _composition_charts(overview)
        if items
    }


def render_composition(
    overview: FacultyOverview,
    branding: Branding,
    *,
    prefix: str,
    export_context: Mapping[str, str] | None = None,
) -> dict[str, Callable[[], bytes]]:
    """Distribuições com as contagens calculadas; sem recompor totais pelas barras.

    Devolve geradores de PNG: o arquivo só é desenhado quando alguém o baixa.
    """
    export_context = dict(export_context or {}) | {"Origem": overview.source}
    files: dict[str, Callable[[], bytes]] = {}
    charts = _composition_charts(overview)
    # Valor único primeiro; várias categorias lado a lado, e a última ocupa a linha se sobrar.
    slots = {chart[0]: st.container() for chart in charts if len(chart[3]) <= 1}
    grid = [chart for chart in charts if len(chart[3]) > 1]
    for start in range(0, len(grid), 2):
        pair = grid[start : start + 2]
        targets = st.columns(2, gap="medium") if len(pair) == 2 else [st.container()]
        slots.update({chart[0]: target for chart, target in zip(pair, targets, strict=True)})
    for name, title, label, items, unit, orientation in charts:
        with slots[name]:
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
                indicator=name == "resultado",
                export_context=_chart_context(overview, export_context, title, unit),
            )
        if png is not None:
            files[f"R01/grafico-{name}.png"] = png
    st.caption(
        "Passe o cursor para ver os valores; clique numa barra para destacar e clique duas "
        "vezes para limpar. O destaque não altera filtros, resultados ou arquivos. "
        "Por quadro conta matrículas funcionais distintas; por categoria e departamento "
        "conta linhas do cadastro com matrícula. Não some as barras para reconstruir o total. "
        "O resultado de carga reproduz a regra do painel e não avalia produtividade."
    )
    return files


def _detail_frames(overview: FacultyOverview) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ordena somente para exibição e mantém linhas repetidas e estados da fonte."""
    rows = sorted(
        overview.detail,
        key=lambda row: ((row.name or "").casefold(), row.registration or ""),
    )
    labels = dict(DETAIL_COLUMNS) | {"weekly_hours": "CH contratada"}
    if is_institutional(overview.source):
        labels["registration"] = "Vínculo pseudonimizado"
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
            data_table(general)
        st.caption(
            "Dados do cadastro atual, ordenados por nome. "
            "Cada linha é um registro do cadastro; não representa necessariamente uma pessoa única."
        )
    with workload_tab:
        st.subheader("CH Real dos professores em disciplinas")
        if workload.empty:
            st.info("Sem registros docentes para o recorte selecionado.")
        else:
            data_table(workload, numeric=QUANTITY_COLUMNS)
        st.caption(
            "Horas Reais: soma da fonte dedicada no maior semestre "
            "de cada matrícula, indicado na tabela; não são reconstruídas pelas disciplinas. "
            "CH contratada corresponde à carga semanal do cadastro. "
            "A unidade institucional das Horas Reais permanece não confirmada. "
            "Zero é um valor informado; ausente pode indicar nulo na fonte, falta de registro "
            "ou fonte indisponível, conforme Estado das Horas Reais. "
            "O resultado reproduz a regra documentada e não avalia produtividade."
        )
