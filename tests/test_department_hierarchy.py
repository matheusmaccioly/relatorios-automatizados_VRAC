"""Recortes por centro conservam a unidade de departamento e não presumem relações reais."""

from contextlib import contextmanager, nullcontext
from dataclasses import asdict

import pytest

from vrac.analyses.academic_data import ALL_DEPARTMENTS
from vrac.analyses.academic_fixture import load_fixture
from vrac.db import synthetic_postgres as reader
from vrac.demo_data import (
    DemoDataError,
    load_academic_source,
    load_department_hierarchy,
    load_faculty_source,
)
from vrac.department_hierarchy import (
    ALL_CENTERS,
    UNKNOWN_CENTER,
    DepartmentHierarchy,
    DepartmentRelation,
    hierarchy_for_departments,
)
from vrac.settings import DemoSource, Settings


def test_centers_limit_departments_and_unknown_origin_stays_explicit() -> None:
    hierarchy = load_department_hierarchy(Settings())
    assert hierarchy.departments_for("Centro sintético 1") == ("SINT-A", "SINT-VAZIO")
    assert hierarchy.departments_for("Centro sintético 2") == ("SINT-B",)
    assert hierarchy.departments_for(ALL_CENTERS) == (
        "SINT-A",
        "SINT-B",
        "SINT-VAZIO",
        "DEMO — Departamento exemplo",
    )
    assert "fictícios" in hierarchy.note
    unknown = hierarchy_for_departments(("SYN-A", "SYN-B"), source="PostgreSQL sintético")
    assert unknown.centers == (UNKNOWN_CENTER,)
    assert unknown.departments_for(UNKNOWN_CENTER) == ("SYN-A", "SYN-B")
    assert "pendente" in unknown.note
    with pytest.raises(ValueError, match="centro disponível"):
        hierarchy.departments_for("Centro inexistente")


def test_ambiguous_center_relationship_is_rejected() -> None:
    with pytest.raises(ValueError, match="único centro"):
        DepartmentHierarchy(
            (DepartmentRelation("A", "SINT-A"), DepartmentRelation("B", "SINT-A")),
            "Memória",
            "Teste",
        )


def test_center_scope_limits_every_memory_component_and_records_its_label() -> None:
    settings = Settings()
    scope = "Centro sintético 1 · Todos os departamentos"
    selected = ("SINT-A", "SINT-VAZIO")
    faculty = load_faculty_source(settings, department=scope, departments=selected)
    source = load_academic_source(settings, department=scope, departments=selected)
    assert faculty.department == source.department == source.faculty.department == scope
    assert {row.department for row in faculty.register} == {"SINT-A"}
    registrations = {row.registration_int for row in faculty.register}
    assert all(row.registration_int in registrations for row in faculty.real_hours)
    for name in (
        "history",
        "workloads",
        "allocations",
        "functions",
        "appointments",
        "students",
        "student_history",
    ):
        assert all(row.department in selected for row in getattr(source, name))
    student_keys = {row.registration for row in (*source.students, *source.student_history)}
    assert source.scholarships and all(
        row.registration in student_keys for row in source.scholarships
    )
    all_source = load_academic_source(settings, department=ALL_DEPARTMENTS)
    assert len(source.faculty.register) < len(all_source.faculty.register)
    assert source.fingerprint != all_source.fingerprint


@pytest.mark.parametrize("selected", [(), ("SINT-A", "SINT-A"), ("NÃO EXISTE",)])
def test_invalid_memory_department_sets_never_create_partial_results(selected) -> None:
    for load in (load_faculty_source, load_academic_source):
        with pytest.raises(DemoDataError, match="departamento"):
            load(Settings(), department="Centro sintético", departments=selected)


class ScopedConnection:
    def transaction(self):
        return nullcontext()


def install_scoped_reader(monkeypatch):
    calls = []
    opens = []

    @contextmanager
    def connection(settings):
        opens.append(settings)
        yield ScopedConnection(), "synthetic-scoped-test"

    def rows(connection, query, parameters=None):
        calls.append((query, parameters))
        if query == reader.Query.DEPARTMENTS:
            return [{"department": d} for d in ("SINT-A", "SINT-B", "SINT-VAZIO")]
        if query == reader.Query.PERIODS:
            return [{"period": "2026.1"}]
        if query == reader.Query.POLICY:
            return [asdict(load_fixture("SINT-A").policy)]
        source = load_fixture(parameters["department"])
        components = {
            reader.Query.FACULTY_REGISTER: source.faculty.register,
            reader.Query.FACULTY_REAL_HOURS: source.faculty.real_hours,
            reader.Query.HISTORY: source.history,
            reader.Query.WORKLOADS: source.workloads,
            reader.Query.TEACHING_ALLOCATIONS: source.allocations,
            reader.Query.FUNCTIONS: source.functions,
            reader.Query.APPOINTMENTS: source.appointments,
            reader.Query.STUDENTS: source.students,
            reader.Query.STUDENT_HISTORY: source.student_history,
            reader.Query.SCHOLARSHIPS: source.scholarships,
        }
        return [asdict(row) for row in components[query]]

    monkeypatch.setattr(reader, "_connection", connection)
    monkeypatch.setattr(reader, "_rows", rows)
    return calls, opens


def test_postgres_center_reads_only_bound_departments_in_one_snapshot(monkeypatch) -> None:
    calls, opens = install_scoped_reader(monkeypatch)
    settings = Settings(demo_source=DemoSource.POSTGRES)
    scope = "Centro sintético · Todos os departamentos"
    source = reader.load_academic_source(
        settings, department=scope, departments=("SINT-A", "SINT-VAZIO")
    )
    assert len(opens) == 1
    assert source.department == source.faculty.department == scope
    assert source.history and {r.department for r in source.history} == {"SINT-A"}
    record_calls = [(q, p) for q, p in calls if p is not None]
    assert record_calls
    assert {p["department"] for _, p in record_calls} == {"SINT-A", "SINT-VAZIO"}
    assert all(p["department"] != scope for _, p in record_calls)
    for query, _ in record_calls:
        assert "%(department)s" in reader._query(query)


def test_invalid_postgres_scope_stops_before_any_record_query(monkeypatch) -> None:
    calls, _ = install_scoped_reader(monkeypatch)
    with pytest.raises(DemoDataError, match="departamento disponível"):
        reader.load_faculty_source(
            Settings(demo_source=DemoSource.POSTGRES),
            department="Centro sintético",
            departments=("SINT-A", "SINT-A'; SELECT 1; --"),
        )
    assert all(parameters is None for _, parameters in calls)


def test_institutional_mapping_intersects_access_and_keeps_unknown_explicit():
    from vrac.department_hierarchy import institutional_hierarchy

    hierarchy = institutional_hierarchy(
        ("ADM", "ECO", "EDU", "FIL", "ELE", "IND", "INF", "DIR", "JUR", "NOVO")
    )
    assert hierarchy.departments_for("CCS") == ("ADM", "ECO")
    assert hierarchy.departments_for("CTCH") == ("EDU", "FIL")
    assert hierarchy.departments_for("CTC") == ("ELE", "IND", "INF")
    assert hierarchy.departments_for(UNKNOWN_CENTER) == ("NOVO",)
    assert institutional_hierarchy(("IND",)).departments_for("CTC") == ("IND",)
