"""Selecionar explicitamente a origem sintética sem fallback entre fontes."""

from dataclasses import dataclass, replace

from vrac.analyses import faculty_overview_fixture
from vrac.analyses.academic_data import ALL_DEPARTMENTS, AcademicSource
from vrac.analyses.faculty_overview import FacultySource
from vrac.authorization import require_data_access
from vrac.department_hierarchy import (
    DepartmentHierarchy,
    hierarchy_for_departments,
    resolve_departments,
)
from vrac.settings import DemoSource, Settings
from vrac.synthetic import DEPARTMENTS, PERIODS, SyntheticDataset, load_demo_data, select_demo_data


class DemoDataError(RuntimeError):
    """Mensagem pública da demonstração, sem detalhes internos da conexão."""


@dataclass(frozen=True)
class DemoOptions:
    departments: tuple[str, ...]
    periods: tuple[str, ...]
    default_period: str
    source: str


def load_demo_options(settings: Settings) -> DemoOptions:
    require_data_access(settings)
    if settings.demo_source == DemoSource.SUPABASE:
        from vrac.db.supabase_reader import load_options

        return load_options(settings)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_options

        return load_options(settings)
    return DemoOptions(DEPARTMENTS, PERIODS, PERIODS[1], "Memória")


def faculty_history_periods(settings: Settings, options: DemoOptions) -> tuple[str, ...]:
    """O histórico usa suas competências, sem ficar limitado à fixture de registros brutos."""
    require_data_access(settings)
    if settings.demo_source in (DemoSource.POSTGRES, DemoSource.SUPABASE):
        return options.periods
    from vrac.analyses.academic_fixture import PERIODS as history_periods

    return history_periods


def load_selected_demo(settings: Settings, *, department: str, period: str) -> SyntheticDataset:
    require_data_access(settings)
    if settings.demo_source == DemoSource.SUPABASE:
        from vrac.db.supabase_reader import load_selected

        return load_selected(settings, department=department, period=period)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_selected

        return load_selected(settings, department=department, period=period)
    return select_demo_data(load_demo_data(settings), department=department, period=period)


def load_faculty_departments(settings: Settings) -> tuple[str, ...]:
    require_data_access(settings)
    if settings.demo_source == DemoSource.SUPABASE:
        from vrac.db.supabase_reader import load_faculty_departments as load

        return load(settings)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_faculty_departments as load

        return load(settings)
    return faculty_overview_fixture.DEPARTMENTS


def load_department_hierarchy(settings: Settings) -> DepartmentHierarchy:
    """Relações da fixture em memória; centro ausente na origem PG é pendência explícita."""
    departments = load_faculty_departments(settings)
    return hierarchy_for_departments(
        departments,
        source={DemoSource.POSTGRES: "PostgreSQL sintético", DemoSource.SUPABASE: "Supabase"}.get(
            settings.demo_source, "Memória"
        ),
        synthetic_centers=settings.demo_source == DemoSource.MEMORY,
    )


def _faculty_scope(
    source: FacultySource, department: str, departments: tuple[str, ...]
) -> FacultySource:
    register = tuple(row for row in source.register if row.department in departments)
    registrations = {row.registration_int for row in register if row.registration_int is not None}
    return replace(
        source,
        department=department,
        register=register,
        real_hours=tuple(row for row in source.real_hours if row.registration_int in registrations),
    )


def load_faculty_source(
    settings: Settings, *, department: str, departments: tuple[str, ...] | None = None
) -> FacultySource:
    """Origem explícita da R01; falha na base nunca recorre aos dados em memória."""
    require_data_access(settings)
    if settings.demo_source == DemoSource.SUPABASE:
        from vrac.db.supabase_reader import load_faculty_source as load

        return load(settings, department=department, departments=departments)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_faculty_source as load

        if departments is None:
            return load(settings, department=department)
        return load(settings, department=department, departments=departments)
    try:
        selected = resolve_departments(
            faculty_overview_fixture.DEPARTMENTS, department, departments
        )
        if departments is not None or department == ALL_DEPARTMENTS:
            parts = [
                faculty_overview_fixture.load_fixture(d)
                for d in faculty_overview_fixture.DEPARTMENTS
            ]
            source = FacultySource(
                department,
                tuple(r for p in parts for r in p.register),
                tuple(r for p in parts for r in p.real_hours),
                "Memória",
                faculty_overview_fixture.FIXTURE_VERSION,
            )
            return _faculty_scope(source, department, selected)
        return faculty_overview_fixture.load_fixture(department)
    except ValueError:
        raise DemoDataError("Selecione um departamento disponível na demonstração.") from None


def load_academic_source(
    settings: Settings, *, department: str, departments: tuple[str, ...] | None = None
) -> AcademicSource:
    """Carregar todos os roteiros na origem escolhida; nunca alternar fontes por falha."""
    require_data_access(settings)
    if settings.demo_source == DemoSource.SUPABASE:
        from vrac.db.supabase_reader import load_academic_source as load

        return load(settings, department=department, departments=departments)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_academic_source as load

        if departments is None:
            return load(settings, department=department)
        return load(settings, department=department, departments=departments)
    from vrac.analyses.academic_fixture import load_fixture

    try:
        selected = resolve_departments(
            faculty_overview_fixture.DEPARTMENTS, department, departments
        )
        if departments is None:
            return load_fixture(department)
        source = load_fixture(ALL_DEPARTMENTS)
        students = tuple(row for row in source.students if row.department in selected)
        student_history = tuple(row for row in source.student_history if row.department in selected)
        registrations = {row.registration for row in (*students, *student_history)}
        scoped = {
            name: tuple(row for row in getattr(source, name) if row.department in selected)
            for name in ("history", "workloads", "allocations", "functions", "appointments")
        }
        return replace(
            source,
            department=department,
            faculty=_faculty_scope(source.faculty, department, selected),
            students=students,
            student_history=student_history,
            scholarships=tuple(
                row for row in source.scholarships if row.registration in registrations
            ),
            **scoped,
        )
    except ValueError:
        raise DemoDataError("Selecione departamentos disponíveis na demonstração.") from None
