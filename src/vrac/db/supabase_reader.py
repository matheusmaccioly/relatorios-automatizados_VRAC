"""Leitura dos contratos R01–R06 pelo JWT do usuário, em RPCs fixas sob RLS."""

from datetime import UTC, datetime

from vrac.analyses.academic_data import (
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
from vrac.analyses.faculty_overview import FacultySource, RealHoursRow, RegisterRow
from vrac.authorization import require_data_access
from vrac.demo_data import DemoDataError, DemoOptions
from vrac.department_hierarchy import resolve_departments
from vrac.settings import Settings
from vrac.supabase_auth import current_session
from vrac.synthetic import FacultyRecord, SyntheticDataset, TeachingAllocation

MAX_ROWS = 5000
COMPONENTS = {
    "register": RegisterRow,
    "real_hours": RealHoursRow,
    "history": HistoryRow,
    "workloads": WorkloadRow,
    "allocations": AllocationRow,
    "functions": FunctionRow,
    "appointments": AppointmentRow,
    "students": StudentRow,
    "student_history": StudentRow,
    "scholarships": ScholarshipRow,
    "demo_faculty": FacultyRecord,
    "demo_allocations": TeachingAllocation,
}


def _rpc(settings: Settings, name: str, params: dict | None = None) -> dict:
    require_data_access(settings)
    if name not in {"vrac_options", "vrac_snapshot"}:
        raise DemoDataError("Consulta indisponível.")
    try:
        result = current_session().client.rpc(name, params or {}).execute().data
        if not isinstance(result, dict) or result.get("synthetic") is not True:
            raise ValueError
        return result
    except Exception:
        raise DemoDataError(
            "Não foi possível consultar os dados autorizados no Supabase. "
            "Confira sua sessão e tente novamente. Nenhum exemplo local foi carregado."
        ) from None


def load_options(settings: Settings) -> DemoOptions:
    data = _rpc(settings, "vrac_options")
    try:
        departments, periods = tuple(data["departments"]), tuple(data["periods"])
        if (
            not departments
            or not periods
            or any(not isinstance(v, str) or not v for v in (*departments, *periods))
        ):
            raise ValueError
        return DemoOptions(departments, periods, periods[-1], "Supabase · dados sintéticos")
    except (KeyError, TypeError, ValueError):
        raise DemoDataError("Filtros do Supabase indisponíveis ou inválidos.") from None


def load_faculty_departments(settings: Settings) -> tuple[str, ...]:
    return load_options(settings).departments


def _snapshot(settings: Settings, department: str, departments: tuple[str, ...] | None) -> dict:
    options = load_options(settings)
    try:
        selected = resolve_departments(options.departments, department, departments)
    except ValueError:
        raise DemoDataError("Selecione departamentos autorizados.") from None
    return _rpc(settings, "vrac_snapshot", {"p_departments": list(selected)})


def _decode(data: dict, component: str) -> tuple:
    rows = data[component]
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise ValueError
    converted = []
    for row in rows:
        item = dict(row)
        for name in ("reference_date", "start", "end"):
            if isinstance(item.get(name), str):
                item[name] = datetime.fromisoformat(item[name])
        converted.append(COMPONENTS[component](**item))
    return tuple(converted)


def _academic(data: dict, department: str) -> AcademicSource:
    try:
        values = {name: _decode(data, name) for name in COMPONENTS if not name.startswith("demo_")}
        faculty = FacultySource(
            department,
            values.pop("register"),
            values.pop("real_hours"),
            "Supabase · dados sintéticos",
            data["version"],
        )
        return AcademicSource(
            department,
            faculty,
            tuple(data["periods"]),
            policy=SimulationPolicy(**data["policy"]),
            available=frozenset((*values, "register", "real_hours", "policy")),
            **values,
        )
    except (KeyError, TypeError, ValueError):
        raise DemoDataError("O snapshot do Supabase está incompleto ou incompatível.") from None


def load_academic_source(
    settings: Settings,
    *,
    department: str,
    departments: tuple[str, ...] | None = None,
) -> AcademicSource:
    return _academic(_snapshot(settings, department, departments), department)


def load_faculty_source(
    settings: Settings,
    *,
    department: str,
    departments: tuple[str, ...] | None = None,
) -> FacultySource:
    return load_academic_source(settings, department=department, departments=departments).faculty


def load_selected(settings: Settings, *, department: str, period: str) -> SyntheticDataset:
    data = _snapshot(settings, department, None)
    try:
        if period not in data["periods"]:
            raise ValueError
        faculty = tuple(r for r in _decode(data, "demo_faculty") if r.period == period)
        allocations = tuple(r for r in _decode(data, "demo_allocations") if r.period == period)
        return SyntheticDataset(
            faculty,
            allocations,
            data["version"],
            True,
            "Supabase · dados sintéticos",
            datetime.now(UTC),
        )
    except (KeyError, TypeError, ValueError):
        raise DemoDataError("Selecione um período disponível no Supabase.") from None
