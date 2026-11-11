"""Gráficos Matplotlib com cores e fontes dos tokens de branding."""

import io
import json
import textwrap
import threading
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING

import matplotlib

from vrac.provenance import is_institutional, nature

matplotlib.use("Agg")

from matplotlib import font_manager  # noqa: E402
from matplotlib import pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from vrac.analyses.academic import chart_unit  # noqa: E402
from vrac.branding import Branding  # noqa: E402

_REGISTERED: set[str] = set()
_DRAWING = threading.Lock()

if TYPE_CHECKING:
    from vrac.analyses.academic import CalculatedAnalysis, ChartSpec


def _register_fonts(branding: Branding) -> str:
    """Registrar as fontes locais fornecidas; sem download ou fonte do sistema presumida."""
    for font in branding.tokens["fonts"]:
        path = str(branding.root / font["file"])
        if path not in _REGISTERED:
            font_manager.fontManager.addfont(path)
            _REGISTERED.add(path)
    return branding.tokens["typography"]["body_family"]


def horizontal_bars(
    items: Sequence[tuple[str, int]], *, title: str, unit: str, branding: Branding
) -> Figure:
    """Uma série: barras finas em azul, sem legenda; o título nomeia a série."""
    colors = branding.tokens["colors"]
    family = _register_fonts(branding)
    labels = [label for label, _ in items][::-1]
    values = [value for _, value in items][::-1]
    figure, axis = plt.subplots(figsize=(6.4, 0.4 * len(items) + 1.1), dpi=150)
    figure.patch.set_facecolor(colors["white"])
    axis.set_facecolor(colors["white"])
    bars = axis.barh(labels, values, height=0.32, color=colors["blue"])
    # Rótulo de valor na ponta: poucas barras, texto em preto, não na cor da série.
    axis.bar_label(bars, padding=4, fontsize=9, color=colors["black"], family=family)
    axis.set_title(title, loc="left", fontsize=11, color=colors["black"], family=family, pad=10)
    axis.set_xlabel(unit, fontsize=8, color=colors["black"], family=family)
    axis.xaxis.get_major_locator().set_params(integer=True)
    axis.set_xlim(0, max(values) * 1.15 if values and max(values) > 0 else 1)
    axis.grid(axis="x", color=colors["line"], linewidth=0.6)
    axis.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(colors["line"])
    axis.tick_params(colors=colors["black"], labelsize=9, length=0)
    for label in (*axis.get_xticklabels(), *axis.get_yticklabels()):
        label.set_family(family)
    figure.tight_layout()
    return figure


def distribution_bars(
    items: Sequence[tuple[str, int]],
    *,
    title: str,
    unit: str,
    branding: Branding,
    orientation: str = "horizontal",
    color: str = "blue",
    keep_order: bool = False,
) -> Figure:
    """Distribuições docentes: direção e cor declaradas também nas exportações."""
    if orientation not in {"horizontal", "vertical"}:
        raise ValueError("Orientação de gráfico inválida.")
    colors = branding.tokens["colors"]
    family = _register_fonts(branding)
    # Mesma ordem da tela: maiores valores primeiro, empates na ordem recebida.
    ordered = list(items) if keep_order else sorted(items, key=lambda item: -item[1])
    labels = [label for label, _ in ordered]
    values = [value for _, value in ordered]
    # Proporção próxima da área do slide; fontes legíveis depois da redução no PDF.
    figure, axis = plt.subplots(
        figsize=(12, max(3.6, len(items) * 0.55 + 1.6) if orientation == "horizontal" else 5.2),
        dpi=150,
    )
    figure.patch.set_facecolor(colors["white"])
    axis.set_facecolor(colors["white"])
    if orientation == "vertical":
        bars = axis.bar(labels, values, width=0.4, color=colors[color])
        axis.set_ylim(0, max(values, default=0) * 1.22 or 1)
        axis.set_ylabel(unit, family=family, fontsize=11)
        grid_axis = "y"
        axis.yaxis.get_major_locator().set_params(integer=True)
    else:
        bars = axis.barh(labels[::-1], values[::-1], height=0.42, color=colors[color])
        axis.set_xlim(0, max(values, default=0) * 1.2 or 1)
        axis.set_xlabel(unit, family=family, fontsize=11)
        grid_axis = "x"
        axis.xaxis.get_major_locator().set_params(integer=True)
    axis.bar_label(bars, padding=5, fontsize=11, color=colors["black"], family=family)
    axis.set_title(
        title, loc="left", family=family, color=colors["black"], fontsize=15, pad=15, weight="bold"
    )
    axis.grid(axis=grid_axis, color=colors["line"], linewidth=0.6)
    axis.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(colors["line"])
    axis.tick_params(labelsize=11, length=0)
    for label in (*axis.get_xticklabels(), *axis.get_yticklabels()):
        label.set_family(family)
    figure.tight_layout()
    return figure


def _wrap(label: str, width: int = 16) -> str:
    """Rótulos longos em até três linhas, sem girar o texto."""
    lines = textwrap.wrap(label, width) or [label]
    return "\n".join(lines[:2] + ([" ".join(lines[2:])] if len(lines) > 2 else []))


def _number(value: float, percent: bool) -> str:
    if percent:
        return f"{value:.1f}".replace(".", ",") + "%"
    return f"{value:g}".replace(".", ",")


def academic_chart(
    result: "CalculatedAnalysis", specification: "ChartSpec", branding: Branding
) -> Figure:
    """PNG das mesmas séries da tela, legível no PDF; ausências nunca viram zero."""
    colors = branding.tokens["colors"]
    family = _register_fonts(branding)
    table = next(t for t in result.tables if t.key == specification.table)
    unit = chart_unit(result, specification)
    percent = unit == "%"
    if specification.table in {"real_distribution", "contract_distribution"}:
        items = sorted(table.rows, key=lambda row: -row[1])
        figure, axis = plt.subplots(figsize=(12, 5.2), dpi=150)
        figure.set_label(result.source)
        figure.patch.set_facecolor(colors["white"])
        values = [row[1] for row in items]
        axis.barh(
            range(len(items)),
            values,
            left=[-v / 2 for v in values],
            color=colors["blue"],
            height=0.72,
        )
        axis.set_yticks(
            range(len(items)),
            [f"{r[0]} h" if r[0] != "ausente" else "ausente" for r in items],
            family=family,
            fontsize=11,
        )
        axis.invert_yaxis()
        largest = max(values, default=1) or 1
        axis.set_xlim(-largest * 0.75, largest * 0.75)
        for i, value in enumerate(values):
            axis.text(
                value / 2 + largest * 0.025, i, str(value), va="center", family=family, fontsize=11
            )
        axis.set_xticks([])
        axis.tick_params(length=0)
        for spine in axis.spines.values():
            spine.set_visible(False)
        axis.set_title(
            specification.title, family=family, loc="left", pad=16, fontsize=15, weight="bold"
        )
        axis.set_xlabel("Quantidade de professores", family=family, fontsize=11)
        figure.text(0.01, 0.012, nature(result.source), family=family, fontsize=8)
        figure.tight_layout(rect=(0, 0.04, 1, 1))
        return figure
    xi = table.columns.index(specification.x)
    monthly = specification.table == "monthly_history"
    labels = [str(row[xi]) for row in table.rows]
    figure, axis = plt.subplots(figsize=(12, 5.2), dpi=150)
    figure.set_label(result.source)
    figure.patch.set_facecolor(colors["white"])
    axis.set_facecolor(colors["white"])
    palette = list(branding.series)
    markers = ("o", "s", "^", "D", "v")
    bottom = [0.0] * len(labels)
    series = specification.series
    bars_kind = specification.kind in {"bar", "grouped_bar", "stacked_bar"}
    grouped = specification.kind == "grouped_bar"
    # Largura limitada: uma categoria não vira um bloco que ocupa o gráfico inteiro.
    group_width = min(0.8, 0.28 * len(series)) if grouped else 0.5
    total_bars = len(labels) * (len(series) if grouped else 1)
    label_bars = total_bars <= 24
    for index, name in enumerate(series):
        yi = table.columns.index(name)
        values = [float("nan") if row[yi] is None else float(row[yi]) for row in table.rows]
        color = palette[index % len(palette)]
        if bars_kind:
            width = group_width / len(series) if grouped else group_width
            positions = [
                x - group_width / 2 + width * (index + 0.5) if grouped else x
                for x in range(len(labels))
            ]
            bars = axis.bar(
                positions,
                values,
                bottom=bottom if specification.kind == "stacked_bar" else None,
                color=color,
                width=width,
                edgecolor=colors["white"],
                linewidth=0.6,
                label=name if len(series) > 1 else None,
            )
            if specification.kind != "stacked_bar" and label_bars:
                axis.bar_label(
                    bars,
                    labels=["" if v != v else _number(v, percent) for v in values],
                    padding=3,
                    fontsize=10,
                    family=family,
                    color=colors["black"],
                )
            if specification.kind == "stacked_bar":
                bottom = [a + (0 if b != b else b) for a, b in zip(bottom, values, strict=True)]
        else:
            axis.plot(
                range(len(labels)),
                values,
                color=color,
                marker=markers[index % len(markers)] if len(labels) <= 40 else None,
                linewidth=2.2,
                markersize=4.5,
                linestyle="-" if index < len(palette) else "--",
                label=name if len(series) > 1 else None,
            )
            # Só o último valor conhecido de cada série: leitura direta sem sobreposição.
            known = [(i, v) for i, v in enumerate(values) if v == v]
            if known:
                position, value = known[-1]
                axis.annotate(
                    _number(value, percent),
                    (position, value),
                    xytext=(6, 0),
                    textcoords="offset points",
                    va="center",
                    fontsize=10,
                    family=family,
                    color=color,
                    weight="bold",
                )
    if specification.kind == "stacked_bar" and total_bars <= 24:
        # Total da pilha no topo; segmentos ficam na tabela e na legenda.
        for position, total in enumerate(bottom):
            if total > 0:
                axis.text(
                    position,
                    total,
                    _number(total, False),
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    family=family,
                )
    if monthly:
        # Meses na primeira linha; semestre na segunda, sem somar competências.
        semesters = [str(row[table.columns.index("Período")]) for row in table.rows]
        labels = [str(row[table.columns.index("Mês")]) for row in table.rows]
        for semester in dict.fromkeys(semesters):
            positions = [i for i, value in enumerate(semesters) if value == semester]
            midpoint = (positions[0] + positions[-1]) / 2
            axis.text(
                midpoint,
                -0.12,
                semester,
                transform=axis.get_xaxis_transform(),
                ha="center",
                family=family,
                fontsize=10,
                weight="bold",
            )
            if positions[0] > 0:
                axis.axvline(positions[0] - 0.5, color=colors["line"], linewidth=0.8)
    many = len(labels) > 14
    long_labels = any(len(label) > 12 for label in labels)
    axis.set_xticks(
        range(len(labels)),
        labels if many or not long_labels else [_wrap(label) for label in labels],
        rotation=45 if many and long_labels else 0,
        ha="right" if many and long_labels else "center",
    )
    if bars_kind and len(labels) < 4:
        # Poucas categorias: margem lateral para a barra não ocupar o gráfico inteiro.
        extra = (4 - len(labels)) / 2
        axis.set_xlim(-0.5 - extra, len(labels) - 0.5 + extra)
    # Legenda longa em duas colunas; o título sobe o necessário para não ser coberto.
    legend_columns = min(len(series), 4)
    if sum(len(name) for name in series) > 80:
        legend_columns = min(len(series), 2)
    legend_rows = -(-len(series) // legend_columns) if len(series) > 1 else 0
    axis.set_title(
        specification.title,
        loc="left",
        fontsize=15,
        family=family,
        color=colors["black"],
        weight="bold",
        pad=14 + 22 * legend_rows,
    )
    axis.set_ylabel(
        "Presenças por quadro" if monthly and specification.kind == "stacked_bar" else unit,
        family=family,
        fontsize=11,
    )
    axis.grid(axis="y", color=colors["line"], linewidth=0.6)
    axis.set_axisbelow(True)
    # Contagens e percentuais partem de zero: sem eixo truncado nem casas decimais falsas.
    axis.set_ylim(bottom=0)
    top = axis.get_ylim()[1]
    axis.set_ylim(0, (top if top > 0 else 1) * 1.12)
    axis.yaxis.get_major_locator().set_params(integer=not percent, min_n_ticks=3)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(colors["line"])
    axis.tick_params(length=0, labelsize=11)
    if axis.get_legend_handles_labels()[0]:
        # Legenda acima da área de dados, abaixo do título: nunca cobre barras ou linhas.
        legend = axis.legend(
            frameon=False,
            fontsize=11,
            loc="lower left",
            bbox_to_anchor=(0, 1.0),
            ncol=legend_columns,
            handlelength=1.6,
            borderaxespad=0.2,
        )
        for label in legend.get_texts():
            label.set_family(family)
    for label in (*axis.get_xticklabels(), *axis.get_yticklabels()):
        label.set_family(family)
    figure.text(
        0.01,
        0.012,
        f"{nature(result.source)} | {result.department} | "
        f"{result.filters.first_period} a {result.filters.last_period}",
        family=family,
        color=colors["black"],
        fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.04 if not monthly else 0.06, 1, 1))
    return figure


def render_png(build: Callable[[], Figure], context: Mapping[str, str] | None = None) -> bytes:
    """Desenha e fecha a figura; downloads rodam fora do script e o pyplot é global."""
    with _DRAWING:
        figure = build()
        try:
            return figure_png(figure, context)
        finally:
            plt.close(figure)


def figure_png(figure: Figure, context: Mapping[str, str] | None = None) -> bytes:
    stream = io.BytesIO()
    source = figure.get_label() or (context or {}).get("Origem", "")
    figure.savefig(
        stream,
        format="png",
        dpi=150,
        facecolor=figure.get_facecolor(),
        metadata={
            "Description": nature(source)
            if is_institutional(source)
            else "DEMONSTRAÇÃO — DADOS TOTALMENTE SINTÉTICOS",
            "Contexto": json.dumps(dict(context or {}), ensure_ascii=False),
        },
    )
    return stream.getvalue()
