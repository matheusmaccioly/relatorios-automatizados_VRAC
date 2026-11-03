"""Coerência offline entre tabelas mensais, gráficos web e arquivos PNG."""

import json
import math
import struct
from dataclasses import replace
from datetime import date

import pytest
from matplotlib import pyplot as plt
from matplotlib.path import Path

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_data import HistoryRow
from vrac.analyses.academic_fixture import load_fixture
from vrac.branding import load_branding
from vrac.charts import academic_chart, figure_png
from vrac.web_charts import chart_records, interactive_chart


def _result():
    first = HistoryRow(
        "SINT-A", "P1", "V1", date(2026, 1, 1), "PROF PRINCIPAL", "C", "A", "3", None
    )
    source = replace(
        load_fixture("SINT-A"),
        history=(
            first,
            first,
            replace(first, registration="V2", cadre="PROF HORISTA"),
            replace(first, reference_date=date(2026, 3, 1), person_key="P2"),
            replace(first, reference_date=date(2026, 7, 1), status="I"),
            replace(first, reference_date=date(2026, 8, 1)),
        ),
    )
    return calculate(AnalysisKind.HISTORY, source, AnalysisFilters("2026.1", "2026.2", "2026.2"))


def _nodes(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from _nodes(item)


@pytest.mark.parametrize("index", [0, 1])
def test_monthly_web_records_preserve_table_values_and_use_local_data(index):
    result = _result()
    spec = result.charts[index]
    table = next(table for table in result.tables if table.key == "monthly_history")
    records = chart_records(result, spec)
    assert [record["Valor"] for record in records] == [
        row[table.columns.index(series)] for row in table.rows for series in spec.series
    ]
    assert {record["Unidade"] for record in records} == {table.unit}
    assert any(record["Valor"] is None and record["Situação"] == "ausente" for record in records)
    assert any(record["Valor"] == 0 and record["Situação"] == "observado" for record in records)
    assert records[0]["Semestre"] == "2026.1" and records[0]["Mês"] == 1
    assert next(record for record in records if record["Mês"] == 8)["Semestre"] == "2026.2"

    branding = load_branding()
    serialized = interactive_chart(result, spec, branding).to_dict()
    json.dumps(serialized, allow_nan=False)
    nodes = list(_nodes(serialized))
    assert any(node.get("data", {}).get("values") == records for node in nodes)
    assert serialized["width"] == "container"
    assert serialized["config"]["font"] == branding.tokens["typography"]["body_family"]
    assert not any("url" in node or "transform" in node for node in nodes)
    references = {node["param"] for node in nodes if "param" in node}
    declared = {param["name"] for node in nodes for param in node.get("params", [])}
    assert references <= declared
    main = serialized["layer"][0]
    assert main["encoding"]["x"]["axis"]["labelExpr"]
    semester_labels = serialized["layer"][-1]["data"]["values"]
    assert [row["Semestre"] for row in semester_labels] == ["2026.1", "2026.2"]
    if spec.kind == "line":
        assert main["mark"]["invalid"] == "break-paths-show-domains"
        assert main["encoding"]["color"]["scale"]["range"] == [branding.tokens["colors"]["yellow"]]
        assert serialized["layer"][1]["encoding"]["text"]["field"] == "Valor"
    else:
        assert main["mark"]["type"] == "bar"
        assert main["encoding"]["y"]["stack"] == "zero"
        labels = serialized["layer"][1]["data"]["values"]
        january = [row for row in labels if row["Referência"] == "2026-01"]
        assert [row["Valor"] for row in january] == [1, 1]
        assert [row["Posição"] for row in january] == [0.5, 1.5]


def test_monthly_png_line_keeps_gaps_values_and_semester_month_labels():
    result = _result()
    branding = load_branding()
    figure = academic_chart(result, result.charts[0], branding)
    try:
        axis = figure.axes[0]
        values = axis.lines[0].get_ydata()
        expected = [1, None, 1, None, None, None, 0, 1, None, None, None, None]
        assert all(
            math.isnan(actual) if value is None else actual == value
            for actual, value in zip(values, expected, strict=True)
        )
        assert axis.lines[0].get_color() == branding.tokens["colors"]["yellow"]
        moves = sum(code == Path.MOVETO for _, code in axis.lines[0].get_path().iter_segments())
        assert moves == 3
        assert [tick.get_text() for tick in axis.get_xticklabels()] == [
            str(month) for month in range(1, 13)
        ]
        texts = [text.get_text() for text in axis.texts]
        assert "2026.1" in texts and "2026.2" in texts and "0" in texts
        png = figure_png(figure)
        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", png[16:24])
        assert width > 1000 and height > 500
    finally:
        plt.close(figure)


def test_monthly_png_stacks_cadres_without_converting_absence_to_zero():
    result = _result()
    table = next(table for table in result.tables if table.key == "monthly_history")
    spec = result.charts[1]
    figure = academic_chart(result, spec, load_branding())
    try:
        axis = figure.axes[0]
        assert len(axis.containers) == len(spec.series)
        for container, series in zip(axis.containers, spec.series, strict=True):
            expected = [row[table.columns.index(series)] for row in table.rows]
            actual = [rectangle.get_height() for rectangle in container.patches]
            assert all(
                math.isnan(height) if value is None else height == value
                for height, value in zip(actual, expected, strict=True)
            )
        assert sum(container.patches[0].get_height() for container in axis.containers) == 2
        assert table.rows[0][table.columns.index("Total")] == 1
        assert figure_png(figure).startswith(b"\x89PNG")
    finally:
        plt.close(figure)
