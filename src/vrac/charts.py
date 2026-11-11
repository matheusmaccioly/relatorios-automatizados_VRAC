"""Gráficos Matplotlib com cores e fontes dos tokens de branding."""

import io
import json
import re
import textwrap
import threading
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING

import matplotlib
import numpy as np

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
    from vrac.analyses.academic import CalculatedAnalysis, ChartSpec, ResultTable


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


# Painel com a proporção da área de gráfico do slide; séries longas viram vários painéis.
PANEL_SIZE = (12.0, 5.2)
PANEL_DPI = 150
PANELS_KEY = "Paineis"
MAX_MONTHS_PER_PANEL = 48
MAX_BARS_PER_PANEL = 12
MONTH_NAMES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
_COMPETENCE = re.compile(r"([0-9]{4})-([0-9]{2})")


def _time_axis(table: "ResultTable", specification: "ChartSpec") -> list[tuple[str, int]] | None:
    """(semestre, mês) de cada linha quando o eixo é mensal; calendário docente jan–jul = 1."""
    if specification.table == "monthly_history":
        period = table.columns.index("Período")
        month = table.columns.index("Mês")
        return [(str(row[period]), int(row[month])) for row in table.rows]
    xi = table.columns.index(specification.x)
    found = [_COMPETENCE.fullmatch(str(row[xi])) for row in table.rows]
    if not found or not all(found):
        return None
    axis = []
    for match in found:
        year, month = int(match[1]), int(match[2])
        if not 1 <= month <= 12:
            return None
        axis.append((f"{year}.{1 if month <= 7 else 2}", month))
    return axis


def _horizontal(specification: "ChartSpec", labels: Sequence[str], time: object) -> bool:
    """Uma série com nomes longos ou muitas categorias: barras deitadas, nomes legíveis."""
    return (
        specification.kind == "bar"
        and len(specification.series) == 1
        and time is None
        and (len(labels) > 8 or any(len(label) > 14 for label in labels))
    )


def _parts(count: int, time: list[tuple[str, int]] | None, horizontal: bool) -> list[range]:
    """Faixas de linhas por painel; meses quebram só na troca de semestre."""
    if time is not None and count > MAX_MONTHS_PER_PANEL:
        parts: list[range] = []
        start = index = 0
        while index < count:
            end = index
            while end < count and time[end][0] == time[index][0]:
                end += 1
            if end - start > MAX_MONTHS_PER_PANEL and index > start:
                parts.append(range(start, index))
                start = index
            index = end
        parts.append(range(start, count))
        return parts
    if horizontal and count > MAX_BARS_PER_PANEL:
        return [
            range(start, min(start + MAX_BARS_PER_PANEL, count))
            for start in range(0, count, MAX_BARS_PER_PANEL)
        ]
    return [range(count)]


def chart_panels(figure: Figure) -> int:
    """Quantidade de painéis empilhados na figura; 1 para gráficos simples."""
    return getattr(figure, "vrac_panels", 1)


def _text_color(hex_color: str) -> str:
    """Preto ou branco, o de maior contraste sobre o preenchimento da barra."""
    channels = [int(hex_color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    luminance = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    return "#FFFFFF" if 1.05 / (luminance + 0.05) >= (luminance + 0.05) / 0.05 else "#000000"


def academic_chart(
    result: "CalculatedAnalysis", specification: "ChartSpec", branding: Branding
) -> Figure:
    """PNG das mesmas séries da tela, legível no PDF; ausências nunca viram zero.

    Séries mensais longas e listas longas de categorias saem em painéis empilhados com a
    proporção do slide e a mesma escala; o PDF mostra um painel por página.
    """
    colors = branding.tokens["colors"]
    family = _register_fonts(branding)
    table = next(t for t in result.tables if t.key == specification.table)
    if specification.table in {"real_distribution", "contract_distribution"}:
        return _centered_distribution(result, specification, table, colors, family)
    xi = table.columns.index(specification.x)
    labels = [str(row[xi]) for row in table.rows]
    time = _time_axis(table, specification)
    horizontal = _horizontal(specification, labels, time)
    parts = _parts(len(labels), time, horizontal)
    if len(parts) == 1:
        return _panel(result, specification, branding, table, time, horizontal, parts[0], None)
    images = []
    for index, rows in enumerate(parts):
        panel = _panel(
            result, specification, branding, table, time, horizontal, rows, (index, len(parts))
        )
        try:
            panel.canvas.draw()
            images.append(np.asarray(panel.canvas.buffer_rgba()).copy())
        finally:
            plt.close(panel)
    image = np.vstack(images)
    height, width = image.shape[:2]
    figure = plt.figure(figsize=(width / PANEL_DPI, height / PANEL_DPI), dpi=PANEL_DPI)
    figure.set_label(result.source)
    figure.patch.set_facecolor(colors["white"])
    figure.figimage(image, xo=0, yo=0, origin="upper")
    figure.vrac_panels = len(parts)  # type: ignore[attr-defined]
    return figure


def _centered_distribution(
    result: "CalculatedAnalysis",
    specification: "ChartSpec",
    table: "ResultTable",
    colors: Mapping[str, str],
    family: str,
) -> Figure:
    """Distribuição de horas centrada, como no painel; ausente fica em categoria própria."""
    items = sorted(table.rows, key=lambda row: -row[1])
    figure, axis = plt.subplots(figsize=PANEL_SIZE, dpi=PANEL_DPI)
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


def _series_values(table: "ResultTable", name: str, rows: range | None = None) -> list[float]:
    yi = table.columns.index(name)
    selected = table.rows if rows is None else [table.rows[i] for i in rows]
    return [float("nan") if row[yi] is None else float(row[yi]) for row in selected]


def _panel(
    result: "CalculatedAnalysis",
    specification: "ChartSpec",
    branding: Branding,
    table: "ResultTable",
    time: list[tuple[str, int]] | None,
    horizontal: bool,
    rows: range,
    part: tuple[int, int] | None,
) -> Figure:
    colors = branding.tokens["colors"]
    family = _register_fonts(branding)
    unit = chart_unit(result, specification)
    percent = unit == "%"
    xi = table.columns.index(specification.x)
    labels = [str(table.rows[i][xi]) for i in rows]
    count = len(labels)
    series = specification.series
    stacked = specification.kind == "stacked_bar"
    bars_kind = specification.kind in {"bar", "grouped_bar", "stacked_bar"}
    grouped = specification.kind == "grouped_bar"
    # Mesma escala em todos os painéis: o leitor compara partes sem reler o eixo.
    if stacked:
        columns = [_series_values(table, name) for name in series]
        largest = max(
            (sum(0 if v != v else v for v in values) for values in zip(*columns, strict=True)),
            default=0,
        )
    else:
        largest = max(
            (v for name in series for v in _series_values(table, name) if v == v), default=0
        )
    figure, axis = plt.subplots(figsize=PANEL_SIZE, dpi=PANEL_DPI)
    figure.set_label(result.source)
    figure.patch.set_facecolor(colors["white"])
    axis.set_facecolor(colors["white"])
    title = specification.title
    if part is not None:
        if time is not None:
            title += f" · {time[rows[0]][0]} a {time[rows[-1]][0]}"
        title += f" (parte {part[0] + 1} de {part[1]})"
    if horizontal:
        _horizontal_bars(
            axis, table, specification, rows, labels, largest, colors, family, part, percent
        )
        _finish(axis, figure, result, title, unit, family, colors, (), horizontal=True)
        return figure

    palette = list(branding.series)
    markers = ("o", "s", "^", "D", "v")
    bottom = [0.0] * count
    group_width = min(0.8, 0.28 * len(series)) if grouped else (0.7 if time else 0.5)
    total_bars = count * (len(series) if grouped else 1)
    label_bars = total_bars <= 24
    # Largura de cada posição em pontos, para decidir quais rótulos cabem.
    slot = 10.4 * 72 / max(count, 1)
    size = 10 if count <= 24 else 9 if count <= 36 else 8
    single = len(series) == 1
    for index, name in enumerate(series):
        values = _series_values(table, name, rows)
        color = palette[index % len(palette)]
        if bars_kind:
            width = group_width / len(series) if grouped else group_width
            positions = [
                x - group_width / 2 + width * (index + 0.5) if grouped else x for x in range(count)
            ]
            bars = axis.bar(
                positions,
                values,
                bottom=bottom if stacked else None,
                color=color,
                width=width,
                edgecolor=colors["white"],
                linewidth=0.6,
                label=name if len(series) > 1 else None,
            )
            if not stacked and label_bars:
                axis.bar_label(
                    bars,
                    labels=["" if v != v else _number(v, percent) for v in values],
                    padding=3,
                    fontsize=10,
                    family=family,
                    color=colors["black"],
                )
            if stacked:
                _segment_labels(
                    axis, values, bottom, width * slot, largest, color, family, size, percent
                )
                bottom = [a + (0 if b != b else b) for a, b in zip(bottom, values, strict=True)]
        else:
            axis.plot(
                range(count),
                values,
                color=color,
                marker=markers[index % len(markers)],
                linewidth=2.2,
                markersize=5.5 if count <= 48 else 4,
                markeredgecolor=colors["white"],
                markeredgewidth=0.8,
                linestyle="-" if index < len(palette) else "--",
                label=name if len(series) > 1 else None,
            )
            known = [(i, v) for i, v in enumerate(values) if v == v]
            # Uma série: valor em cada ponto. Várias: só o último, para não sobrepor.
            for order, (position, value) in enumerate(known if single else known[-1:]):
                # Vale da linha: rótulo abaixo do ponto, para não ficar sobre a linha.
                below = (
                    single
                    and 0 < order < len(known) - 1
                    and value < known[order - 1][1]
                    and value < known[order + 1][1]
                    and value > (largest or 1) * 0.15
                )
                axis.annotate(
                    _number(value, percent),
                    (position, value),
                    xytext=(0, -9 if below else 8) if single else (6, 0),
                    textcoords="offset points",
                    ha="center" if single else "left",
                    va=("top" if below else "bottom") if single else "center",
                    fontsize=size if single else 10,
                    family=family,
                    color=colors["black"] if single else color,
                    weight="normal" if single else "bold",
                )
    if stacked and total_bars <= 24:
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
    if time is not None:
        _month_axis(axis, [time[i] for i in rows], family, colors)
    else:
        many = count > 14
        long_labels = any(len(label) > 12 for label in labels)
        axis.set_xticks(
            range(count),
            labels if many or not long_labels else [_wrap(label) for label in labels],
            rotation=45 if many and long_labels else 0,
            ha="right" if many and long_labels else "center",
            fontsize=11,
        )
    if bars_kind and count < 4:
        # Poucas categorias: margem lateral para a barra não ocupar o gráfico inteiro.
        extra = (4 - count) / 2
        axis.set_xlim(-0.5 - extra, count - 0.5 + extra)
    else:
        axis.set_xlim(-0.6, count - 0.4)
    # Contagens e percentuais partem de zero; folga no topo para os rótulos de valor.
    axis.set_ylim(0, (largest if largest > 0 else 1) * 1.18)
    axis.yaxis.get_major_locator().set_params(integer=not percent, min_n_ticks=1)
    axis.grid(axis="y", color=colors["line"], linewidth=0.6)
    _finish(
        axis,
        figure,
        result,
        title,
        "Presenças por quadro" if time is not None and stacked else unit,
        family,
        colors,
        series,
        horizontal=False,
    )
    return figure


def _segment_labels(
    axis,
    values: Sequence[float],
    bottom: Sequence[float],
    width_points: float,
    largest: float,
    color: str,
    family: str,
    size: int,
    percent: bool,
) -> None:
    """Valor dentro de cada segmento só quando cabe; segmento pequeno fica na tabela."""
    ink = _text_color(color)
    height_points = 3.3 * 72  # altura útil aproximada do eixo no painel
    top = (largest if largest > 0 else 1) * 1.18
    for position, (value, base) in enumerate(zip(values, bottom, strict=True)):
        if value != value or value <= 0:
            continue
        text = _number(value, percent)
        tall = value / top * height_points
        wide = len(text) * size * 0.62 + 3
        if width_points >= wide and tall >= size * 1.4:
            rotation = 0
        elif width_points >= size * 1.3 and tall >= wide + 2:
            rotation = 90
        else:
            continue
        axis.text(
            position,
            base + value / 2,
            text,
            ha="center",
            va="center",
            rotation=rotation,
            fontsize=size,
            family=family,
            color=ink,
        )


def _month_axis(
    axis, time: Sequence[tuple[str, int]], family: str, colors: Mapping[str, str]
) -> None:
    """Mês abreviado em cada ponto e semestre abaixo, com faixas alternadas por semestre."""
    count = len(time)
    rotate = count > 40
    axis.set_xticks(
        range(count),
        [MONTH_NAMES[month - 1] for _, month in time],
        rotation=90 if rotate else 0,
        fontsize=9 if rotate else 10,
    )
    semesters = [semester for semester, _ in time]
    for order, semester in enumerate(dict.fromkeys(semesters)):
        positions = [i for i, value in enumerate(semesters) if value == semester]
        if order % 2:
            axis.axvspan(
                positions[0] - 0.5,
                positions[-1] + 0.5,
                color=colors["background"],
                zorder=0,
                linewidth=0,
            )
        if positions[0] > 0:
            axis.axvline(positions[0] - 0.5, color=colors["line"], linewidth=0.8, zorder=0.5)
        axis.annotate(
            semester,
            xy=((positions[0] + positions[-1]) / 2, 0),
            xycoords=("data", "axes fraction"),
            xytext=(0, -32 if rotate else -24),
            textcoords="offset points",
            ha="center",
            va="top",
            family=family,
            fontsize=10,
            weight="bold",
        )


def _horizontal_bars(
    axis,
    table: "ResultTable",
    specification: "ChartSpec",
    rows: range,
    labels: Sequence[str],
    largest: float,
    colors: Mapping[str, str],
    family: str,
    part: tuple[int, int] | None,
    percent: bool,
) -> None:
    """Categorias na ordem da tabela, de cima para baixo, com o valor na ponta."""
    values = _series_values(table, specification.series[0], rows)
    positions = range(len(labels))
    bars = axis.barh(positions, values, height=0.55, color=colors["blue"])
    axis.set_yticks(positions, [_wrap(label, 44) for label in labels], fontsize=10)
    axis.bar_label(
        bars,
        labels=["" if v != v else _number(v, percent) for v in values],
        padding=4,
        fontsize=10,
        family=family,
        color=colors["black"],
    )
    # Último painel com menos itens mantém a espessura das barras dos anteriores.
    rows_shown = MAX_BARS_PER_PANEL if part is not None else max(len(labels), 4)
    axis.set_ylim(rows_shown - 0.5, -0.5)
    axis.set_xlim(0, (largest if largest > 0 else 1) * 1.15)
    axis.xaxis.get_major_locator().set_params(integer=not percent, min_n_ticks=1)
    axis.grid(axis="x", color=colors["line"], linewidth=0.6)


def _finish(
    axis,
    figure: Figure,
    result: "CalculatedAnalysis",
    title: str,
    unit: str,
    family: str,
    colors: Mapping[str, str],
    series: Sequence[str],
    *,
    horizontal: bool,
) -> None:
    """Título, legenda acima dos dados, eixos sem moldura e rodapé de origem."""
    legend_columns = max(1, min(len(series), 4))
    if sum(len(name) for name in series) > 80:
        legend_columns = min(len(series), 2)
    legend_rows = -(-len(series) // legend_columns) if len(series) > 1 else 0
    style = {"fontsize": 15, "family": family, "color": colors["black"], "weight": "bold"}
    if horizontal:
        # Nomes longos empurram o eixo para a direita; o título fica na margem da figura.
        figure.suptitle(title, x=0.012, y=0.965, ha="left", va="top", **style)
        axis.set_xlabel(unit, family=family, fontsize=11)
    else:
        axis.set_title(title, loc="left", pad=14 + 22 * legend_rows, **style)
        # Unidade longa em até duas linhas, sem sair da figura.
        label = "\n".join(textwrap.wrap(unit, 40)[:2]) if len(unit) > 40 else unit
        axis.set_ylabel(label, family=family, fontsize=11)
    axis.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(colors["line"])
    axis.tick_params(length=0)
    axis.tick_params(axis="x" if horizontal else "y", labelsize=11)
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
        for text in legend.get_texts():
            text.set_family(family)
    for tick in (*axis.get_xticklabels(), *axis.get_yticklabels()):
        tick.set_family(family)
    figure.text(
        0.01,
        0.012,
        f"{nature(result.source)} | {result.department} | "
        f"{result.filters.first_period} a {result.filters.last_period}",
        family=family,
        color=colors["black"],
        fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.04, 1, 1))


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
            # O PDF mostra um painel por página; o PNG avulso traz todos empilhados.
            PANELS_KEY: str(chart_panels(figure)),
        },
    )
    return stream.getvalue()
