"""Séries mensais docentes: identidade, calendário, filtros e cobertura offline."""

from dataclasses import replace
from datetime import UTC, date, datetime

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_data import HistoryRow
from vrac.analyses.academic_export import table_csv
from vrac.analyses.academic_fixture import load_fixture

FILTERS = AnalysisFilters("2026.1", "2026.2", "2026.2")


def _table(result, key):
    return next(table for table in result.tables if table.key == key)


def _source():
    first = HistoryRow(
        "SINT-A", "P1", "V1", date(2026, 1, 1), "PROF PRINCIPAL", "C1", "A", "3", None
    )
    return replace(
        load_fixture("SINT-A"),
        history=(
            first,
            first,
            replace(first, registration="V2", payroll_batch="4"),
            replace(first, registration="V3", cadre="PROF HORISTA"),
            replace(first, person_key="P2", registration="V4", category="C2"),
            replace(first, reference_date=date(2026, 2, 1), status="I"),
            replace(first, reference_date=date(2026, 7, 1)),
            replace(first, reference_date=date(2026, 8, 1)),
            replace(first, reference_date=date(2026, 12, 1), person_key=None),
        ),
    )


def test_monthly_distinct_people_do_not_sum_lots_contracts_or_cadres():
    result = calculate(AnalysisKind.HISTORY, _source(), FILTERS)
    monthly = _table(result, "monthly_history")
    assert monthly.columns == (
        "Período",
        "Competência",
        "Mês",
        "Total",
        "PROF HORISTA",
        "PROF PRINCIPAL",
    )
    assert len(monthly.rows) == 12
    assert monthly.rows[0] == ("2026.1", "2026-01", 1, 2, 1, 2)
    assert monthly.rows[6] == ("2026.1", "2026-07", 7, 1, 0, 1)
    assert monthly.rows[7] == ("2026.2", "2026-08", 8, 1, 0, 1)
    semester = _table(result, "history")
    assert semester.rows[0][1] == 2
    assert sum(row[3] or 0 for row in monthly.rows[:7]) == 3
    assert monthly.rows[0][4] + monthly.rows[0][5] > monthly.rows[0][3]
    assert [chart.table for chart in result.charts[:2]] == ["monthly_history"] * 2
    assert result.charts[0].series == ("Total",)
    assert "Total" not in result.charts[1].series


def test_monthly_missing_observation_and_observed_zero_remain_distinct_in_csv():
    result = calculate(AnalysisKind.HISTORY, _source(), FILTERS)
    table = _table(result, "monthly_history")
    assert table.rows[1] == ("2026.1", "2026-02", 2, 0, 0, 0)
    assert table.rows[2] == ("2026.1", "2026-03", 3, None, None, None)
    assert table.rows[-1] == ("2026.2", "2026-12", 12, 0, 0, 0)
    assert result.status == "Parcial"
    exported = table_csv(result, table, datetime(2026, 11, 3, tzinfo=UTC)).decode("utf-8-sig")
    assert "2026.1;2026-02;2;0;0;0" in exported
    assert "2026.1;2026-03;3;ausente;ausente;ausente" in exported


def test_cadre_selects_monthly_series_and_category_filters_population():
    full = calculate(AnalysisKind.HISTORY, _source(), FILTERS)
    selected = calculate(
        AnalysisKind.HISTORY, _source(), replace(FILTERS, cadres=("PROF HORISTA",))
    )
    selected_table = _table(selected, "monthly_history")
    assert selected_table.columns == ("Período", "Competência", "Mês", "Total", "PROF HORISTA")
    assert [row[3] for row in selected_table.rows] == [
        row[3] for row in _table(full, "monthly_history").rows
    ]
    assert selected_table.rows[6][3:] == (1, 0)
    category = calculate(AnalysisKind.HISTORY, _source(), replace(FILTERS, categories=("C2",)))
    category_table = _table(category, "monthly_history")
    assert category_table.rows[0][3:] == (1, 1)
    assert category_table.rows[6][3:] == (0, 0)
    assert category_table.rows[2][3:] == (None, None)


def test_no_history_preserves_all_missing_competencies_and_semester_absence():
    result = calculate(AnalysisKind.HISTORY, replace(_source(), history=()), FILTERS)
    table = _table(result, "monthly_history")
    assert result.status == "Sem dados"
    assert len(table.rows) == 12
    assert all(row[3] is None for row in table.rows)
    assert all(row[1] is None for row in _table(result, "history").rows)
