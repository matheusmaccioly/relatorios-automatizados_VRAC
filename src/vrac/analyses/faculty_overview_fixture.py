"""Cenários fictícios em memória para R01; identificados e sem valor institucional."""

from vrac.analyses.faculty_overview import FacultySource, RealHoursRow, RegisterRow

FIXTURE_VERSION = "faculty-overview-memory-v1"
SOURCE_LABEL = "Memória"
DEPARTMENTS = ("SINT-A", "SINT-B", "SINT-VAZIO")


def _register(
    department: str,
    registration: str,
    person: str,
    cadre: str | None,
    category: str | None,
    *,
    dual_role: str | None = "N",
    weekly_hours: float | None = 40,
) -> RegisterRow:
    return RegisterRow(
        department=department,
        registration=registration,
        registration_int=int(registration),
        person_key=person,
        name=f"Docente fictício {person[-3:]}",
        cadre=cadre,
        category=category,
        status="Ativo",
        dual_role=dual_role,
        extraordinary=None,
        weekly_hours=weekly_hours,
        tenure_years=None,
        degree=None,
    )


REGISTER = (
    # Mesma pessoa com dois vínculos: total conta matrículas, aviso aponta a pessoa.
    _register("SINT-A", "880000001", "SYN-P-001", "PROF PRINCIPAL", "PROF PRINCIPAL"),
    _register("SINT-A", "880000002", "SYN-P-001", "PROF HORISTA", "PROF HORISTA", weekly_hours=20),
    _register("SINT-A", "880000003", "SYN-P-002", "PRINCIPAL", "PROF PRINCIPAL", dual_role="S"),
    _register("SINT-A", "880000004", "SYN-P-003", "COMPLEMENTAR TEMPO PARCIAL", "PROF QCP"),
    _register("SINT-A", "880000005", "SYN-P-004", None, None, weekly_hours=None),
    _register("SINT-B", "880000006", "SYN-P-005", "PROF SUPLEMENTAR", "PROF SUPLEMENTAR"),
)

REAL_HOURS = (
    RealHoursRow(880000001, 20252, 30, "PROF PRINCIPAL"),
    RealHoursRow(880000001, 20261, 12, "PROF PRINCIPAL"),
    RealHoursRow(880000002, 20261, 0, "PROF HORISTA"),
    RealHoursRow(880000003, 20261, 50, "PRINCIPAL"),
    RealHoursRow(880000004, 20261, None, "COMPLEMENTAR TEMPO PARCIAL"),
    RealHoursRow(880000006, 20252, 10, "PROF SUPLEMENTAR"),
    # 880000005 não tem linha de Horas Reais: célula ausente, nunca zero.
)


def load_fixture(department: str) -> FacultySource:
    if department not in DEPARTMENTS:
        raise ValueError("Departamento indisponível na demonstração.")
    register = tuple(row for row in REGISTER if row.department == department)
    registrations = {row.registration_int for row in register}
    hours = tuple(row for row in REAL_HOURS if row.registration_int in registrations)
    return FacultySource(department, register, hours, SOURCE_LABEL, FIXTURE_VERSION)
