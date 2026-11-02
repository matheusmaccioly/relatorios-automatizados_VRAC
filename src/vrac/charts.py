"""Gráficos Matplotlib com cores e fontes dos tokens de branding."""

import io
from collections.abc import Sequence
from typing import TYPE_CHECKING

import matplotlib

matplotlib.use("Agg")

from matplotlib import font_manager  # noqa: E402
from matplotlib import pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from vrac.branding import Branding  # noqa: E402

_REGISTERED: set[str] = set()

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
    axis.grid(axis="x", color=colors["gray"], linewidth=0.5, alpha=0.4)
    axis.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(colors["gray"])
    axis.tick_params(colors=colors["black"], labelsize=9, length=0)
    for label in (*axis.get_xticklabels(), *axis.get_yticklabels()):
        label.set_family(family)
    figure.tight_layout()
    return figure


def academic_chart(
    result: "CalculatedAnalysis", specification: "ChartSpec", branding: Branding
) -> Figure:
    """Séries não empilhadas; ausências interrompem as curvas e nunca viram zero."""
    colors = branding.tokens["colors"]
    family = _register_fonts(branding)
    table = next(t for t in result.tables if t.key == specification.table)
    xi = table.columns.index(specification.x)
    labels = [str(row[xi]) for row in table.rows]
    figure, axis = plt.subplots(figsize=(9.5, 4.7), dpi=140)
    figure.patch.set_facecolor(colors["white"])
    axis.set_facecolor(colors["white"])
    palette = [colors[name] for name in ("blue", "cyan", "yellow", "gray", "black")]
    markers = ("o", "s", "^", "D", "v")
    for index, name in enumerate(specification.series):
        yi = table.columns.index(name)
        values = [float("nan") if row[yi] is None else float(row[yi]) for row in table.rows]
        if specification.kind == "bar":
            axis.bar(
                range(len(labels)),
                values,
                color=palette[index % len(palette)],
                width=0.5,
                label=name if len(specification.series) > 1 else None,
            )
        else:
            axis.plot(
                range(len(labels)),
                values,
                color=palette[index % len(palette)],
                marker=markers[index % len(markers)],
                linewidth=1.8,
                markersize=4,
                linestyle="-" if index < len(palette) else "--",
                label=name,
            )
    axis.set_xticks(
        range(len(labels)),
        labels,
        rotation=25 if any(len(label) > 12 for label in labels) else 0,
        ha="right" if any(len(label) > 12 for label in labels) else "center",
    )
    axis.set_title(
        specification.title, loc="left", fontsize=12, family=family, color=colors["black"]
    )
    axis.set_ylabel(table.unit, family=family, fontsize=9)
    axis.grid(axis="y", color=colors["gray"], alpha=0.3, linewidth=0.5)
    axis.set_axisbelow(True)
    axis.yaxis.get_major_locator().set_params(integer=True)
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    if specification.kind != "bar" or len(specification.series) > 1:
        legend = axis.legend(frameon=False, fontsize=8, loc="best")
        for label in legend.get_texts():
            label.set_family(family)
    for label in (*axis.get_xticklabels(), *axis.get_yticklabels()):
        label.set_family(family)
    axis.tick_params(labelsize=8)
    figure.text(
        0.02,
        0.015,
        f"DEMONSTRAÇÃO — DADOS SINTÉTICOS | {result.department} | "
        f"{result.filters.first_period} a {result.filters.last_period}",
        family=family,
        color=colors["black"],
        fontsize=7,
    )
    figure.tight_layout(rect=(0, 0.045, 1, 1))
    return figure


def figure_png(figure: Figure) -> bytes:
    stream = io.BytesIO()
    figure.savefig(
        stream,
        format="png",
        dpi=150,
        facecolor=figure.get_facecolor(),
        metadata={"Description": "DEMONSTRAÇÃO — DADOS TOTALMENTE SINTÉTICOS"},
    )
    return stream.getvalue()
