"""Departamento fictício completo para apresentação; não representa unidade real."""

from dataclasses import replace
from datetime import date

from vrac.analyses.academic_data import AcademicSource, HistoryRow, WorkloadRow
from vrac.analyses.faculty_overview import FacultySource, RealHoursRow
from vrac.analyses.faculty_overview_fixture import _register

DEPARTMENT = "DEMO — Departamento exemplo"


def load_presentation() -> AcademicSource:
    from vrac.analyses.academic_fixture import load_fixture

    base = load_fixture("SINT-A")
    categories = (
        "PROFESSOR ADJUNTO 2",
        "PROFESSOR ADJUNTO 1",
        "PROFESSOR ASSISTENTE 1",
        "PROFESSOR ASSOCIADO 1",
        "PROFESSOR TITULAR",
        "PROFESSOR AGREGADO",
    )
    register = tuple(
        _register(
            DEPARTMENT,
            str(990000001 + i),
            f"DEMO-{i:03}",
            "PROF PRINCIPAL" if i < 12 else "PROF QCI",
            categories[i % len(categories)],
            weekly_hours=40 if i < 12 else 20,
        )
        for i in range(14)
    )
    loads = (12, 12, 12, 12, 16, 16, 16, 20, 20, 24, 24, 24, 8, 8)
    faculty = FacultySource(
        DEPARTMENT,
        register,
        tuple(
            RealHoursRow(r.registration_int, 20261, loads[i], r.cadre)
            for i, r in enumerate(register)
        ),
        "Memória — exemplo de apresentação",
        "presentation-v1",
    )
    history = tuple(
        HistoryRow(
            DEPARTMENT,
            r.person_key,
            r.registration,
            date(year, month, 1),
            r.cadre,
            r.category,
            "A",
            "3",
            None,
        )
        for r in register
        for year in range(2024, 2027)
        for month in range(1, 13)
    )
    workloads = tuple(
        WorkloadRow(
            DEPARTMENT,
            r.registration,
            int(p.replace(".", "")),
            r.name,
            r.cadre,
            r.category,
            loads[i],
            r.weekly_hours,
        )
        for i, r in enumerate(register)
        for p in base.periods
    )
    return replace(
        base,
        department=DEPARTMENT,
        faculty=faculty,
        history=history,
        workloads=workloads,
        allocations=(),
        functions=(),
        appointments=(),
        students=tuple(
            replace(r, department=DEPARTMENT, registration=r.registration + 10000)
            for r in base.students
        ),
        student_history=tuple(
            replace(r, department=DEPARTMENT, registration=r.registration + 10000)
            for r in base.student_history
        ),
        scholarships=tuple(
            replace(r, registration=r.registration + 10000) for r in base.scholarships
        ),
    )
