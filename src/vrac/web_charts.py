"""Apresentação web local; usa as tabelas calculadas sem filtrar seus resultados."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import altair as alt

from vrac.analyses.academic import CalculatedAnalysis, ChartSpec
from vrac.branding import Branding


def chart_records(result: CalculatedAnalysis, spec: ChartSpec) -> list[dict]:
    """Formato longo, preservando zero e nulo e sem agregar séries sobrepostas."""
    table = next(t for t in result.tables if t.key == spec.table)
    xi = table.columns.index(spec.x)
    unit = (
        "matrículas funcionais distintas"
        if result.kind == "R02" and spec.table == "departments"
        else table.unit
    )
    return [
        {
            "Referência": row[xi],
            "Série": series,
            "Valor": row[table.columns.index(series)],
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


def _theme(chart: alt.Chart, branding: Branding) -> alt.Chart:
    colors = branding.tokens["colors"]
    family = branding.tokens["typography"]["body_family"]
    return (
        chart.properties(width="container")
        .configure(background=colors["white"], font=family)
        .configure_view(stroke=None)
        .configure_axis(
            labelFont=family,
            titleFont=family,
            labelColor=colors["black"],
            titleColor=colors["black"],
            gridColor=colors["gray"],
            gridOpacity=0.25,
            labelFontSize=12,
            titleFontSize=12,
            titleLimit=180,
        )
        .configure_legend(
            labelFont=family,
            titleFont=family,
            labelColor=colors["black"],
            titleColor=colors["black"],
            orient="bottom",
            columns=1,
            labelLimit=260,
        )
    )


def interactive_chart(result: CalculatedAnalysis, spec: ChartSpec, branding: Branding) -> alt.Chart:
    import altair as alt

    records = chart_records(result, spec)
    if spec.table == "monthly_history":
        return _monthly_chart(records, spec, branding)
    colors = branding.tokens["colors"]
    palette = [colors[k] for k in ("blue", "cyan", "yellow", "gray", "black")]
    data = alt.Data(values=records)
    selection = alt.selection_point(fields=["Série"], bind="legend")
    base = (
        alt.Chart(data)
        .encode(
            color=alt.Color("Série:N", scale=alt.Scale(domain=list(spec.series), range=palette)),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.18)),
            tooltip=[
                alt.Tooltip("Referência:N", title=spec.x),
                alt.Tooltip("Série:N"),
                alt.Tooltip("Valor:Q", format=",.2~f"),
                alt.Tooltip("Unidade:N"),
                alt.Tooltip("Situação:N"),
            ],
        )
        .add_params(selection)
    )
    if spec.kind in {"bar", "grouped_bar"}:
        chart = (
            base.mark_bar()
            .encode(
                y=alt.Y("Referência:N", title=None, sort=None, axis=alt.Axis(labelLimit=145)),
                x=alt.X("Valor:Q", title="Quantidade", stack=None),
                yOffset="Série:N",
            )
            .properties(height=max(180, len(records) * 26))
        )
    else:
        encodings = dict(
            x=alt.X(
                "Referência:O",
                title=spec.x,
                sort=None,
                axis=alt.Axis(labelAngle=-45, labelOverlap="greedy"),
            ),
            y=alt.Y(
                "Valor:Q",
                title="Presenças por quadro" if spec.kind == "stacked_bar" else "Quantidade",
                stack="zero" if spec.kind == "stacked_bar" else None,
            ),
        )
        if spec.kind == "stacked_bar":
            chart = base.mark_bar().encode(**encodings)
        else:
            # Nulos interrompem a curva; nunca são convertidos em zeros ou interpolados.
            chart = base.mark_line(point=True, invalid="break-paths-show-domains").encode(
                **encodings, strokeDash="Série:N"
            )
        chart = chart.properties(height=300)
    return _theme(chart, branding)


def interactive_bars(
    items: Sequence[tuple[str, int]],
    *,
    label: str,
    unit: str,
    branding: Branding,
    orientation: str = "horizontal",
    color: str = "blue",
) -> alt.Chart:
    import altair as alt

    selection = alt.selection_point(fields=["Categoria"], on="click", clear="dblclick")
    if orientation not in {"horizontal", "vertical"}:
        raise ValueError("Orientação de gráfico inválida.")
    base = (
        alt.Chart(
            alt.Data(
                values=[
                    {"Categoria": category, "Valor": value, "Unidade": unit}
                    for category, value in items
                ]
            )
        )
        .encode(
            opacity=alt.condition(selection, alt.value(1), alt.value(0.18)),
            tooltip=[alt.Tooltip("Categoria:N", title=label), alt.Tooltip("Valor:Q"), "Unidade:N"],
        )
        .add_params(selection)
    )
    if orientation == "vertical":
        base = base.encode(
            x=alt.X(
                "Categoria:N", title=None, sort=None, axis=alt.Axis(labelAngle=0, labelLimit=170)
            ),
            y=alt.Y(
                "Valor:Q",
                title="Quantidade",
                scale=alt.Scale(zero=True),
                axis=alt.Axis(tickMinStep=1),
            ),
        )
        labels = base.mark_text(dy=-10, color=branding.tokens["colors"]["black"]).encode(
            text=alt.Text("Valor:Q", format="d")
        )
        height = 240
    else:
        base = base.encode(
            y=alt.Y("Categoria:N", title=None, sort=None, axis=alt.Axis(labelLimit=310)),
            x=alt.X(
                "Valor:Q",
                title="Quantidade",
                scale=alt.Scale(zero=True),
                axis=alt.Axis(tickMinStep=1),
            ),
        )
        labels = base.mark_text(
            align="left", dx=7, color=branding.tokens["colors"]["black"]
        ).encode(text=alt.Text("Valor:Q", format="d"))
        height = max(170, 32 * len(items))
    chart = (base.mark_bar(color=branding.tokens["colors"][color]) + labels).properties(
        height=height
    )
    return _theme(chart, branding)


def _monthly_chart(records: list[dict], spec: ChartSpec, branding: Branding) -> alt.Chart:
    """Eixo mensal contínuo com segundo nível semestral; sem agregar no visual."""
    import altair as alt

    colors = branding.tokens["colors"]
    selection = alt.selection_point(fields=["Série"], bind="legend")
    stacked = spec.kind == "stacked_bar"
    references = list(dict.fromkeys(r["Referência"] for r in records))
    base = alt.Chart(alt.Data(values=records)).encode(
        x=alt.X(
            "Referência:O",
            title=None,
            sort=None,
            scale=alt.Scale(domain=references),
            axis=alt.Axis(
                labelAngle=0, labelExpr="toNumber(split(datum.label, '-')[1])", labelOverlap=False
            ),
        ),
        y=alt.Y(
            "Valor:Q",
            title="Presenças por quadro" if stacked else "Professores ativos",
            stack="zero" if stacked else None,
            axis=alt.Axis(tickMinStep=1),
        ),
        color=alt.Color(
            "Série:N",
            title="Quadro" if stacked else None,
            scale=alt.Scale(
                domain=list(spec.series),
                range=[
                    colors[k]
                    for k in (
                        ("blue", "cyan", "yellow", "gray", "black") if stacked else ("yellow",)
                    )
                ],
            ),
            legend=alt.Legend() if stacked else None,
        ),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.18))
        if stacked
        else alt.value(1),
        order=alt.Order("Ordem:Q", sort="ascending"),
        tooltip=[
            "Semestre:N",
            "Mês:O",
            "Série:N",
            alt.Tooltip("Valor:Q", format="d"),
            "Unidade:N",
            "Situação:N",
        ],
    )
    if stacked:
        marks = base.mark_bar().add_params(selection)
        # Cada segmento recebe o próprio valor; a pilha não é um total distinto.
        positions = []
        for reference in dict.fromkeys(r["Referência"] for r in records):
            bottom = 0
            for record in (r for r in records if r["Referência"] == reference):
                value = record["Valor"]
                if value is not None:
                    if value:
                        positions.append({**record, "Posição": bottom + value / 2})
                    bottom += value
        labels = (
            alt.Chart(alt.Data(values=positions))
            .mark_text(color=colors["black"], fontSize=11)
            .encode(x=alt.X("Referência:O", sort=None), y=alt.Y("Posição:Q"), text="Valor:Q")
        )
    else:
        marks = base.mark_line(point=True, invalid="break-paths-show-domains")
        labels = base.mark_text(dy=-12).encode(text="Valor:Q", color=alt.value(colors["black"]))
    semester_labels = []
    for semester in dict.fromkeys(r["Semestre"] for r in records):
        references = list(
            dict.fromkeys(r["Referência"] for r in records if r["Semestre"] == semester)
        )
        semester_labels.append(
            {"Referência": references[len(references) // 2], "Semestre": semester}
        )
    semesters = (
        alt.Chart(alt.Data(values=semester_labels))
        .mark_text(dy=37, color=colors["black"])
        .encode(x=alt.X("Referência:O", sort=None), y=alt.value(280), text="Semestre:N")
    )
    chart = (marks + labels + semesters).properties(height=280, padding={"bottom": 45, "top": 20})
    return _theme(chart, branding)
