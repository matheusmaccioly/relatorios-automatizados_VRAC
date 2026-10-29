"""Tabelas e gráfico derivados de um resultado; sem Streamlit, banco ou cálculo.

A apresentação não recalcula nem completa valores. Célula sem número mostra a
situação do dado — nulo, sem registros, não calculável ou falha — e nunca zero.
Cores e tipografia vêm dos tokens institucionais, sem variantes inventadas.
"""

from dataclasses import dataclass
from enum import StrEnum

import pandas as pd
from matplotlib.figure import Figure

from vrac.analyses.contracts import (
    AnalysisRequest,
    AnalysisResult,
    Availability,
    MetricDatum,
    ResultStatus,
)
from vrac.analyses.faculty import GENERAL_METRIC, UNCLASSIFIED_METRIC
from vrac.analyses.rules import FacultyRule
from vrac.settings import DataMode

_AVAILABILITY_LABELS = {
    Availability.OBSERVED: "Observado",
    Availability.NULL: "Nulo na origem",
    Availability.NO_ROWS: "Sem registros",
    Availability.UNDEFINED: "Não calculável",
    Availability.ERROR: "Falha na origem",
}

_STATUS_LABELS = {
    ResultStatus.VALID: "Válido",
    ResultStatus.PARTIAL: "Parcial",
    ResultStatus.BLOCKED: "Bloqueado",
}

_METRIC_LABELS = {
    GENERAL_METRIC: "Total do recorte",
    UNCLASSIFIED_METRIC: "Sem classificação na dimensão",
}


class ViewState(StrEnum):
    """Estados da tela; distintos entre si e do estado do resultado."""

    READY = "pronto"
    RUNNING = "executando"
    EMPTY = "vazio"
    PARTIAL = "parcial"
    BLOCKED = "bloqueado"
    ERROR = "erro"


@dataclass(frozen=True, slots=True)
class ViewModel:
    """O que a tela mostra, já decidido fora do Streamlit."""

    state: ViewState
    headline: str
    result: AnalysisResult | None


def view_state(result: AnalysisResult) -> ViewState:
    """Vazio é um estado próprio: ausência de registros não é resultado parcial comum."""
    if result.status == ResultStatus.BLOCKED:
        return ViewState.BLOCKED
    if any(item.availability == Availability.ERROR for item in result.data):
        return ViewState.ERROR
    if all(item.availability == Availability.NO_ROWS for item in result.data):
        return ViewState.EMPTY
    if result.status == ResultStatus.PARTIAL:
        return ViewState.PARTIAL
    return ViewState.READY


def build_view(result: AnalysisResult) -> ViewModel:
    state = view_state(result)
    headlines = {
        ViewState.BLOCKED: "Resultado bloqueado: nenhuma consulta foi executada.",
        ViewState.ERROR: "Falha na origem dos dados; nenhum número foi concluído.",
        ViewState.EMPTY: ("Sem registros neste recorte. Ausência de registros não significa zero."),
        ViewState.PARTIAL: "Resultado parcial: confira as limitações antes de usar.",
        ViewState.READY: "Resultado calculado no recorte informado.",
    }
    return ViewModel(state=state, headline=headlines[state], result=result)


def _metric_label(datum: MetricDatum) -> str:
    if datum.metric in _METRIC_LABELS:
        return _METRIC_LABELS[datum.metric]
    return datum.metric.replace("por_", "Por ").replace("_", " ")


def _category_label(datum: MetricDatum) -> str:
    if not datum.dimensions:
        return "—"
    return " · ".join(item.identifier for item in datum.dimensions)


def result_table(result: AnalysisResult) -> pd.DataFrame:
    """Uma linha por métrica; o valor ausente aparece como situação, não como zero."""
    rows = [
        {
            "Métrica": _metric_label(datum),
            "Categoria": _category_label(datum),
            "Valor": datum.value if datum.availability == Availability.OBSERVED else None,
            "Unidade": datum.unit.value.replace("_", " "),
            "Situação do dado": _AVAILABILITY_LABELS[datum.availability],
        }
        for datum in result.data
    ]
    return pd.DataFrame(
        rows,
        columns=["Métrica", "Categoria", "Valor", "Unidade", "Situação do dado"],
    )


def filters_table(request: AnalysisRequest, rule: FacultyRule) -> pd.DataFrame:
    """Filtros efetivos junto do resultado, para não ler um número fora do recorte."""
    rows = [
        {"Filtro": item.kind.value.replace("_", " "), "Valor": item.identifier}
        for item in request.filters
    ]
    rows.extend(
        [
            {"Filtro": "período", "Valor": request.period.identifier},
            {
                "Filtro": "período completo",
                "Valor": "sim" if request.period.complete else "não",
            },
            {"Filtro": "regra aplicada", "Valor": rule.label},
            {"Filtro": "população", "Valor": rule.counting_basis.value.replace("_", " ")},
            {
                "Filtro": "referência temporal",
                "Valor": rule.temporal_basis.value.replace("_", " "),
            },
            {
                "Filtro": "data da foto",
                "Valor": (
                    request.snapshot_on.isoformat() if request.snapshot_on else "não se aplica"
                ),
            },
            {
                "Filtro": "modo",
                "Valor": "sintético" if request.mode == DataMode.SYNTHETIC else "real",
            },
        ]
    )
    return pd.DataFrame(rows, columns=["Filtro", "Valor"])


def metadata_table(result: AnalysisResult) -> pd.DataFrame:
    """Proveniência e versões; extração e atualização permanecem datas separadas."""
    rows = [
        {"Informação": "situação do resultado", "Valor": _STATUS_LABELS[result.status]},
        {"Informação": "execução", "Valor": result.execution_id},
        {"Informação": "calculado em", "Valor": result.created_at.isoformat()},
        {"Informação": "versão do catálogo", "Valor": result.catalog_version},
        {"Informação": "versão da regra", "Valor": result.rule_version},
        {
            "Informação": "versão da consulta",
            "Valor": result.query_version or "não há consulta revisada nesta fase",
        },
    ]
    for origin in result.origins:
        extracted = origin.extracted_at.isoformat() if origin.extracted_at else "não registrada"
        updated = origin.updated_at.isoformat() if origin.updated_at else "desconhecida"
        rows.append(
            {
                "Informação": f"origem · {origin.logical_source}",
                "Valor": (
                    f"versão {origin.version}"
                    f" · extração {extracted}"
                    f" · atualização da origem {updated}"
                ),
            }
        )
    return pd.DataFrame(rows, columns=["Informação", "Valor"])


def composition_chart(result: AnalysisResult, tokens: dict) -> Figure | None:
    """Barras das categorias observadas; não plota total nem valor ausente."""
    plotted = [
        datum
        for datum in result.data
        if datum.dimensions and datum.availability == Availability.OBSERVED
    ]
    if not plotted:
        return None
    colors = tokens["colors"]
    typography = tokens["typography"]
    figure = Figure(figsize=(7.0, 3.6), dpi=144)
    figure.patch.set_facecolor(colors["white"])
    axes = figure.add_subplot(111)
    axes.set_facecolor(colors["white"])
    labels = [_category_label(datum) for datum in plotted]
    values = [int(datum.value) for datum in plotted]
    palette = (colors["blue"], colors["cyan"], colors["black"])
    axes.bar(
        labels,
        values,
        color=[palette[index % len(palette)] for index in range(len(values))],
        width=0.6,
    )
    axes.set_ylabel(plotted[0].unit.value.replace("_", " "), color=colors["black"])
    axes.set_title(
        "Distribuição no recorte informado",
        color=colors["blue"],
        fontfamily=typography["heading_family"],
    )
    for spine in ("top", "right"):
        axes.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        axes.spines[spine].set_color(colors["black"])
    axes.tick_params(colors=colors["black"])
    for label in (*axes.get_xticklabels(), *axes.get_yticklabels()):
        label.set_fontfamily(typography["body_family"])
    # Inteiros não recebem casas decimais; contagem não é medida contínua.
    axes.set_yticks(range(0, max(values) + 1, max(1, max(values) // 5)))
    figure.tight_layout()
    return figure
