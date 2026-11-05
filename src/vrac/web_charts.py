"""Apresentação web local; usa as tabelas calculadas sem filtrar seus resultados."""

from __future__ import annotations

import importlib
import json
import threading
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import altair as alt

from vrac.analyses.academic import CalculatedAnalysis, ChartSpec, chart_unit
from vrac.branding import Branding
from vrac.indicators import INDICATORS, indicator_label

BAR_THICKNESS = 18
# Rótulos de categoria acompanham a largura do cartão, sem depender do tamanho da tela.
LABEL_LIMIT = {"expr": "max(90, min(250, containerSize()[0] * 0.36))"}
MONTHS = "['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']"


def warm_up() -> None:
    """Importa o Altair em segundo plano, para o primeiro cálculo não esperar por ele."""
    threading.Thread(target=importlib.import_module, args=("altair",), daemon=True).start()


def _number_label(value: int | float | None) -> str:
    """Texto do tooltip em português; o valor numérico continua intacto."""
    if value is None:
        return "ausente"
    text = f"{value:,.2f}".rstrip("0").rstrip(".")
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def chart_records(result: CalculatedAnalysis, spec: ChartSpec) -> list[dict]:
    """Formato longo, preservando zero e nulo e sem agregar séries sobrepostas."""
    table = next(t for t in result.tables if t.key == spec.table)
    xi = table.columns.index(spec.x)
    unit = chart_unit(result, spec)
    return [
        {
            "Referência": row[xi],
            "Série": series,
            "Valor": row[table.columns.index(series)],
            "Valor exibido": _number_label(row[table.columns.index(series)]),
            "Unidade": unit,
            "Situação": "ausente" if row[table.columns.index(series)] is None else "observado",
            **(
                {
                    "Semestre": row[table.columns.index("Período")],
                    "Mês": row[table.columns.index("Mês")],
                    "Ordem": spec.series.index(series),
                }
                if spec.table == "monthly_history"
                else {}
            ),
        }
        for row in table.rows
        for series in spec.series
    ]


def _shared_rows(records: list[dict], series: Sequence[str]) -> list[dict]:
    """Uma linha por referência, para ler todas as séries do mesmo ponto no tooltip."""
    rows: dict[object, dict] = {}
    for record in records:
        row = rows.setdefault(
            record["Referência"],
            {
                key: record[key]
                for key in ("Referência", "Unidade", "Semestre", "Mês")
                if key in record
            },
        )
        row[f"serie_{series.index(record['Série'])}"] = record["Valor exibido"]
    return list(rows.values())


def _maximum(records: list[dict]) -> float:
    return max((r["Valor"] for r in records if r["Valor"] is not None), default=0) or 1


def _reference_order(records: list[dict]) -> list | None:
    """Faixas numéricas em ordem de valor, com ausente ao fim; demais mantêm a tabela."""
    references = list(dict.fromkeys(r["Referência"] for r in records))
    absent = [value for value in references if value == "ausente"]
    known = [value for value in references if value != "ausente"]
    try:
        return sorted(known, key=lambda value: float(str(value).replace(",", "."))) + absent
    except ValueError:
        return None


def _indicator_labels() -> str:
    """Símbolos só no rótulo do eixo: os registros do gráfico seguem iguais aos da tabela."""
    labels = {name: indicator_label(name) for name in INDICATORS}
    return f"{json.dumps(labels, ensure_ascii=False)}[datum.label] || datum.label"


def _legend(series: Sequence[str]) -> alt.Legend:
    """Colunas pelo tamanho dos nomes: a legenda quebra em vez de cortar em telas estreitas."""
    import altair as alt

    longest = max(len(name) for name in series)
    columns = 1 if longest > 28 else min(len(series), 2 if longest > 16 else 4)
    return alt.Legend(title=None, columns=columns, labelLimit=320 if columns == 1 else 190)


def _text_on(fill: str) -> str:
    """Preto ou branco pela luminância da barra; o texto nunca usa a cor da série."""
    red, green, blue = (int(fill[index : index + 2], 16) for index in (1, 3, 5))
    return "#000000" if 0.299 * red + 0.587 * green + 0.114 * blue > 150 else "#FFFFFF"


def _theme(chart: alt.Chart, branding: Branding) -> alt.Chart:
    import altair as alt

    colors = branding.tokens["colors"]
    family = branding.tokens["typography"]["body_family"]
    return (
        chart.properties(
            width="container",
            autosize=alt.AutoSizeParams(type="fit-x", contains="padding", resize=True),
        )
        .configure(background=colors["white"], font=family)
        .configure_view(stroke=None)
        .configure_axis(
            labelFont=family,
            titleFont=family,
            labelColor=colors["ink_soft"],
            titleColor=colors["ink_soft"],
            gridColor=colors["line"],
            gridOpacity=0.55,
            gridWidth=1,
            labelFontSize=12,
            titleFontSize=12,
            titleFontWeight=400,
            titleLimit=220,
            titleLineHeight=15,
            titlePadding=10,
            labelPadding=6,
            domain=False,
            ticks=False,
        )
        .configure_legend(
            labelFont=family,
            titleFont=family,
            labelColor=colors["black"],
            orient="top",
            labelFontSize=12,
            symbolSize=120,
            symbolStrokeWidth=2.5,
            rowPadding=6,
            columnPadding=14,
            padding=6,
        )
    )


def _crosshair(
    shared: list[dict],
    series: Sequence[str],
    x: alt.X,
    branding: Branding,
    *,
    height: int,
    extra_tooltip: Sequence[alt.Tooltip] = (),
) -> tuple[alt.Parameter, alt.Chart, alt.Chart]:
    """Linha-guia e faixas transparentes: cada referência mostra todas as séries juntas."""
    import altair as alt

    focus = alt.selection_point(
        fields=["Referência"], on="pointerover", clear="pointerout", empty=False
    )
    tooltip = [
        *extra_tooltip,
        *(
            alt.Tooltip(f"serie_{index}:N", title=name if len(series) > 1 else "Valor")
            for index, name in enumerate(series)
        ),
        alt.Tooltip("Unidade:N"),
    ]
    data = alt.Data(values=shared)
    guide = (
        alt.Chart(data)
        .mark_rule(color=branding.tokens["colors"]["ink_soft"], strokeWidth=1)
        .encode(x=x, opacity=alt.condition(focus, alt.value(0.6), alt.value(0)))
    )
    # Transparente, e não opacidade zero: a faixa precisa continuar recebendo o cursor.
    catcher = (
        alt.Chart(data)
        .mark_bar(color="transparent", width={"band": 1})
        .encode(x=x, y=alt.value(0), y2=alt.value(height), tooltip=tooltip)
        .add_params(focus)
    )
    return focus, guide, catcher


def interactive_chart(result: CalculatedAnalysis, spec: ChartSpec, branding: Branding) -> alt.Chart:
    import altair as alt

    records = chart_records(result, spec)
    if spec.table == "monthly_history":
        return _monthly_chart(records, spec, branding)
    colors = branding.tokens["colors"]
    data = alt.Data(values=records)
    selection = alt.selection_point(fields=["Série"], bind="legend")
    several = len(spec.series) > 1
    base = (
        alt.Chart(data)
        .encode(
            color=alt.Color(
                "Série:N",
                scale=alt.Scale(domain=list(spec.series), range=list(branding.series)),
                legend=_legend(spec.series) if several else None,
            ),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.18)),
            tooltip=[
                alt.Tooltip("Referência:N", title=spec.x),
                alt.Tooltip("Série:N"),
                alt.Tooltip("Valor exibido:N", title="Valor"),
                alt.Tooltip("Unidade:N"),
                alt.Tooltip("Situação:N"),
            ],
        )
        .add_params(selection)
    )
    if spec.kind in {"bar", "grouped_bar"}:
        rows = len({record["Referência"] for record in records})
        offset = {"yOffset": alt.YOffset("Série:N", sort=list(spec.series))} if several else {}
        position = {
            "y": alt.Y(
                "Referência:N",
                title=None,
                sort=_reference_order(records),
                axis=alt.Axis(
                    labelLimit=LABEL_LIMIT,
                    **({"labelExpr": _indicator_labels()} if spec.table == "indicators" else {}),
                ),
            ),
            "x": alt.X(
                "Valor:Q",
                title=None,
                stack=None,
                scale=alt.Scale(zero=True, domainMax=_maximum(records) * 1.18),
                axis=alt.Axis(labels=False, grid=False),
            ),
            **offset,
        }
        # Sem invalid="show", a categoria nula some do eixo e parece não existir. Assim ela
        # fica no lugar, sem barra e com o texto ausente; o dado continua nulo.
        bars = base.mark_bar(
            cornerRadiusEnd=4,
            invalid="show",
            **({} if several else {"size": BAR_THICKNESS}),
        ).encode(**position)
        labels = base.mark_text(
            align="left", dx=6, color=colors["black"], fontSize=12, invalid="show"
        ).encode(**position, text="Valor exibido:N", color=alt.value(colors["black"]))
        height = max(40, rows * (len(spec.series) * 20 + 14))
        return _theme((bars + labels).properties(height=height), branding)
    x = alt.X(
        "Referência:O",
        title=spec.x,
        sort=None,
        axis=alt.Axis(labelAngle=0, labelOverlap="greedy", labelLimit=90, grid=False),
    )
    y = alt.Y(
        "Valor:Q",
        title="Presenças por quadro" if spec.kind == "stacked_bar" else None,
        stack="zero" if spec.kind == "stacked_bar" else None,
        scale=alt.Scale(zero=True),
        axis=alt.Axis(tickCount=5),
    )
    if spec.kind == "stacked_bar":
        chart = base.mark_bar(size=28, stroke=colors["white"], strokeWidth=1.5).encode(x=x, y=y)
        return _theme(chart.properties(height=300), branding)
    # Nulos interrompem a curva; nunca são convertidos em zeros ou interpolados.
    line = base.mark_line(
        point=alt.OverlayMarkDef(filled=True, size=70, stroke=colors["white"], strokeWidth=1.5),
        strokeWidth=2,
        strokeCap="round",
        strokeJoin="round",
        invalid="break-paths-show-domains",
    ).encode(x=x, y=y, strokeDash=alt.StrokeDash("Série:N", legend=None))
    focus, guide, catcher = _crosshair(
        _shared_rows(records, spec.series),
        spec.series,
        x,
        branding,
        height=300,
        extra_tooltip=(alt.Tooltip("Referência:N", title=spec.x),),
    )
    dots = base.mark_point(filled=True, size=120, stroke=colors["white"], strokeWidth=2).encode(
        x=x, y=y, opacity=alt.condition(focus, alt.value(1), alt.value(0))
    )
    return _theme(alt.layer(line, guide, dots, catcher).properties(height=300), branding)


def interactive_bars(
    items: Sequence[tuple[str, int]],
    *,
    label: str,
    unit: str,
    branding: Branding,
    orientation: str = "horizontal",
    color: str = "blue",
    keep_order: bool = False,
) -> alt.Chart:
    import altair as alt

    selection = alt.selection_point(fields=["Categoria"], on="click", clear="dblclick")
    hover = alt.selection_point(
        fields=["Categoria"], on="pointerover", clear="pointerout", empty=False
    )
    if orientation not in {"horizontal", "vertical"}:
        raise ValueError("Orientação de gráfico inválida.")
    colors = branding.tokens["colors"]
    largest = max((v for _, v in items), default=1) or 1
    base = (
        alt.Chart(
            alt.Data(
                values=[
                    {
                        "Categoria": category,
                        "Valor": value,
                        "Valor exibido": _number_label(value),
                        "Unidade": unit,
                    }
                    for category, value in items
                ]
            )
        )
        .encode(
            opacity=alt.condition(selection, alt.value(1), alt.value(0.18)),
            tooltip=[
                alt.Tooltip("Categoria:N", title=label),
                alt.Tooltip("Valor exibido:N", title="Valor"),
                "Unidade:N",
            ],
        )
        .add_params(selection)
    )
    if orientation == "vertical":
        base = base.encode(
            x=alt.X(
                "Categoria:N",
                title=None,
                sort="-y",
                axis=alt.Axis(labelAngle=0, labelLimit=110, labelOverlap="greedy"),
            ),
            y=alt.Y(
                "Valor:Q",
                title=None,
                scale=alt.Scale(zero=True, domainMax=largest * 1.15),
                axis=alt.Axis(labels=False, grid=False),
            ),
        )
        labels = base.mark_text(dy=-9, color=colors["black"], fontSize=12).encode(
            text="Valor exibido:N"
        )
        height = 240
    else:
        base = base.encode(
            y=alt.Y(
                "Categoria:N",
                title=None,
                sort=[category for category, _ in items] if keep_order else "-x",
                axis=alt.Axis(labelLimit=LABEL_LIMIT),
            ),
            x=alt.X(
                "Valor:Q",
                title=None,
                scale=alt.Scale(zero=True, domainMax=largest * 1.18),
                axis=alt.Axis(labels=False, grid=False),
            ),
        )
        labels = base.mark_text(align="left", dx=6, color=colors["black"], fontSize=12).encode(
            text="Valor exibido:N"
        )
        height = max(60, 34 * len(items))
    bars = (
        base.mark_bar(color=colors[color], cornerRadiusEnd=4, size=BAR_THICKNESS, cursor="pointer")
        .encode(
            stroke=alt.condition(hover, alt.value(colors["black"]), alt.value(None)),
            strokeWidth=alt.value(1.5),
        )
        .add_params(hover)
    )
    chart = (bars + labels).properties(height=height, padding={"top": 8, "right": 12})
    return _theme(chart, branding)


def _monthly_chart(records: list[dict], spec: ChartSpec, branding: Branding) -> alt.Chart:
    """Eixo mensal contínuo com segundo nível semestral; sem agregar no visual."""
    import altair as alt

    colors = branding.tokens["colors"]
    selection = alt.selection_point(fields=["Série"], bind="legend")
    stacked = spec.kind == "stacked_bar"
    references = list(dict.fromkeys(r["Referência"] for r in records))
    palette = list(branding.series)
    x = alt.X(
        "Referência:O",
        title=None,
        sort=None,
        scale=alt.Scale(domain=references),
        axis=alt.Axis(
            labelAngle=0,
            labelExpr=f"{MONTHS}[toNumber(split(datum.label, '-')[1]) - 1]",
            labelOverlap="greedy",
            grid=False,
        ),
    )
    y = alt.Y(
        "Valor:Q",
        title="Presenças por quadro" if stacked else "Professores ativos",
        stack="zero" if stacked else None,
        scale=alt.Scale(zero=True),
        axis=alt.Axis(tickMinStep=1, tickCount=5),
    )
    base = alt.Chart(alt.Data(values=records)).encode(
        x=x,
        y=y,
        color=alt.Color(
            "Série:N",
            title="Quadro" if stacked else None,
            scale=alt.Scale(domain=list(spec.series), range=palette if stacked else palette[:1]),
            legend=_legend(spec.series) if stacked else None,
        ),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.18))
        if stacked
        else alt.value(1),
        order=alt.Order("Ordem:Q", sort="ascending"),
        tooltip=[
            "Semestre:N",
            "Mês:O",
            "Série:N",
            alt.Tooltip("Valor exibido:N", title="Valor"),
            "Unidade:N",
            "Situação:N",
        ],
    )
    fits = f"width / {max(1, len(references))} >= 44"
    extras: list[alt.Chart] = []
    if stacked:
        marks = base.mark_bar(stroke=colors["white"], strokeWidth=1).add_params(selection)
        # Cada segmento recebe o próprio valor; a pilha não é um total distinto.
        positions = []
        tallest = 0
        for reference in references:
            bottom = 0
            for record in (r for r in records if r["Referência"] == reference):
                value = record["Valor"]
                if value is not None:
                    if value:
                        fill = palette[record["Ordem"] % len(palette)]
                        positions.append(
                            {**record, "Posição": bottom + value / 2, "Tinta": _text_on(fill)}
                        )
                    bottom += value
            tallest = max(tallest, bottom)
        # Rótulo só quando o segmento comporta o texto; o tooltip e a tabela têm todos.
        labels = (
            alt.Chart(alt.Data(values=positions))
            .mark_text(fontWeight=600)
            .encode(
                x=alt.X("Referência:O", sort=None),
                y=alt.Y("Posição:Q"),
                text=alt.Text("Valor:Q", format="d"),
                color=alt.Color("Tinta:N", scale=None),
                opacity=alt.condition(selection, alt.value(1), alt.value(0.18)),
                size=alt.condition(
                    f"{fits} && datum.Valor >= {tallest * 0.09}", alt.value(11), alt.value(0)
                ),
            )
        )
    else:
        marks = base.mark_line(
            point=alt.OverlayMarkDef(filled=True, size=46, stroke=colors["white"], strokeWidth=1),
            strokeWidth=2,
            strokeCap="round",
            strokeJoin="round",
            invalid="break-paths-show-domains",
        )
        # Rótulos seletivos: início, fim e extremos; o restante aparece na linha-guia.
        observed = [r for r in records if r["Valor"] is not None]
        highlights = (
            [
                observed[0],
                observed[-1],
                max(observed, key=lambda r: r["Valor"]),
                min(observed, key=lambda r: r["Valor"]),
            ]
            if observed
            else []
        )
        unique = list({r["Referência"]: r for r in highlights}.values())
        labels = (
            alt.Chart(alt.Data(values=unique))
            .mark_text(dy=-13, fontWeight=600, fontSize=12, color=colors["black"])
            .encode(x=x, y=y, text=alt.Text("Valor:Q"))
        )
        area = base.mark_area(opacity=0.1, invalid="break-paths-show-domains").encode(
            opacity=alt.value(0.1), tooltip=alt.value(None)
        )
        focus, guide, catcher = _crosshair(
            _shared_rows(records, spec.series),
            spec.series,
            x,
            branding,
            height=280,
            extra_tooltip=(alt.Tooltip("Semestre:N"), alt.Tooltip("Mês:O")),
        )
        dot = base.mark_point(filled=True, size=120, stroke=colors["white"], strokeWidth=2).encode(
            opacity=alt.condition(focus, alt.value(1), alt.value(0))
        )
        extras = [area, guide, dot, catcher]
    semester_labels = []
    for semester in dict.fromkeys(r["Semestre"] for r in records):
        months = list(dict.fromkeys(r["Referência"] for r in records if r["Semestre"] == semester))
        semester_labels.append({"Referência": months[len(months) // 2], "Semestre": semester})
    semesters = (
        alt.Chart(alt.Data(values=semester_labels))
        .mark_text(dy=37, color=colors["black"], fontWeight=600)
        .encode(
            x=alt.X("Referência:O", sort=None),
            y=alt.value(280),
            text="Semestre:N",
            size=alt.condition(
                f"width / {max(1, len(semester_labels))} >= 38", alt.value(12), alt.value(0)
            ),
        )
    )
    chart = alt.layer(marks, labels, *extras, semesters).properties(
        height=280, padding={"bottom": 45, "top": 20}
    )
    return _theme(chart, branding)
