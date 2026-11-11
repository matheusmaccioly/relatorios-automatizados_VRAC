"""Fechamento docente: conciliação offline, sem números das capturas ou banco."""

import csv
import io
import json
from dataclasses import replace
from datetime import UTC, date, datetime
from zipfile import ZipFile

import pytest
from matplotlib import pyplot as plt

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_data import ALL_DEPARTMENTS, HistoryRow
from vrac.analyses.academic_export import report_zip, table_csv
from vrac.analyses.academic_fixture import load_fixture
from vrac.analyses.export import summary_csv
from vrac.analyses.faculty_overview import OverviewFilters, OverviewStatus, compute_overview
from vrac.branding import load_branding
from vrac.charts import academic_chart
from vrac.web_charts import chart_records, interactive_bars, interactive_chart

FILTERS = AnalysisFilters("2026.1", "2026.1", "2026.1", group_a_cadres=("PROF PRINCIPAL",))
NOW = datetime(2026, 11, 3, 12, tzinfo=UTC)


def table(result, key):
    return next(t for t in result.tables if t.key == key)


def comparison_source():
    source = load_fixture(ALL_DEPARTMENTS)
    base = source.faculty.register[0]
    a = replace(base, department="SINT-A", registration="V1", person_key="P1")
    b = replace(a, registration="V2", cadre="PROF HORISTA")  # dois vínculos da pessoa
    c = replace(a, department="SINT-B", registration="V3", person_key="P2")
    d = replace(c, registration="V4", person_key="P3", cadre=None)
    return replace(source, faculty=replace(source.faculty, register=(a, a, b, c, d)))


def test_current_units_and_department_comparison_agree_with_exports():
    source = comparison_source()
    overview = compute_overview(source.faculty, OverviewFilters())
    # V4 tem quadro vazio e sai pelo filtro de página do painel.
    assert overview.total == 3
    assert dict(overview.by_department) == {"SINT-A": 3, "SINT-B": 1}  # linhas do visual
    assert sum(n for _, n in overview.by_category) == 4
    exported = list(
        csv.reader(io.StringIO(summary_csv(overview, NOW).decode("utf-8-sig")), delimiter=";")
    )
    assert ["Resultado", "Total", "3"] in exported
    assert ["Por departamento", "SINT-A", "3"] in exported
    assert overview.fingerprint in str(exported)
    result = calculate(AnalysisKind.COMPARISON, source, FILTERS)
    expected = (("SINT-A", 1, 2, 1, 50), ("SINT-B", 1, 1, 1, 100))
    assert table(result, "departments").rows == expected
    assert result.metrics[0].value == 2 and result.metrics[1].value == 3
    changed = calculate(
        AnalysisKind.COMPARISON,
        source,
        replace(FILTERS, group_a_cadres=("PROF HORISTA",), cadres=("PROF HORISTA",)),
    )
    assert changed.metrics[0].value == 1 and changed.metrics[1].value == 3
    assert [r[1] for r in table(changed, "departments").rows] == [1, 0]
    text = table_csv(result, table(result, "departments"), NOW).decode("utf-8-sig")
    assert "SINT-A;1;2;1;50" in text and "SINT-B;1;1;1;100" in text
    with ZipFile(io.BytesIO(report_zip((result,), NOW))) as archive:
        assert archive.read("R02/departments.csv").decode("utf-8-sig") == text


def test_same_selection_is_full_share_and_department_overlap_is_not_a_total():
    source = comparison_source()
    repeated = replace(source.faculty.register[0], department="SINT-B")
    source = replace(
        source, faculty=replace(source.faculty, register=(*source.faculty.register, repeated))
    )
    result = calculate(AnalysisKind.COMPARISON, source, replace(FILTERS, group_a_cadres=()))
    metrics = {m.label: m.value for m in result.metrics}
    assert metrics["QP"] == metrics["Geral"] == 3 and metrics["QP em % de Geral"] == 100
    # V1 está nos dois departamentos: as linhas não somam o total do recorte.
    assert sum(r[2] for r in table(result, "departments").rows) == 4
    assert table(result, "groups").rows[0][1] == "todos os quadros"
    assert result.charts[0].series == ("QP", "Geral")


def test_history_complete_and_partial_coverage_with_overlapping_cadres():
    source = load_fixture("SINT-A")
    rows = tuple(
        HistoryRow("SINT-A", "P1", "V1", date(2026, m, 1), "PROF PRINCIPAL", "C", "A", "3", None)
        for m in range(1, 8)
    )
    second = replace(rows[-1], cadre="PROF HORISTA", registration="V2", payroll_batch="4")
    source = replace(source, history=(*rows, rows[0], second))
    result = calculate(AnalysisKind.HISTORY, source, FILTERS)
    assert result.status == "Calculado"
    assert table(result, "history").rows == (("2026.1", 1, 1, 1),)
    assert sum(r[2] for r in table(result, "monthly").rows) == 7
    stacked = next(c for c in result.charts if c.kind == "stacked_bar" and c.table == "history")
    assert "Total" not in stacked.series
    assert sum(r["Valor"] for r in chart_records(result, stacked)) == 2
    partial = calculate(AnalysisKind.HISTORY, replace(source, history=rows[1:]), FILTERS)
    assert partial.status == "Parcial"
    assert table(partial, "coverage").rows[0][2:] == (6, 7)
    missing = calculate(AnalysisKind.HISTORY, replace(source, history=()), FILTERS)
    assert missing.status == "Sem dados" and table(missing, "history").rows[0][1] is None


def test_hours_unavailable_does_not_remove_composition_or_become_null_source_value():
    source = load_fixture("SINT-A").faculty
    # Quadro vazio sai pelo filtro de página; com quadro, o vínculo sem horas permanece.
    source = replace(
        source, register=tuple(replace(r, cadre=r.cadre or "PROF QCI") for r in source.register)
    )
    normal = compute_overview(source, OverviewFilters())
    states = {d.hours_state for d in normal.detail}
    assert states == {"Valor informado", "Nulo na fonte", "Sem registro"}
    unavailable = compute_overview(replace(source, real_hours_available=False), OverviewFilters())
    assert unavailable.total == normal.total
    assert unavailable.status == OverviewStatus.PARTIAL
    assert all(
        d.real_hours is None and d.hours_state == "Fonte indisponível" for d in unavailable.detail
    )
    assert unavailable.fingerprint != normal.fingerprint
    assert "Fonte de Horas Reais indisponível" in summary_csv(unavailable, NOW).decode("utf-8-sig")


@pytest.mark.parametrize(
    "kind", [AnalysisKind.QP, AnalysisKind.HISTORY, AnalysisKind.WORKLOAD, AnalysisKind.FUNCTIONS]
)
def test_web_specs_keep_table_values_nulls_units_and_local_only_highlighting(kind):
    result = calculate(
        kind,
        load_fixture(ALL_DEPARTMENTS),
        replace(FILTERS, first_period="2024.1", last_period="2026.2"),
    )
    branding = load_branding()
    for spec in result.charts:
        source_table = table(result, spec.table)
        records = chart_records(result, spec)
        assert [r["Valor"] for r in records] == [
            row[source_table.columns.index(s)] for row in source_table.rows for s in spec.series
        ]
        before = table_csv(result, source_table, NOW)
        serialized = interactive_chart(result, spec, branding).to_dict()
        marks = serialized.get("layer", [serialized])
        assert serialized["width"] == "container"
        assert marks[0]["encoding"]["tooltip"]
        funnel = spec.table in {"real_distribution", "contract_distribution"}
        if not funnel and (spec.table != "monthly_history" or spec.kind == "stacked_bar"):
            assert serialized["params"][0]["bind"] == "legend"
        assert "transform" not in serialized  # nenhum filtro visual reduz a tabela
        source_data = serialized.get("data", marks[0].get("data", {}))
        if funnel:
            assert [
                {k: v for k, v in row.items() if k not in {"left", "right"}}
                for row in source_data["values"]
            ] == sorted(records, key=lambda row: -(row["Valor"] or 0))
            assert "x2" in marks[0]["encoding"]
        else:
            assert source_data["values"] == records
        assert "url" not in source_data
        assert serialized["config"]["font"] == "Rethink Sans"
        assert before == table_csv(result, source_table, NOW)
        json.dumps(serialized, allow_nan=False)


def test_single_series_chart_preserves_zero_and_uses_click_highlighting():
    spec = interactive_bars(
        (("Ausente", 0), ("Quadro de nome longo", 2)),
        label="Quadro",
        unit="matrículas funcionais distintas",
        branding=load_branding(),
    ).to_dict()
    assert spec["data"]["values"][0]["Valor"] == 0
    assert spec["params"][0]["select"]["clear"] == "dblclick"
    assert "transform" not in spec


def test_comparison_department_chart_uses_count_unit_in_png_and_web():
    result = calculate(AnalysisKind.COMPARISON, comparison_source(), FILTERS)
    spec = next(chart for chart in result.charts if chart.table == "departments")
    assert "%" in table(result, "departments").unit
    unit = "professores (matrículas funcionais distintas)"
    assert {row["Unidade"] for row in chart_records(result, spec)} == {unit}
    figure = academic_chart(result, spec, load_branding())
    try:
        assert figure.axes[0].get_ylabel() == unit
    finally:
        plt.close(figure)
