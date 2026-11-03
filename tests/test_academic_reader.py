"""Isolamento de falha por fonte, usando um cursor fictício e sem rede."""

from contextlib import contextmanager, nullcontext
from dataclasses import asdict

import pytest

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_fixture import load_fixture
from vrac.db import synthetic_postgres as reader
from vrac.settings import DemoSource, Settings


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, sql, parameters):
        query = next(q for q in reader.Query if sql == reader._query(q))
        self.connection.calls.append((query, parameters))
        if query in self.connection.failures:
            raise RuntimeError("password=segredo-ficticio-nao-exibir")
        self.rows = self.connection.responses[query]

    def fetchmany(self, limit):
        return self.rows[:limit]


class FakeConnection:
    def __init__(self, failures):
        source = load_fixture("SINT-A")
        self.failures = failures
        self.calls = []
        self.responses = {
            reader.Query.DEPARTMENTS: [{"department": "SINT-A"}],
            reader.Query.PERIODS: [{"period": p} for p in source.periods],
            reader.Query.FACULTY_REGISTER: [asdict(r) for r in source.faculty.register],
            reader.Query.FACULTY_REAL_HOURS: [asdict(r) for r in source.faculty.real_hours],
            reader.Query.HISTORY: [asdict(r) for r in source.history],
            reader.Query.WORKLOADS: [asdict(r) for r in source.workloads],
            reader.Query.TEACHING_ALLOCATIONS: [asdict(r) for r in source.allocations],
            reader.Query.FUNCTIONS: [asdict(r) for r in source.functions],
            reader.Query.APPOINTMENTS: [asdict(r) for r in source.appointments],
            reader.Query.STUDENTS: [asdict(r) for r in source.students],
            reader.Query.STUDENT_HISTORY: [asdict(r) for r in source.student_history],
            reader.Query.SCHOLARSHIPS: [asdict(r) for r in source.scholarships],
            reader.Query.POLICY: [asdict(source.policy)],
        }

    def cursor(self):
        return FakeCursor(self)

    def transaction(self):
        return nullcontext()


@pytest.mark.parametrize(
    "failed_query",
    [reader.Query.SCHOLARSHIPS, reader.Query.FACULTY_REGISTER, reader.Query.FACULTY_REAL_HOURS],
)
def test_source_failure_does_not_block_independent_analyses(monkeypatch, failed_query) -> None:
    connection = FakeConnection({failed_query})

    @contextmanager
    def connect(settings):
        yield connection, "fixture-test-v1"

    monkeypatch.setattr(reader, "_connection", connect)
    source = reader.load_academic_source(
        Settings(demo_source=DemoSource.POSTGRES), department="SINT-A"
    )
    filters = AnalysisFilters("2024.1", "2026.2", "2026.1", qp_cadres=("PROF PRINCIPAL",))
    assert source.errors and all("segredo-ficticio" not in e for e in source.errors)
    assert calculate(AnalysisKind.HISTORY, source, filters).status != "Bloqueado"
    assert calculate(AnalysisKind.WORKLOAD, source, filters).status != "Bloqueado"
    if failed_query == reader.Query.SCHOLARSHIPS:
        assert "scholarships" not in source.available
        result = calculate(AnalysisKind.STUDENTS, source, filters)
        series = next(t for t in result.tables if t.key == "students")
        assert series.rows[0][1] is not None and series.rows[0][2] is None
    elif failed_query == reader.Query.FACULTY_REGISTER:
        assert "register" not in source.available
        assert calculate(AnalysisKind.QP, source, filters).status == "Bloqueado"
        assert calculate(AnalysisKind.STUDENTS, source, filters).status != "Bloqueado"
    else:
        from vrac.analyses.faculty_overview import OverviewFilters, OverviewStatus, compute_overview

        assert "real_hours" not in source.available and not source.faculty.real_hours_available
        overview = compute_overview(source.faculty, OverviewFilters())
        assert overview.total == 5 and overview.status == OverviewStatus.PARTIAL
        assert calculate(AnalysisKind.QP, source, filters).metrics[0].value == 5
    bound_calls = [p for q, p in connection.calls if q == reader.Query.HISTORY]
    assert bound_calls == [{"department": "SINT-A"}]


def test_r01_hours_failure_keeps_register_and_all_department_queries_bound(monkeypatch):
    from vrac.analyses.academic_data import ALL_DEPARTMENTS
    from vrac.analyses.faculty_overview import OverviewFilters, OverviewStatus, compute_overview

    connection = FakeConnection({reader.Query.FACULTY_REAL_HOURS})

    @contextmanager
    def connect(settings):
        yield connection, "fixture-test-v1"

    monkeypatch.setattr(reader, "_connection", connect)
    source = reader.load_faculty_source(
        Settings(demo_source=DemoSource.POSTGRES), department=ALL_DEPARTMENTS
    )
    result = compute_overview(source, OverviewFilters())
    assert result.total == 5 and result.status == OverviewStatus.PARTIAL
    assert not source.real_hours and not source.real_hours_available
    assert [p for q, p in connection.calls if q == reader.Query.FACULTY_REGISTER] == [
        {"department": "SINT-A"}
    ]
    with pytest.raises(Exception, match="Selecione um departamento"):
        reader.load_faculty_source(
            Settings(demo_source=DemoSource.POSTGRES), department="SINT-A'; DROP"
        )


@pytest.mark.parametrize(
    "failed_query", [reader.Query.WORKLOADS, reader.Query.TEACHING_ALLOCATIONS, reader.Query.POLICY]
)
def test_workload_source_failures_are_isolated(monkeypatch, failed_query):
    connection = FakeConnection({failed_query})

    @contextmanager
    def connect(settings):
        yield connection, "fixture-test-v1"

    monkeypatch.setattr(reader, "_connection", connect)
    source = reader.load_academic_source(
        Settings(demo_source=DemoSource.POSTGRES), department="SINT-A"
    )
    filters = AnalysisFilters("2024.1", "2026.2", "2026.1")
    result = calculate(AnalysisKind.WORKLOAD, source, filters)
    assert calculate(AnalysisKind.STUDENTS, source, filters).status != "Bloqueado"
    if failed_query == reader.Query.WORKLOADS:
        assert result.status == "Bloqueado"
    elif failed_query == reader.Query.TEACHING_ALLOCATIONS:
        assert result.status != "Bloqueado"
        assert any("indisponível" in note for note in result.notes)
    else:
        assert result.status != "Bloqueado"
        rows = next(t for t in result.tables if t.key == "workload").rows
        assert all(row[6:8] == (None, None) for row in rows)
