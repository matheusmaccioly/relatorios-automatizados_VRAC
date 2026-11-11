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
    StudentRow,
    WorkloadRow,
)
from vrac.analyses.academic_export import report_zip, table_csv
from vrac.analyses.academic_fixture import load_fixture
from vrac.analyses.academic_quality import inspect_source
from vrac.analyses.export import safe_cell
from vrac.branding import load_branding
from vrac.charts import academic_chart, figure_png

FILTERS = AnalysisFilters("2024.1", "2026.2", "2026.1", group_a_cadres=("PROF PRINCIPAL",))
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


def test_group_comparison_reproduces_qp_and_general_and_other_group_pairs() -> None:
    source = load_fixture("SINT-A")
    result = calculate(AnalysisKind.COMPARISON, source, FILTERS)
    metrics = {m.label: m.value for m in result.metrics}
    # Quadro vazio fica fora, como o filtro de página do painel.
    assert metrics["QP"] == 1 and metrics["Geral"] == 4
    assert metrics["QP em % de Geral"] == 25
    assert "Em ambos os grupos" not in metrics
    assert result.status == "Calculado"
    assert not any("simulação" in text.casefold() for text in result.notes)
    departments = table(result, "departments")
    assert departments.columns == (
        "Departamento",
        "QP",
        "Geral",
        "Em ambos os grupos",
        "Participação (%)",
    )
    assert departments.rows == (("SINT-A", 1, 4, 1, 25.0),)

    disjoint = calculate(
        AnalysisKind.COMPARISON,
        source,
        replace(FILTERS, group_b_cadres=("PROF HORISTA",), group_b_name="Horistas"),
    )
    metrics = {m.label: m.value for m in disjoint.metrics}
    assert (metrics["QP"], metrics["Horistas"], metrics["Em ambos os grupos"]) == (1, 1, 0)
    assert not any(m.unit == "%" for m in disjoint.metrics)
    assert table(disjoint, "departments").rows[0][-1] is None

    overlap = calculate(
        AnalysisKind.COMPARISON,
        source,
        replace(
            FILTERS,
            group_a_cadres=("PROF PRINCIPAL", "PROF HORISTA"),
            group_a_name="A",
            group_b_cadres=("PROF HORISTA", "PRINCIPAL"),
            group_b_name="B",
        ),
    )
    metrics = {m.label: m.value for m in overlap.metrics}
    assert (metrics["A"], metrics["B"], metrics["Em ambos os grupos"]) == (2, 2, 1)

    by_category = calculate(
        AnalysisKind.COMPARISON,
        source,
        replace(FILTERS, group_a_cadres=(), group_a_categories=("PROF PRINCIPAL",)),
    )
    assert by_category.metrics[0].value == 2

    absent = calculate(AnalysisKind.COMPARISON, source, replace(FILTERS, statuses=("Afastado",)))
    assert absent.status == "Sem dados" and not absent.metrics
    for bad in (
        replace(FILTERS, group_b_name="QP"),
        replace(FILTERS, group_a_name="Departamento"),
        replace(FILTERS, group_a_cadres=("INEXISTENTE",)),
    ):
        with pytest.raises(ValueError):
            calculate(AnalysisKind.COMPARISON, source, bad)


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


def test_workload_uses_dedicated_rows_not_allocations_and_follows_dashboard_order() -> None:
    source = load_fixture("SINT-A")
    rows = (
        WorkloadRow("SINT-A", "V3", 20261, "SYN-3", "PRINCIPAL", "C", None, 20),
        WorkloadRow("SINT-A", "V2", 20261, "SYN-2", "PRINCIPAL", "C", 0, 0),
        WorkloadRow("SINT-A", "V1", 20261, "SYN-1", "PRINCIPAL", "C", 10, 20),
        WorkloadRow("SINT-A", "V1", 20261, "SYN-1", "PRINCIPAL", "C", 2, 20),
        WorkloadRow("SINT-A", "V4", 20252, "SYN-4", "PRINCIPAL", "C", 999, 20),
    )
    result = calculate(AnalysisKind.WORKLOAD, replace(source, workloads=rows), FILTERS)
    workload = table(result, "workload")
    assert workload.title == "CH Real dos Professores em Disciplinas"
    assert "Diferença (simulação)" not in workload.columns
    assert workload.columns[5:8] == (
        "Indicador de CH",
        "Horas Reais (Semestre Atual)",
        "CH Contratada",
    )
    # Ordem decrescente de Horas Reais, ausente ao final (slide 8 do roteiro).
    assert [r[0] for r in workload.rows] == ["V1", "V2", "V3"]
    detail = {r[0]: r for r in workload.rows}
    assert detail["V1"][5:8] == ("Resultados distintos", 12, 20)  # linhas 10 e 2
    assert detail["V2"][5:8] == ("Sem alocação (CH = 0)", 0, 0)
    assert detail["V3"][6] is None
    assert result.metrics[1].value == 12
    # Situação vem do cadastro; vínculos sem cadastro não atendem a um filtro de situação.
    filtered = calculate(
        AnalysisKind.WORKLOAD,
        replace(source, workloads=rows),
        replace(FILTERS, statuses=("Ativo",)),
    )
    assert filtered.status == "Sem dados"


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
    assert metrics["Professores com papéis simultâneos"] == 1
    assert len(table(result, "appointments").rows) == 3
    no_appointments = replace(source, appointments=())
    result = calculate(AnalysisKind.FUNCTIONS, no_appointments, FILTERS)
    assert (
        next(m.value for m in result.metrics if m.label == "Função administrativa com evidência")
        == 0
    )
    assert next(m.value for m in result.metrics if m.label == "Registros de gratificação") > 0


def test_functions_follow_gratification_page_and_hide_unavailable_synthetic_evidence() -> None:
    source = load_fixture("SINT-A")
    unavailable = replace(source, appointments=(), available=source.available - {"appointments"})
    result = calculate(AnalysisKind.FUNCTIONS, unavailable, FILTERS)
    metrics = {m.label: m for m in result.metrics}
    assert result.status == "Calculado" and result.calculation_version == "academic-funcoes-v2"
    assert "Função administrativa com evidência" not in metrics
    assert {t.key for t in result.tables}.isdisjoint({"appointments", "simultaneous"})
    baseline = calculate(AnalysisKind.FUNCTIONS, source, FILTERS)
    assert metrics["Registros de gratificação"].value == next(
        metric.value for metric in baseline.metrics if metric.label == "Registros de gratificação"
    )
    by_function = table(result, "by_function")
    assert by_function.columns == ("Gratificação", "Professores")
    assert sum(r[1] for r in by_function.rows) >= 1
    assert all(len(row) == 4 for row in table(result, "function_comparison").rows)
    assert [c.table for c in result.charts] == ["by_function", "by_department", "by_month"]

    observed_empty = calculate(AnalysisKind.FUNCTIONS, replace(source, appointments=()), FILTERS)
    observed_metrics = {m.label: m for m in observed_empty.metrics}
    assert observed_metrics["Função administrativa com evidência"].value == 0
    assert observed_metrics["Professores com papéis simultâneos"].value == 0

    no_register = replace(
        source,
        faculty=replace(source.faculty, register=()),
        available=source.available - {"register", "functions"},
        functions=(),
    )
    result = calculate(AnalysisKind.FUNCTIONS, no_register, FILTERS)
    metrics = {m.label: m for m in result.metrics}
    assert metrics["Professores com dupla função"].value is None
    assert metrics["Professores com dupla função"].status == "Fonte indisponível"
    assert metrics["Registros de gratificação"].status == "Fonte indisponível"
    assert any("gratificações indisponível" in note for note in result.notes)


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


def test_entry_follows_dashboard_and_course_filters_do_not_merge_courses() -> None:
    source = student_source()
    # Sem cadastro não conta (DAX); não vira ausência de dado.
    current = tuple(r for r in source.students if r.registration != 1)
    result = calculate(AnalysisKind.STUDENTS, replace(source, students=current), FILTERS)
    assert table(result, "students").rows[0][1:3] == (0, 0)
    # Ingresso em branco no cadastro conta, como a comparação do DAX com vazio.
    blank = tuple(
        replace(r, entry_period=None) if r.registration == 1 else r for r in source.students
    )
    result = calculate(AnalysisKind.STUDENTS, replace(source, students=blank), FILTERS)
    assert table(result, "students").rows[0][1:3] == (1, 1)
    assert any("ingresso em branco" in note for note in result.notes)
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
        assert manifest["analyses"][0]["filters"]["group_a_cadres"] == ["PROF PRINCIPAL"]
        assert "6-analise-geral-alunos/students.csv" in archive.namelist()
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
