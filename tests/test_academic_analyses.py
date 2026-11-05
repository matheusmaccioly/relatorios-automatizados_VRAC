"""Cálculos dos roteiros: expectativas independentes com casos analíticos pequenos."""

import io
import json
from dataclasses import replace
from datetime import UTC, date, datetime
from zipfile import ZipFile

import pytest

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate, faculty_period
from vrac.analyses.academic_data import (
    ALL_DEPARTMENTS,
    AppointmentRow,
    HistoryRow,
    ScholarshipRow,
    SimulationPolicy,
    StudentRow,
    WorkloadRow,
)
from vrac.analyses.academic_export import report_zip, table_csv
from vrac.analyses.academic_fixture import load_fixture
from vrac.analyses.academic_quality import inspect_source
from vrac.analyses.export import safe_cell
from vrac.branding import load_branding
from vrac.charts import academic_chart, figure_png

FILTERS = AnalysisFilters("2024.1", "2026.2", "2026.1", qp_cadres=("PROF PRINCIPAL",))
NOW = datetime(2026, 10, 30, 18, 0, tzinfo=UTC)


def table(result, key):
    return next(t for t in result.tables if t.key == key)


def test_every_route_is_available_and_reproducible_in_memory() -> None:
    source = load_fixture(ALL_DEPARTMENTS)
    assert source.fingerprint == load_fixture(ALL_DEPARTMENTS).fingerprint
    for kind in AnalysisKind:
        result = calculate(kind, source, FILTERS)
        assert result == calculate(kind, source, FILTERS)
        assert result.tables and result.status != "Bloqueado"
        assert result.source == "Memória"
        assert result.fingerprint == source.fingerprint


def test_qp_simulation_keeps_general_denominator_and_unknown_classification() -> None:
    source = load_fixture("SINT-A")
    result = calculate(AnalysisKind.QP, source, FILTERS)
    metrics = {m.label: m.value for m in result.metrics}
    assert metrics["Geral"] == 5
    assert metrics["Grupo QP simulado"] == 1
    assert metrics["Classificação ausente"] == 1
    assert metrics["Demais"] is None and metrics["Participação do grupo"] is None
    known = replace(
        source,
        faculty=replace(
            source.faculty, register=tuple(r for r in source.faculty.register if r.cadre)
        ),
    )
    result = calculate(AnalysisKind.QP, known, FILTERS)
    metrics = {m.label: m.value for m in result.metrics}
    assert metrics["Geral"] == 4 and metrics["Grupo QP simulado"] == 1
    assert metrics["Demais"] == 3 and metrics["Participação do grupo"] == 25
    other = calculate(AnalysisKind.QP, known, replace(FILTERS, qp_cadres=("PROF HORISTA",)))
    assert other.metrics[0].value == 4
    assert any("simulação" in text for text in result.notes)


def test_history_unions_people_and_keeps_overlapping_cadres_and_july_calendar() -> None:
    source = load_fixture("SINT-A")
    rows = (
        HistoryRow("SINT-A", "P1", "V1", date(2026, 3, 1), "PROF PRINCIPAL", "C1", "A", "3", None),
        HistoryRow("SINT-A", "P1", "V1", date(2026, 3, 1), "PROF PRINCIPAL", "C1", "A", "4", None),
        HistoryRow("SINT-A", "P1", "V2", date(2026, 7, 1), "PROF HORISTA", "C2", "A", "3", None),
        HistoryRow("SINT-A", "P2", "V3", date(2026, 5, 1), "PROF HORISTA", "C2", "A", "3", "A4"),
        HistoryRow("SINT-A", "P3", "V4", date(2026, 6, 1), "PROF HORISTA", "C2", "A", "9", None),
        HistoryRow("SINT-A", "P4", "V5", date(2026, 6, 1), "PROF HORISTA", "C2", "I", "3", None),
    )
    result = calculate(AnalysisKind.HISTORY, replace(source, history=rows), FILTERS)
    row = next(r for r in table(result, "history").rows if r[0] == "2026.1")
    assert row[1] == 1
    assert row[2:] == (1, 1)
    monthly = table(result, "monthly").rows
    assert sum(r[2] for r in monthly) == 2  # a soma não é usada como total semestral
    assert faculty_period(date(2026, 7, 31)) == 20261
    assert faculty_period(date(2026, 8, 1)) == 20262
    assert next(r for r in table(result, "history").rows if r[0] == "2026.2")[1] is None


def test_workload_uses_dedicated_rows_not_allocations_and_blocks_base_zero_ratio() -> None:
    source = load_fixture("SINT-A")
    rows = (
        WorkloadRow("SINT-A", "V1", 20261, "SYN-1", "PRINCIPAL", "C", 10, 20),
        WorkloadRow("SINT-A", "V1", 20261, "SYN-1", "PRINCIPAL", "C", 2, 20),
        WorkloadRow("SINT-A", "V2", 20261, "SYN-2", "PRINCIPAL", "C", 0, 0),
        WorkloadRow("SINT-A", "V3", 20261, "SYN-3", "PRINCIPAL", "C", None, 20),
        WorkloadRow("SINT-A", "V4", 20252, "SYN-4", "PRINCIPAL", "C", 999, 20),
    )
    result = calculate(AnalysisKind.WORKLOAD, replace(source, workloads=rows), FILTERS)
    detail = {r[0]: r for r in table(result, "workload").rows}
    assert detail["V1"][4:8] == (12, 20, -8, 60)
    assert detail["V2"][4:8] == (0, 0, 0, None)
    assert detail["V3"][4] is None
    assert "V4" not in detail
    assert result.metrics[1].value == 12
    units_missing = replace(source, workloads=rows, policy=SimulationPolicy())
    result = calculate(AnalysisKind.WORKLOAD, units_missing, FILTERS)
    assert all(r[6] is None and r[7] is None for r in table(result, "workload").rows)


def test_function_evidence_and_simultaneity_do_not_follow_gratification_or_dual_flag() -> None:
    source = load_fixture("SINT-A")
    reg = source.faculty.register[0].registration
    appointments = (
        AppointmentRow(
            "SINT-A", reg, "Papel A", date(2026, 1, 1), date(2026, 1, 31), "SYN-1", True
        ),
        AppointmentRow(
            "SINT-A", reg, "Papel B", date(2026, 2, 1), date(2026, 2, 28), "SYN-2", True
        ),
        AppointmentRow(
            "SINT-A", reg, "Papel C", date(2026, 1, 20), date(2026, 2, 10), "SYN-3", True
        ),
        AppointmentRow(
            "SINT-A", reg, "Atividade acadêmica", date(2026, 1, 1), None, "SYN-4", False
        ),
    )
    result = calculate(AnalysisKind.FUNCTIONS, replace(source, appointments=appointments), FILTERS)
    overlap = table(result, "simultaneous").rows
    assert len(overlap) == 2
    assert not any(set(r[1:3]) == {"Papel A", "Papel B"} for r in overlap)
    metrics = {m.label: m.value for m in result.metrics}
    assert metrics["Função administrativa com evidência"] == 1
    assert metrics["Vínculos com papéis simultâneos"] == 1
    assert len(table(result, "appointments").rows) == 3
    no_appointments = replace(source, appointments=())
    result = calculate(AnalysisKind.FUNCTIONS, no_appointments, FILTERS)
    assert (
        next(m.value for m in result.metrics if m.label == "Função administrativa com evidência")
        == 0
    )
    assert next(m.value for m in result.metrics if m.label == "Registros de função") > 0


def test_functions_distinguish_unavailable_sources_from_observed_absence() -> None:
    source = load_fixture("SINT-A")
    unavailable = replace(
        source,
        appointments=(),
        available=source.available - {"appointments"},
    )
    result = calculate(AnalysisKind.FUNCTIONS, unavailable, FILTERS)
    metrics = {m.label: m for m in result.metrics}
    assert result.status == "Parcial" and result.calculation_version == "academic-funcoes-v2"
    for label in ("Função administrativa com evidência", "Vínculos com papéis simultâneos"):
        assert metrics[label].value is None and metrics[label].status == "Fonte indisponível"
    baseline = calculate(AnalysisKind.FUNCTIONS, source, FILTERS)
    assert metrics["Registros de função"].value == next(
        metric.value for metric in baseline.metrics if metric.label == "Registros de função"
    )
    assert all(row[-1] == "Fonte indisponível" for row in table(result, "function_comparison").rows)
    assert any("Fonte de vigências indisponível" in note for note in result.notes)
    exported = table_csv(result, table(result, "function_comparison"), NOW).decode("utf-8-sig")
    assert "Fonte indisponível" in exported and "Sem evidência no recorte" not in exported

    observed_empty = calculate(AnalysisKind.FUNCTIONS, replace(source, appointments=()), FILTERS)
    assert all(
        row[-1] == "Sem evidência no recorte"
        for row in table(observed_empty, "function_comparison").rows
    )
    observed_metrics = {m.label: m for m in observed_empty.metrics}
    assert observed_metrics["Função administrativa com evidência"].value == 0
    assert observed_metrics["Vínculos com papéis simultâneos"].value == 0

    no_register = replace(
        source,
        faculty=replace(source.faculty, register=()),
        available=source.available - {"register", "functions"},
        functions=(),
    )
    result = calculate(AnalysisKind.FUNCTIONS, no_register, FILTERS)
    metrics = {m.label: m for m in result.metrics}
    assert metrics["Dupla função no cadastro"].value is None
    assert metrics["Dupla função no cadastro"].status == "Fonte indisponível"
    assert metrics["Registros de função"].status == "Fonte indisponível"
    assert any("registros de função indisponível" in note for note in result.notes)


def student(reg, period, status="MT", entry=20241, kind="Ingresso sintético", course="C1"):
    return StudentRow(
        reg, "SINT-A", course, f"Curso {course}", "H1", "D", "GR", entry, period, status, kind
    )


def student_source():
    source = load_fixture("SINT-A")
    history = (
        student(1, 20241),
        student(1, 20241, "MC"),
        student(1, 20242, "MC"),
        student(2, 20241, entry=20242),  # ingresso futuro: não matriculado no ponto anterior
        student(3, 20242, "FR"),
        student(4, 20242, "HF"),
        student(5, 20242, kind="Dupla Diplomacao"),  # entra mesmo sem linha no ponto de ingresso
    )
    current = (
        student(1, 20242),
        student(2, 20241, entry=20242),
        student(3, 20242, "FR"),
        student(4, 20242, "HF"),
        student(5, 20242, kind="Dupla Diplomacao"),
    )
    return replace(
        source,
        students=current,
        student_history=history,
        scholarships=(ScholarshipRow(1, 20241),) * 3 + (ScholarshipRow(2, 20241),),
    )


def test_student_series_deduplicate_apply_future_entry_and_keep_own_populations() -> None:
    result = calculate(AnalysisKind.STUDENTS, student_source(), FILTERS)
    rows = table(result, "students").rows
    assert rows[0] == ("2024.1", 1, 1, 0, 2)
    assert rows[1] == ("2024.2", 2, 0, 1, 0)
    assert rows[2] == ("2025.1", None, None, None, None)
    assert table(result, "enrollment_change").rows[0][4:6] == (1, 100)
    assert all(r[2] is None or r[2] <= r[1] for r in rows)


def test_student_base_zero_and_missing_scholarship_only_affect_their_metrics() -> None:
    source = student_source()
    history = tuple(
        replace(r, status="FR") if r.period == 20241 else r for r in source.student_history
    )
    result = calculate(AnalysisKind.STUDENTS, replace(source, student_history=history), FILTERS)
    change = table(result, "enrollment_change").rows[0]
    assert change[2] == 0 and change[5] is None and change[6] == "Base zero"
    missing_bolsa = replace(source, available=source.available - {"scholarships"}, scholarships=())
    result = calculate(AnalysisKind.STUDENTS, missing_bolsa, FILTERS)
    row = table(result, "students").rows[0]
    assert row[1] == 1 and row[2] is None and row[3] == 0 and row[4] == 2


def test_unknown_entry_does_not_become_zero_and_course_filters_do_not_merge_courses() -> None:
    source = student_source()
    current = tuple(r for r in source.students if r.registration != 1)
    result = calculate(AnalysisKind.STUDENTS, replace(source, students=current), FILTERS)
    assert table(result, "students").rows[0][1:3] == (None, None)
    course = calculate(AnalysisKind.STUDENTS, source, replace(FILTERS, courses=("C2",)))
    assert course.status == "Sem dados"


@pytest.mark.parametrize("kind", list(AnalysisKind))
def test_empty_department_is_not_fabricated_as_observed_zero(kind) -> None:
    source = load_fixture("SINT-VAZIO")
    result = calculate(kind, source, FILTERS)
    assert result.status == "Sem dados"
    if kind == AnalysisKind.HISTORY:
        assert all(r[1] is None for r in table(result, "history").rows)
    if kind == AnalysisKind.STUDENTS:
        assert all(v is None for row in table(result, "students").rows for v in row[1:])


def test_bad_periods_are_refused() -> None:
    source = load_fixture("SINT-A")
    for bad in ("2026.3", "1900.1", "2026';DROP"):
        with pytest.raises(ValueError):
            calculate(AnalysisKind.STUDENTS, source, replace(FILTERS, first_period=bad))
    with pytest.raises(ValueError):
        calculate(
            AnalysisKind.HISTORY,
            source,
            replace(FILTERS, first_period="2026.2", last_period="2024.1"),
        )


def test_csv_and_zip_include_filters_snapshot_nulls_and_synthetic_marker() -> None:
    source = student_source()
    result = calculate(AnalysisKind.STUDENTS, source, FILTERS)
    csv = table_csv(result, table(result, "students"), NOW).decode("utf-8-sig")
    assert "DEMONSTRAÇÃO" in csv and source.fingerprint in csv and "ausente" in csv
    assert "2024.1" in csv and "2026.2" in csv
    package = report_zip((result,), NOW)
    assert package == report_zip((result,), NOW)
    with ZipFile(io.BytesIO(package)) as archive:
        manifest = json.loads(archive.read("manifesto.json"))
        assert manifest["synthetic"] is True
        assert manifest["analyses"][0]["filters"]["qp_cadres"] == ["PROF PRINCIPAL"]
        assert "R06/students.csv" in archive.namelist()
    with pytest.raises(ValueError):
        report_zip((result,), NOW, additional_files={"../fora.txt": b"x"})


def test_branded_chart_png_preserves_missing_values_in_data() -> None:
    from matplotlib import pyplot as plt

    result = calculate(AnalysisKind.STUDENTS, student_source(), FILTERS)
    figure = academic_chart(result, result.charts[0], load_branding())
    assert figure_png(figure).startswith(b"\x89PNG\r\n\x1a\n")
    assert "SINT-A" in figure.texts[0].get_text() and "SINTÉTICOS" in figure.texts[0].get_text()
    assert figure.axes[0].lines[0].get_ydata()[0] == 1
    assert pd_is_nan(figure.axes[0].lines[0].get_ydata()[2])
    plt.close(figure)


def pd_is_nan(value):
    import math

    return math.isnan(value)


def test_checks_are_closed_descriptive_and_exports_protect_prefixed_formulas() -> None:
    checks = inspect_source(load_fixture("SINT-A"))
    assert len(checks) == 10 and len({c.identifier for c in checks}) == 10
    assert next(c.count for c in checks if c.identifier == "C03") > 0
    assert next(c.count for c in checks if c.identifier == "C04") == 0
    assert next(c.count for c in checks if c.identifier == "C07") == 1
    for text in ("  =1+1", "\n@SOMA(A1)", " =HYPERLINK(x)"):
        assert safe_cell(text).startswith("'")
    assert safe_cell(1234567) == "1234567"
    assert safe_cell(1234567.125) == "1234567,125"
    source = load_fixture("SINT-A")
    missing = replace(source, available=source.available - {"scholarships"}, scholarships=())
    assert next(c.count for c in inspect_source(missing) if c.identifier == "C05") is None
