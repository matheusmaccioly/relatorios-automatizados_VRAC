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


@pytest.mark.parametrize("failed_query", [reader.Query.SCHOLARSHIPS, reader.Query.FACULTY_REGISTER])
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
    else:
        assert "register" not in source.available
        assert calculate(AnalysisKind.QP, source, filters).status == "Bloqueado"
        assert calculate(AnalysisKind.STUDENTS, source, filters).status != "Bloqueado"
    bound_calls = [p for q, p in connection.calls if q == reader.Query.HISTORY]
    assert bound_calls == [{"department": "SINT-A"}]
