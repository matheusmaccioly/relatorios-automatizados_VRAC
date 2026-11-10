"""Cenários determinísticos completos em memória, somente por escolha explícita."""

from dataclasses import replace
from datetime import date

from vrac.analyses.academic_data import (
    ALL_DEPARTMENTS,
    AcademicSource,
    AllocationRow,
    AppointmentRow,
    FunctionRow,
    HistoryRow,
    ScholarshipRow,
    SimulationPolicy,
    StudentRow,
    WorkloadRow,
)
from vrac.analyses.faculty_overview import FacultySource
from vrac.analyses.faculty_overview_fixture import DEPARTMENTS, REAL_HOURS, REGISTER

PERIODS = ("2024.1", "2024.2", "2025.1", "2025.2", "2026.1", "2026.2")
COMPONENTS = frozenset(
    {
        "history",
        "workloads",
        "allocations",
        "functions",
        "appointments",
        "students",
        "student_history",
        "scholarships",
        "policy",
        "register",
        "real_hours",
    }
)


def load_fixture(department: str) -> AcademicSource:
    if department == "DEMO — Departamento exemplo":
        from vrac.analyses.presentation_fixture import load_presentation

        return load_presentation()
    if department not in (*DEPARTMENTS, ALL_DEPARTMENTS):
        raise ValueError("Departamento indisponível na simulação.")
    register = tuple(
        r for r in REGISTER if department == ALL_DEPARTMENTS or r.department == department
    )
    registrations = {r.registration_int for r in register}
    history, workloads, allocations, functions, appointments = [], [], [], [], []
    students, student_history, scholarships = [], [], []
    for i, person in enumerate(register):
        for year in range(2024, 2027):
            for month in range(1, 13):
                cadre = "PROF PRINCIPAL" if i % 2 == 0 else "PROF HORISTA"
                row = HistoryRow(
                    person.department or "SINT-A",
                    person.person_key,
                    person.registration,
                    date(year, month, 1),
                    cadre,
                    person.category,
                    "A",
                    "3",
                    None,
                )
                history.append(row)
                if i == 0 and month == 3:
                    history.append(replace(row, payroll_batch="4"))
        for year in range(2024, 2027):
            for sem in (1, 2):
                code = year * 10 + sem
                hours = 0 if i == 0 else None if i == 1 else (6, 12, 20, 45)[i % 4]
                workloads.append(
                    WorkloadRow(
                        person.department or "SINT-A",
                        person.registration,
                        code,
                        person.name,
                        person.cadre,
                        person.category,
                        hours,
                        person.weekly_hours,
                    )
                )
                allocations.append(
                    AllocationRow(
                        person.department or "SINT-A",
                        "SINT-B",
                        person.registration,
                        code,
                        f"SYN-DISC-{i}",
                        f"SYN-T-{i}",
                        4,
                        0 if i == 0 else None if i == 1 else 20,
                        "S" if i < 2 else "N",
                        None,
                    )
                )
                if i % 2 == 0:
                    functions.append(
                        FunctionRow(
                            person.department or "SINT-A",
                            "SINT-B",
                            person.registration,
                            year,
                            3 if sem == 1 else 9,
                            "Função sintética",
                            "Papel A",
                        )
                    )
        if i == 0 and person.registration:
            appointments += [
                AppointmentRow(
                    person.department or "SINT-A",
                    person.registration,
                    "Coordenação sintética",
                    date(2025, 1, 1),
                    date(2026, 12, 31),
                    "SYN-ATO-01",
                    True,
                ),
                AppointmentRow(
                    person.department or "SINT-A",
                    person.registration,
                    "Comissão sintética",
                    date(2026, 2, 1),
                    date(2026, 10, 31),
                    "SYN-ATO-02",
                    True,
                ),
            ]
    for dept in DEPARTMENTS:
        if dept == "SINT-VAZIO" or (department != ALL_DEPARTMENTS and department != dept):
            continue
        for i in range(18):
            registration = (1000 if dept == "SINT-A" else 2000) + i
            entry_index = i // 3
            entry = int(PERIODS[entry_index].replace(".", ""))
            records = []
            for index in range(entry_index, len(PERIODS)):
                p = int(PERIODS[index].replace(".", ""))
                status = (
                    "FR" if i % 7 == 0 and index - entry_index == 2 else "MC" if i % 3 else "MT"
                )
                row = StudentRow(
                    registration,
                    dept,
                    f"SYN-CURSO-{i % 2}",
                    f"Curso sintético {i % 2}",
                    "SYN-H01",
                    "D",
                    "GR",
                    entry,
                    p,
                    status,
                    "Dupla Diplomacao" if i % 5 == 0 else "Ingresso sintético",
                )
                records.append(row)
                student_history.append(row)
                if status in {"MT", "MC"} and i % 3 == 0:
                    scholarships.extend([ScholarshipRow(registration, p)] * 2)
                if status == "FR":
                    break
            students.append(records[-1])
    faculty = FacultySource(
        department,
        register,
        tuple(r for r in REAL_HOURS if r.registration_int in registrations),
        "Memória",
        "academic-memory-v1",
    )
    source = AcademicSource(
        department,
        faculty,
        PERIODS,
        tuple(history),
        tuple(workloads),
        tuple(allocations),
        tuple(functions),
        tuple(appointments),
        tuple(students),
        tuple(student_history),
        tuple(scholarships),
        SimulationPolicy("h/semana (simulação)", "h/semana (simulação)", True, True),
        COMPONENTS,
    )

    return source
