"""Selecionar explicitamente a origem sintética sem fallback entre fontes."""

from dataclasses import dataclass

from vrac.analyses import faculty_overview_fixture
from vrac.analyses.academic_data import AcademicSource
from vrac.analyses.faculty_overview import FacultySource
from vrac.authorization import require_data_access
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
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_options

        return load_options(settings)
    return DemoOptions(DEPARTMENTS, PERIODS, PERIODS[1], "Memória")


def load_selected_demo(settings: Settings, *, department: str, period: str) -> SyntheticDataset:
    require_data_access(settings)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_selected

        return load_selected(settings, department=department, period=period)
    return select_demo_data(load_demo_data(settings), department=department, period=period)


def load_faculty_departments(settings: Settings) -> tuple[str, ...]:
    require_data_access(settings)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_faculty_departments as load

        return load(settings)
    return faculty_overview_fixture.DEPARTMENTS


def load_faculty_source(settings: Settings, *, department: str) -> FacultySource:
    """Origem explícita da R01; falha na base nunca recorre aos dados em memória."""
    require_data_access(settings)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_faculty_source as load

        return load(settings, department=department)
    try:
        return faculty_overview_fixture.load_fixture(department)
    except ValueError:
        raise DemoDataError("Selecione um departamento disponível na demonstração.") from None


def load_academic_source(settings: Settings, *, department: str) -> AcademicSource:
    """Carregar todos os roteiros na origem escolhida; nunca alternar fontes por falha."""
    require_data_access(settings)
    if settings.demo_source == DemoSource.POSTGRES:
        from vrac.db.synthetic_postgres import load_academic_source as load

        return load(settings, department=department)
    from vrac.analyses.academic_fixture import load_fixture

    return load_fixture(department)
