"""Gráficos Matplotlib com cores e fontes dos tokens de branding."""

import io
import json
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
    figure, axis = plt.subplots(
        figsize=(8, max(2.4, len(items) * 0.42 + 1) if orientation == "horizontal" else 3.5),
        dpi=150,
    )
    figure.patch.set_facecolor(colors["white"])
    axis.set_facecolor(colors["white"])
    if orientation == "vertical":
        bars = axis.bar(labels, values, width=0.4, color=colors[color])
        axis.set_ylim(0, max(values, default=0) * 1.22 or 1)
        axis.set_ylabel(unit, family=family, fontsize=8)
        grid_axis = "y"
        axis.yaxis.get_major_locator().set_params(integer=True)
    else:
        bars = axis.barh(labels[::-1], values[::-1], height=0.42, color=colors[color])
        axis.set_xlim(0, max(values, default=0) * 1.2 or 1)
        axis.set_xlabel(unit, family=family, fontsize=8)
        grid_axis = "x"
        axis.xaxis.get_major_locator().set_params(integer=True)
    axis.bar_label(bars, padding=5, fontsize=9, color=colors["black"], family=family)
    axis.set_title(title, loc="left", family=family, color=colors["black"], fontsize=11, pad=15)
    axis.grid(axis=grid_axis, color=colors["line"], linewidth=0.6)
    axis.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(colors["line"])
    axis.tick_params(labelsize=9, length=0)
    for label in (*axis.get_xticklabels(), *axis.get_yticklabels()):
        label.set_family(family)
    figure.tight_layout()
    return figure


def academic_chart(
    result: "CalculatedAnalysis", specification: "ChartSpec", branding: Branding
) -> Figure:
    """Arquivos PNG das mesmas séries web; ausências nunca viram zero."""
    colors = branding.tokens["colors"]
    family = _register_fonts(branding)
    table = next(t for t in result.tables if t.key == specification.table)
    if specification.table in {"real_distribution", "contract_distribution"}:
        items = sorted(table.rows, key=lambda row: -row[1])
        figure, axis = plt.subplots(figsize=(9.5, 4.7), dpi=140)
        figure.set_label(result.source)
        values = [row[1] for row in items]
        axis.barh(
            range(len(items)),
            values,
            left=[-v / 2 for v in values],
            color=colors["blue"],
            height=0.75,
        )
        axis.set_yticks(
            range(len(items)),
            [f"{r[0]} h" if r[0] != "ausente" else "ausente" for r in items],
            family=family,
        )
        axis.invert_yaxis()
        largest = max(values, default=1) or 1
        axis.set_xlim(-largest * 0.8, largest * 0.8)
        for i, value in enumerate(values):
            axis.text(value / 2 + largest * 0.03, i, str(value), va="center", family=family)
        axis.set_xticks([])
        for spine in axis.spines.values():
            spine.set_visible(False)
        axis.set_title(specification.title, family=family, loc="left", pad=20)
        axis.set_xlabel("Quantidade de vínculos por carga horária", family=family)
        figure.text(0.02, 0.015, nature(result.source), family=family, fontsize=7)
        figure.tight_layout(rect=(0, 0.045, 1, 1))
        return figure
    xi = table.columns.index(specification.x)
    monthly = specification.table == "monthly_history"
    labels = [str(row[xi]) for row in table.rows]
    figure, axis = plt.subplots(
        figsize=(max(9.5, len(labels) * 0.25) if monthly else 9.5, 4.7), dpi=140
    )
    figure.set_label(result.source)
    figure.patch.set_facecolor(colors["white"])
    axis.set_facecolor(colors["white"])
    palette = list(branding.series)
    markers = ("o", "s", "^", "D", "v")
    bottom = [0.0] * len(labels)
    for index, name in enumerate(specification.series):
        yi = table.columns.index(name)
        values = [float("nan") if row[yi] is None else float(row[yi]) for row in table.rows]
        if specification.kind in {"bar", "grouped_bar", "stacked_bar"}:
            grouped = specification.kind == "grouped_bar"
            width = 0.8 / len(specification.series) if grouped else 0.5
            positions = [
                x - 0.4 + width * (index + 0.5) if grouped else x for x in range(len(labels))
            ]
            bars = axis.bar(
                positions,
                values,
                bottom=bottom if specification.kind == "stacked_bar" else None,
                color=palette[index % len(palette)],
                width=width,
                edgecolor=colors["white"],
                linewidth=0.6,
                label=name if len(specification.series) > 1 else None,
            )
            if monthly:
                axis.bar_label(
                    bars,
                    label_type="center",
                    fontsize=7,
                    family=family,
                    labels=[f"{v:g}" if v > 0 else "" for v in values],
                )
            if specification.kind == "stacked_bar":
                bottom = [a + b for a, b in zip(bottom, values, strict=True)]
        else:
            axis.plot(
                range(len(labels)),
                values,
                color=palette[index % len(palette)],
                marker=markers[index % len(markers)],
                linewidth=2,
                markersize=4.5,
                linestyle="-" if index < len(palette) else "--",
                label=name,
            )
            if monthly:
                for position, value in enumerate(values):
                    if value == value:
                        axis.annotate(
                            f"{value:g}",
                            (position, value),
                            xytext=(0, 9),
                            textcoords="offset points",
                            ha="center",
                            fontsize=7,
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
                -0.13,
                semester,
                transform=axis.get_xaxis_transform(),
                ha="center",
                family=family,
                fontsize=8,
            )
            if positions[0] > 0:
                axis.axvline(positions[0] - 0.5, color=colors["line"], linewidth=0.6)
        axis.margins(y=0.2)
    crowded_students = table.key == "student_general" and len(labels) > 12
    axis.set_xticks(
        range(len(labels)),
        labels,
        rotation=45
        if crowded_students
        else (25 if any(len(label) > 12 for label in labels) else 0),
        ha="right" if crowded_students or any(len(label) > 12 for label in labels) else "center",
    )
    axis.set_title(
        specification.title, loc="left", fontsize=12, family=family, color=colors["black"]
    )
    axis.set_ylabel(
        "Presenças por quadro"
        if monthly and specification.kind == "stacked_bar"
        else chart_unit(result, specification),
        family=family,
        fontsize=9,
    )
    axis.grid(axis="y", color=colors["line"], linewidth=0.6)
    axis.set_axisbelow(True)
    axis.yaxis.get_major_locator().set_params(integer=True)
    if monthly or table.key == "student_general":
        axis.set_ylim(bottom=0)
        axis.yaxis.get_major_locator().set_params(integer=True, min_n_ticks=1)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(colors["line"])
    axis.tick_params(length=0)
    if axis.get_legend_handles_labels()[0]:
        legend = axis.legend(frameon=False, fontsize=8, loc="best")
        for label in legend.get_texts():
            label.set_family(family)
    for label in (*axis.get_xticklabels(), *axis.get_yticklabels()):
        label.set_family(family)
    axis.tick_params(labelsize=8)
    figure.text(
        0.02,
        0.015,
        f"{nature(result.source)} | {result.department} | "
        f"{result.filters.first_period} a {result.filters.last_period}",
        family=family,
        color=colors["black"],
        fontsize=7,
    )
    figure.tight_layout(rect=(0, 0.045, 1, 1))
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
