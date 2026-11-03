"""Leitura parametrizada do PostgreSQL sintético local, sem acesso institucional."""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import StrEnum
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

from vrac.analyses.faculty_overview import FacultySource, RealHoursRow, RegisterRow
from vrac.authorization import require_data_access
from vrac.demo_data import DemoDataError, DemoOptions
from vrac.department_hierarchy import resolve_departments
from vrac.dev.postgres_runtime import DATABASE, PORT, READER, runtime_directory
from vrac.dev.semantic_postgres import VERSION
from vrac.settings import DemoSource, Settings
from vrac.synthetic import FacultyRecord, SyntheticDataset, TeachingAllocation

if TYPE_CHECKING:
    from psycopg import Connection

    from vrac.analyses.academic_data import AcademicSource

MAX_ROWS = 5000
MAX_OPTIONS = 1000
CONNECTION_MESSAGE = (
    "Não foi possível consultar o PostgreSQL sintético. "
    "Confira se o banco local está iniciado e se a conexão de demonstração está preparada. "
    "Nenhum exemplo em memória foi carregado."
)


class Query(StrEnum):
    METADATA = "metadata"
    DEPARTMENTS = "departments"
    PERIODS = "periods"
    FACULTY = "faculty"
    ALLOCATIONS = "allocations"
    FACULTY_REGISTER = "faculty_register"
    FACULTY_REAL_HOURS = "faculty_real_hours"
    HISTORY = "academic_history"
    WORKLOADS = "academic_workloads"
    TEACHING_ALLOCATIONS = "academic_allocations"
    FUNCTIONS = "academic_functions"
    APPOINTMENTS = "academic_appointments"
    STUDENTS = "academic_students"
    STUDENT_HISTORY = "academic_student_history"
    SCHOLARSHIPS = "academic_scholarships"
    POLICY = "academic_policy"


def _query(query: Query) -> str:
    relative = f"synthetic_demo/{query.value}.sql"
    packaged = files("vrac").joinpath("sql", relative)
    if packaged.is_file():
        return packaged.read_text(encoding="utf-8")
    return (Path(__file__).resolve().parents[3] / "sql" / relative).read_text(encoding="utf-8")


def _connect() -> "Connection":
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        raise DemoDataError(
            "O suporte ao PostgreSQL sintético não está instalado. "
            "Prepare o ambiente com a opção Postgres descrita no guia de execução."
        ) from None
    runtime = runtime_directory(Path(__file__).resolve().parents[3])
    return psycopg.connect(
        host="127.0.0.1",
        hostaddr="127.0.0.1",
        port=PORT,
        dbname=DATABASE,
        user=READER,
        passfile=str(runtime / "pgpass.conf"),
        sslmode="verify-full",
        sslrootcert=str(runtime / "server.crt"),
        connect_timeout=3,
        application_name="vrac-synthetic-demo",
        options=(
            "-c default_transaction_read_only=on -c statement_timeout=5000 -c lock_timeout=1000"
        ),
        row_factory=dict_row,
    )


def _rows(
    connection: "Connection",
    query: Query,
    parameters: Mapping[str, str] | None = None,
) -> list[dict]:
    limit = (
        2
        if query == Query.METADATA
        else MAX_OPTIONS
        if query in (Query.DEPARTMENTS, Query.PERIODS)
        else MAX_ROWS
    )
    with connection.cursor() as cursor:
        cursor.execute(_query(query), parameters)
        result = cursor.fetchmany(limit + 1)
    if len(result) > limit:
        raise DemoDataError("O recorte ultrapassa o limite da demonstração. Reduza os filtros.")
    return result


@contextmanager
def _connection(settings: Settings) -> Iterator[tuple["Connection", str]]:
    require_data_access(settings)
    if settings.demo_source != DemoSource.POSTGRES:
        raise DemoDataError("Selecione explicitamente a origem PostgreSQL sintética.")
    try:
        with _connect() as connection:
            # As leituras de metadados/filtros/registros compartilham o mesmo snapshot.
            from psycopg import IsolationLevel

            connection.isolation_level = IsolationLevel.REPEATABLE_READ
            records = _rows(connection, Query.METADATA)
            if len(records) != 1:
                raise DemoDataError("O banco local não tem uma identificação sintética válida.")
            metadata = records[0]
            if not (
                metadata.get("synthetic") is True
                and metadata.get("version") == VERSION
                and metadata.get("database_name") == DATABASE
                and metadata.get("role_name") == READER
                and metadata.get("transaction_read_only") == "on"
                and metadata.get("ssl") is True
            ):
                raise DemoDataError(
                    "A conexão local não corresponde à demonstração sintética de leitura."
                )
            yield connection, f"{VERSION} · semente {metadata['seed']}"
    except DemoDataError:
        raise
    except Exception:
        # Drivers podem incluir senha, caminhos, SQL e host no erro original.
        raise DemoDataError(CONNECTION_MESSAGE) from None


def _options(connection: "Connection") -> DemoOptions:
    departments = tuple(r["department"] for r in _rows(connection, Query.DEPARTMENTS))
    periods = tuple(r["period"] for r in _rows(connection, Query.PERIODS))
    if (
        not departments
        or not periods
        or any(not isinstance(x, str) or not x for x in (*departments, *periods))
    ):
        raise DemoDataError("O banco sintético não contém opções de filtros válidas.")
    return DemoOptions(departments, periods, periods[-1], "PostgreSQL sintético")


def load_options(settings: Settings) -> DemoOptions:
    with _connection(settings) as (connection, _):
        return _options(connection)


def load_selected(settings: Settings, *, department: str, period: str) -> SyntheticDataset:
    with _connection(settings) as (connection, version):
        options = _options(connection)
        if department not in options.departments or period not in options.periods:
            raise DemoDataError("Selecione departamento e período disponíveis na demonstração.")
        parameters = {"department": department, "period": period}
        faculty = tuple(
            FacultyRecord(**row) for row in _rows(connection, Query.FACULTY, parameters)
        )
        allocations = tuple(
            TeachingAllocation(**row) for row in _rows(connection, Query.ALLOCATIONS, parameters)
        )
        return SyntheticDataset(
            faculty,
            allocations,
            version=version,
            synthetic=True,
            source=options.source,
            loaded_at=datetime.now(UTC),
        )


def load_faculty_departments(settings: Settings) -> tuple[str, ...]:
    with _connection(settings) as (connection, _):
        return _options(connection).departments


def load_faculty_source(
    settings: Settings, *, department: str, departments: tuple[str, ...] | None = None
) -> FacultySource:
    """R01: cadastro e Horas Reais do departamento no mesmo snapshot de leitura."""
    with _connection(settings) as (connection, version):
        available_departments = _options(connection).departments
        try:
            selected = resolve_departments(available_departments, department, departments)
        except ValueError:
            raise DemoDataError("Selecione um departamento disponível na demonstração.") from None
        register, hours = [], []
        hours_available = True
        for dept in selected:
            parameters = {"department": dept}
            register.extend(
                RegisterRow(**row) for row in _rows(connection, Query.FACULTY_REGISTER, parameters)
            )
            try:
                with connection.transaction():
                    hours.extend(
                        RealHoursRow(**row)
                        for row in _rows(connection, Query.FACULTY_REAL_HOURS, parameters)
                    )
            except Exception:
                hours_available = False
        return FacultySource(
            department,
            tuple(register),
            tuple(hours) if hours_available else (),
            "PostgreSQL sintético",
            version,
            real_hours_available=hours_available,
        )


def load_academic_source(
    settings: Settings, *, department: str, departments: tuple[str, ...] | None = None
) -> "AcademicSource":
    with _connection(settings) as (connection, version):
        return _read_academic_source(
            connection, version, department=department, departments=departments
        )


def _read_academic_source(
    connection: "Connection",
    version: str,
    *,
    department: str,
    departments: tuple[str, ...] | None = None,
) -> "AcademicSource":
    """Reutilizar a leitura existente dentro de um snapshot, inclusive na conferência R06."""
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

    options = _options(connection)
    try:
        selected = resolve_departments(options.departments, department, departments)
    except ValueError:
        raise DemoDataError("Selecione um departamento disponível na demonstração.") from None
    register, hours = [], []
    available, errors = set(), []
    register_ok, hours_ok = True, True
    for dept in selected:
        parameters = {"department": dept}
        try:
            with connection.transaction():
                register.extend(
                    RegisterRow(**r) for r in _rows(connection, Query.FACULTY_REGISTER, parameters)
                )
        except Exception:
            register_ok = False
        try:
            with connection.transaction():
                hours.extend(
                    RealHoursRow(**r)
                    for r in _rows(connection, Query.FACULTY_REAL_HOURS, parameters)
                )
        except Exception:
            hours_ok = False
    if register_ok:
        available.add("register")
    else:
        register = []
        errors.append(
            "Cadastro docente indisponível; histórico e fontes acadêmicas continuam independentes."
        )
    if hours_ok:
        available.add("real_hours")
    else:
        hours = []
        errors.append("Detalhe de Horas Reais do cadastro indisponível.")
    faculty = FacultySource(
        department,
        tuple(register),
        tuple(hours),
        "PostgreSQL sintético",
        version,
        real_hours_available=hours_ok,
    )
    components = (
        ("history", Query.HISTORY, HistoryRow),
        ("workloads", Query.WORKLOADS, WorkloadRow),
        ("allocations", Query.TEACHING_ALLOCATIONS, AllocationRow),
        ("functions", Query.FUNCTIONS, FunctionRow),
        ("appointments", Query.APPOINTMENTS, AppointmentRow),
        ("students", Query.STUDENTS, StudentRow),
        ("student_history", Query.STUDENT_HISTORY, StudentRow),
        ("scholarships", Query.SCHOLARSHIPS, ScholarshipRow),
    )
    labels = {
        "history": "histórico docente",
        "workloads": "carga horária",
        "allocations": "alocações",
        "functions": "registros de função",
        "appointments": "vigências administrativas",
        "students": "cadastro acadêmico",
        "student_history": "histórico acadêmico",
        "scholarships": "bolsas",
    }
    values = {}
    for name, query, row_type in components:
        try:
            # Uma fonte opcional ausente não invalida as outras leituras.
            with connection.transaction():
                rows = []
                # Sem recorte adicional, manter a consulta agregada existente.
                # Em um centro, usar somente sua lista validada de departamentos.
                for selected_department in (department,) if departments is None else selected:
                    rows.extend(
                        row_type(**r)
                        for r in _rows(connection, query, {"department": selected_department})
                    )
                    if len(rows) > MAX_ROWS:
                        raise DemoDataError(
                            "O recorte ultrapassa o limite da demonstração. Reduza os filtros."
                        )
                values[name] = tuple(rows)
            available.add(name)
        except Exception:
            values[name] = ()
            errors.append(
                f"Fonte de {labels[name]} indisponível; somente seus resultados ficam afetados."
            )
    policy = SimulationPolicy()
    try:
        with connection.transaction():
            policy_rows = _rows(connection, Query.POLICY)
            if len(policy_rows) == 1:
                policy = SimulationPolicy(**policy_rows[0])
                available.add("policy")
    except Exception:
        errors.append("Metadados de simulação indisponíveis; unidades não foram presumidas.")
    return AcademicSource(
        department,
        faculty,
        options.periods,
        policy=policy,
        available=frozenset(available),
        errors=tuple(errors),
        **values,
    )
