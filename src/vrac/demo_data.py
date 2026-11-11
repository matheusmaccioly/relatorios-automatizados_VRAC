"""Selecionar explicitamente a origem sintética sem fallback entre fontes."""

from dataclasses import dataclass, replace

from vrac.analyses import faculty_overview_fixture
from vrac.analyses.academic_data import ALL_DEPARTMENTS, AcademicSource
from vrac.analyses.faculty_overview import FacultySource
from vrac.authorization import require_data_access
from vrac.department_hierarchy import (
    DepartmentHierarchy,
    hierarchy_for_departments,
    institutional_hierarchy,
    resolve_departments,
)
from vrac.settings import DataMode, DemoSource, Settings
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

        if settings.data_mode == DataMode.PSEUDONYMIZED:
            from vrac.db.institutional_faculty import load_options

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
        if settings.data_mode == DataMode.PSEUDONYMIZED:
            raise DemoDataError("Conferência sintética indisponível nesta origem.")
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

        if settings.data_mode == DataMode.PSEUDONYMIZED:
            from vrac.db.institutional_faculty import load_faculty_departments as load

        return load(settings)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_faculty_departments as load

        return load(settings)
    return (*faculty_overview_fixture.DEPARTMENTS, "DEMO — Departamento exemplo")


def load_department_hierarchy(settings: Settings) -> DepartmentHierarchy:
    """Relações da fixture em memória; centro ausente na origem PG é pendência explícita."""
    departments = load_faculty_departments(settings)
    if settings.data_mode == DataMode.PSEUDONYMIZED:
        return institutional_hierarchy(departments)
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

        if settings.data_mode == DataMode.PSEUDONYMIZED:
            from vrac.db.institutional_faculty import load_faculty_source as load

        return load(settings, department=department, departments=departments)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_faculty_source as load

        if departments is None:
            return load(settings, department=department)
        return load(settings, department=department, departments=departments)
    if department == "DEMO — Departamento exemplo":
        from vrac.analyses.presentation_fixture import load_presentation

        if departments is not None and departments != (department,):
            raise DemoDataError("Selecione o exemplo de apresentação isoladamente.")
        return load_presentation().faculty
    try:
        selected = resolve_departments(load_faculty_departments(settings), department, departments)
        if departments is not None or department == ALL_DEPARTMENTS:
            parts = [
                faculty_overview_fixture.load_fixture(d) for d in load_faculty_departments(settings)
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

        if settings.data_mode == DataMode.PSEUDONYMIZED:
            from vrac.db.institutional_faculty import load_academic_source as load

        return load(settings, department=department, departments=departments)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_academic_source as load

        if departments is None:
            return load(settings, department=department)
        return load(settings, department=department, departments=departments)
    from vrac.analyses.academic_fixture import load_fixture

    if department == "DEMO — Departamento exemplo":
        from vrac.analyses.presentation_fixture import load_presentation

        if departments is not None and departments != (department,):
            raise DemoDataError("Selecione o exemplo de apresentação isoladamente.")
        return load_presentation()
    try:
        selected = resolve_departments(load_faculty_departments(settings), department, departments)
        if departments is None and department != ALL_DEPARTMENTS:
            return load_fixture(department)
        from vrac.analyses.presentation_fixture import load_presentation

        source = load_fixture(ALL_DEPARTMENTS)
        demo = load_presentation()
        source = replace(
            source,
            faculty=replace(
                source.faculty,
                register=source.faculty.register + demo.faculty.register,
                real_hours=source.faculty.real_hours + demo.faculty.real_hours,
            ),
            **{
                key: getattr(source, key) + getattr(demo, key)
                for key in (
                    "history",
                    "workloads",
                    "allocations",
                    "functions",
                    "appointments",
                    "students",
                    "student_history",
                    "scholarships",
                )
            },
        )
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
