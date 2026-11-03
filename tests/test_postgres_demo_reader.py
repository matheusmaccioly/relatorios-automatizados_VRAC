"""Leitor sintético simulado: parâmetros, autorização e falhas sem conexão de rede."""

from contextlib import nullcontext
from dataclasses import asdict
from typing import Any

import pytest

pytest.importorskip("psycopg")

from vrac.authorization import AccessDenied  # noqa: E402
from vrac.db import synthetic_postgres as reader  # noqa: E402
from vrac.demo_data import DemoDataError, load_selected_demo  # noqa: E402
from vrac.settings import DataMode, DemoSource, Settings  # noqa: E402
from vrac.synthetic import FacultyRecord  # noqa: E402

SETTINGS = Settings(demo_source=DemoSource.POSTGRES)
METADATA = {
    "synthetic": True,
    "version": reader.VERSION,
    "seed": 42,
    "database_name": reader.DATABASE,
    "role_name": reader.READER,
    "transaction_read_only": "on",
    "ssl": True,
}


class Cursor:
    def __init__(self, connection: "Connection") -> None:
        self.connection = connection
        self.result: list[dict[str, Any]] = []

    def __enter__(self) -> "Cursor":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def execute(self, sql: str, parameters: dict | None) -> None:
        query = next(q for q in reader.Query if sql == reader._query(q))
        self.connection.calls.append((query, sql, parameters))
        self.result = self.connection.responses[query]

    def fetchmany(self, size: int) -> list[dict[str, Any]]:
        return self.result[:size]


class Connection:
    def __init__(self) -> None:
        self.calls: list[tuple[reader.Query, str, dict | None]] = []
        self.isolation_level: object = None
        self.responses = {
            reader.Query.METADATA: [dict(METADATA)],
            reader.Query.DEPARTMENTS: [{"department": "SYN-A"}, {"department": "SYN-VAZIO"}],
            reader.Query.PERIODS: [{"period": "2026.1"}, {"period": "2026.2"}],
            reader.Query.FACULTY: [
                asdict(FacultyRecord("SYN-A", "2026.1", "2026-03", "DOC-1", "V1", "Tipo A", 0)),
                asdict(FacultyRecord("SYN-A", "2026.1", "2026-04", "DOC-1", "V1", "Tipo A", None)),
            ],
            reader.Query.ALLOCATIONS: [],
        }

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def cursor(self) -> Cursor:
        return Cursor(self)

    def transaction(self):
        return nullcontext()


@pytest.fixture
def connection(monkeypatch: pytest.MonkeyPatch) -> Connection:
    connection = Connection()
    monkeypatch.setattr(reader, "_connect", lambda: connection)
    return connection


def test_records_keep_months_zero_null_and_bound_filters(connection: Connection) -> None:
    result = reader.load_selected(SETTINGS, department="SYN-A", period="2026.1")
    assert len(result.faculty) == 2
    assert result.faculty[0].real_hours == 0 and result.faculty[1].real_hours is None
    assert result.synthetic and result.source == "PostgreSQL sintético"
    assert result.loaded_at is not None and result.loaded_at.tzinfo is not None
    assert result.allocations == ()
    for query, sql, parameters in connection.calls:
        if query in {reader.Query.FACULTY, reader.Query.ALLOCATIONS}:
            assert "%(department)s" in sql and "%(period)s" in sql
            assert "SYN-A" not in sql
            assert parameters == {"department": "SYN-A", "period": "2026.1"}


@pytest.mark.parametrize(
    "metadata",
    [
        {"synthetic": False},
        {"version": "outra-versao"},
        {"database_name": "outro-banco"},
        {"role_name": "administrador"},
        {"transaction_read_only": "off"},
        {"ssl": False},
    ],
)
def test_wrong_database_identity_or_permissions_block_before_records(
    connection: Connection,
    metadata: dict,
) -> None:
    connection.responses[reader.Query.METADATA][0].update(metadata)
    with pytest.raises(DemoDataError, match="conexão local"):
        reader.load_selected(SETTINGS, department="SYN-A", period="2026.1")
    assert [c[0] for c in connection.calls] == [reader.Query.METADATA]


def test_real_mode_and_memory_source_do_not_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden() -> None:
        pytest.fail("Conexão não autorizada.")

    monkeypatch.setattr(reader, "_connect", forbidden)
    with pytest.raises(AccessDenied):
        reader.load_options(Settings(data_mode=DataMode.REAL, demo_source=DemoSource.POSTGRES))
    with pytest.raises(DemoDataError, match="explicitamente"):
        reader.load_options(Settings())


@pytest.mark.parametrize(
    "department,period",
    [
        ("SYN-A'; DROP TABLE x; --", "2026.1"),
        ("SYN-A", "1900.1"),
    ],
)
def test_unavailable_filters_are_refused_before_record_query(
    connection: Connection,
    department: str,
    period: str,
) -> None:
    with pytest.raises(DemoDataError, match="disponíveis"):
        reader.load_selected(SETTINGS, department=department, period=period)
    assert not any(
        c[0] in {reader.Query.FACULTY, reader.Query.ALLOCATIONS} for c in connection.calls
    )


def test_row_limit_blocks_incomplete_display(connection: Connection) -> None:
    connection.responses[reader.Query.FACULTY] *= reader.MAX_ROWS
    with pytest.raises(DemoDataError, match="limite"):
        reader.load_selected(SETTINGS, department="SYN-A", period="2026.1")


def test_driver_failure_is_sanitized_and_never_activates_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail() -> None:
        raise RuntimeError("password=segredo-ficticio-deste-teste host=servidor-ficticio")

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Fallback para memória não autorizado.")

    monkeypatch.setattr(reader, "_connect", fail)
    monkeypatch.setattr("vrac.demo_data.load_demo_data", forbidden)
    with pytest.raises(DemoDataError) as error:
        load_selected_demo(SETTINGS, department="SYN-A", period="2026.1")
    assert str(error.value) == reader.CONNECTION_MESSAGE
    assert "segredo-ficticio" not in str(error.value)


def test_connection_arguments_pin_local_reader_tls_and_timeouts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import psycopg

    captured = {}
    sentinel = object()

    def capture(**kwargs: object) -> object:
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(psycopg, "connect", capture)
    assert reader._connect() is sentinel
    assert captured["host"] == captured["hostaddr"] == "127.0.0.1"
    assert captured["user"] == reader.READER and captured["dbname"] == reader.DATABASE
    assert captured["sslmode"] == "verify-full"
    assert captured["connect_timeout"] == 3
    assert "default_transaction_read_only=on" in captured["options"]
    assert "password" not in captured


REGISTER_ROW = {
    "department": "SYN-A",
    "registration": "0001",
    "registration_int": 1,
    "person_key": "hash-opaco",
    "name": "Docente fictício",
    "cadre": "PROF PRINCIPAL",
    "category": "PROF PRINCIPAL",
    "status": "Ativo",
    "dual_role": "N",
    "extraordinary": None,
    "weekly_hours": 40,
    "tenure_years": None,
    "degree": None,
}


def test_faculty_source_binds_department_and_keeps_snapshot(connection: Connection) -> None:
    connection.responses[reader.Query.FACULTY_REGISTER] = [dict(REGISTER_ROW)]
    connection.responses[reader.Query.FACULTY_REAL_HOURS] = [
        {"registration_int": 1, "semester": 20261, "hours": 0, "cadre": "PROF PRINCIPAL"}
    ]
    source = reader.load_faculty_source(SETTINGS, department="SYN-A")
    assert source.register[0].registration == "0001"  # texto preservado, sem perder zeros
    assert source.real_hours[0].hours == 0
    assert source.source == "PostgreSQL sintético"
    assert connection.isolation_level is not None
    calls = {query: (sql, parameters) for query, sql, parameters in connection.calls}
    for query in (reader.Query.FACULTY_REGISTER, reader.Query.FACULTY_REAL_HOURS):
        sql, parameters = calls[query]
        assert "%(department)s" in sql and "SYN-A" not in sql
        assert parameters == {"department": "SYN-A"}


def test_faculty_register_query_never_returns_raw_person_identifier() -> None:
    sql = reader._query(reader.Query.FACULTY_REGISTER)
    assert 'md5("CPF")' in sql
    assert "AS person_key" in sql and '"CPF" AS' not in sql


def test_faculty_source_refuses_unknown_department_before_record_queries(
    connection: Connection,
) -> None:
    with pytest.raises(DemoDataError, match="disponível"):
        reader.load_faculty_source(SETTINGS, department="SYN-A'; DROP TABLE x; --")
    assert not any(
        query in {reader.Query.FACULTY_REGISTER, reader.Query.FACULTY_REAL_HOURS}
        for query, _, _ in connection.calls
    )
