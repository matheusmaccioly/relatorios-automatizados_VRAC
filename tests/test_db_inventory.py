"""Inventário limitado com conexão simulada, sem driver nem banco real."""

import json
from dataclasses import replace
from typing import Any

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy.dialects.mssql import pyodbc as mssql_pyodbc  # noqa: E402
from sqlalchemy.exc import DBAPIError  # noqa: E402

from vrac.db.config import DatabaseConfig  # noqa: E402
from vrac.db.errors import DatabaseConfigurationError  # noqa: E402
from vrac.db.inventory import collect_inventory  # noqa: E402


class FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.fetch_sizes: list[int] = []
        self.closed = False

    def mappings(self) -> "FakeResult":
        return self

    def fetchmany(self, size: int) -> list[dict[str, Any]]:
        self.fetch_sizes.append(size)
        return self.rows[:size]

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    closed = False
    invalidated = False

    def __init__(
        self, responses: dict[tuple[str, str], list[dict[str, Any]] | Exception] | None = None
    ) -> None:
        self.responses = responses or {}
        self.calls: list[tuple[Any, dict[str, Any]]] = []
        self.results: list[FakeResult] = []

    def execute(self, statement: Any, parameters: dict[str, Any]) -> FakeResult:
        self.calls.append((statement, dict(parameters)))
        query = statement.text
        category = (
            "foreign_keys"
            if "sys.foreign_keys" in query
            else "keys"
            if "sys.key_constraints" in query
            else "columns"
            if "AS max_length_bytes" in query
            else "objects"
        )
        response = self.responses.get((parameters["schema"], category), [])
        if isinstance(response, Exception):
            raise response
        result = FakeResult(response)
        self.results.append(result)
        return result


def configured_database(**overrides: Any) -> DatabaseConfig:
    values: dict[str, Any] = {
        "dbms": "mssql",
        "server": "servidor-ficticio.invalid",
        "port": 1433,
        "database": "banco_ficticio",
        "schemas": ("escopo_a", "escopo_b"),
        "driver": "ODBC Driver 18 for SQL Server",
        "auth_mode": "windows",
        "sqlserver_confirmed": True,
        "scope_approved": True,
        "metadata_row_limit": 2,
    }
    values.update(overrides)
    return DatabaseConfig(**values)


def category(report: dict[str, Any], name: str, schema_index: int = 0) -> dict[str, Any]:
    return report["schemas"][schema_index]["categories"][name]


def test_catalog_queries_are_closed_bound_and_limited_to_approved_schemas() -> None:
    config = configured_database()
    connection = FakeConnection()
    report = collect_inventory(connection, config)
    assert len(connection.calls) == 4 * len(config.schemas)
    assert report["limits"]["queries_executed"] == report["limits"]["max_queries"] == 8
    for statement, parameters in connection.calls:
        query = statement.text
        assert "TOP (:row_limit)" in query
        assert "ORDER BY" in query
        assert parameters["schema"] in config.schemas
        assert parameters["row_limit"] == config.metadata_row_limit + 1
        assert "escopo_a" not in query and "escopo_b" not in query
        assert "SELECT *" not in query.upper()
        assert "sys.databases" not in query.lower()
        assert "sys.sql_modules" not in query.lower()
        if "allowed_schemas" in parameters:
            assert parameters["allowed_schemas"] == config.schemas
            assert statement._bindparams["allowed_schemas"].expanding
        if "sys.foreign_keys" in query:
            assert "ss.name = :schema" in query
            assert "ss.name IN :allowed_schemas" in query
            assert "ts.name IN :allowed_schemas" in query
    assert all(result.closed and result.fetch_sizes == [3] for result in connection.results)
    assert config.server not in json.dumps(report)


def test_empty_catalog_is_unknown_never_proof_of_absence() -> None:
    report = collect_inventory(FakeConnection(), configured_database())
    assert report["coverage"] == "unknown"
    assert report["status"] == "partial"
    for schema in report["schemas"]:
        assert schema["coverage"] == "unknown"
        for data in schema["categories"].values():
            assert data["coverage"] == "unknown"
            assert data["status"] == "partial"
            assert data["rows"] == []
            assert not data["truncated"]
            assert "desconhecida" in data["warnings"][0]


def test_sqlserver_compilation_keeps_top_and_schema_lists_as_bound_parameters() -> None:
    config = configured_database(schemas=("Escopo com espaço", "OUTRO-ESCOPO"))
    connection = FakeConnection()
    collect_inventory(connection, config)
    # O dialeto não carrega o driver ou abre conexão. qmark é o estilo do pyodbc.
    dialect = mssql_pyodbc.dialect(paramstyle="qmark")
    for statement, parameters in connection.calls:
        compiled = statement.compile(dialect=dialect)
        expanded = compiled.construct_expanded_state(parameters)
        sql = expanded.statement
        assert "TOP (?)" in sql
        assert ":row_limit" not in sql and ":schema" not in sql
        assert all(schema not in sql for schema in config.schemas)
        assert sql.count("?") == len(expanded.positiontup)
        bound_values = [expanded.parameters[name] for name in expanded.positiontup]
        assert config.metadata_row_limit + 1 in bound_values
        assert parameters["schema"] in bound_values
        if "allowed_schemas" in parameters:
            assert "IN (?, ?)" in sql
            assert all(schema in bound_values for schema in config.schemas)


def test_truncation_keeps_only_limit_and_does_not_claim_complete_metadata() -> None:
    rows = [
        {"schema_name": "escopo_a", "object_name": f"objeto_ficticio_{n}", "object_type": "view"}
        for n in range(4)
    ]
    connection = FakeConnection({("escopo_a", "objects"): rows})
    report = collect_inventory(connection, configured_database())
    objects = category(report, "objects")
    assert len(objects["rows"]) == 2
    assert objects["truncated"]
    assert objects["status"] == "partial"
    assert objects["coverage"] == "unknown"
    assert connection.results[0].fetch_sizes == [3]


def test_out_of_scope_metadata_and_unrequested_fields_never_enter_output() -> None:
    valid_fk = {
        "source_schema": "escopo_a",
        "source_table": "origem_ficticia",
        "source_column": "id",
        "target_schema": "escopo_b",
        "target_table": "destino_ficticio",
        "target_column": "id",
        "constraint_name": "fk_ficticia",
        "column_ordinal": 1,
        "is_disabled": False,
        "is_not_trusted": False,
        "definition": "conteudo_nao_autorizado",
    }
    outside = dict(valid_fk, target_schema="fora_do_escopo", target_table="nome_privado_externo")
    outside_source = dict(valid_fk, source_schema="fora_do_escopo")
    connection = FakeConnection(
        {
            ("escopo_a", "objects"): [
                {"schema_name": "fora_do_escopo", "object_name": "nome_privado_externo"}
            ],
            ("escopo_a", "foreign_keys"): [valid_fk, outside, outside_source],
        }
    )
    report = collect_inventory(connection, configured_database(metadata_row_limit=5))
    foreign_keys = category(report, "foreign_keys")
    assert len(foreign_keys["rows"]) == 1
    assert foreign_keys["rows"][0]["target_schema"] == "escopo_b"
    assert foreign_keys["status"] == "partial"
    serialized = json.dumps(report)
    assert "nome_privado_externo" not in serialized
    assert "fora_do_escopo" not in serialized
    assert "conteudo_nao_autorizado" not in serialized


def test_columns_preserve_null_metadata_units_and_hide_external_custom_types() -> None:
    connection = FakeConnection(
        {
            ("escopo_a", "columns"): [
                {
                    "schema_name": "escopo_a",
                    "object_name": "objeto_ficticio",
                    "column_name": "coluna_ficticia",
                    "data_type": "tipo_privado_externo",
                    "data_type_schema": "schema_privado_externo",
                    "base_data_type": "nvarchar",
                    "max_length_bytes": -1,
                    "numeric_precision": 0,
                    "numeric_scale": 0,
                    "is_nullable": True,
                    "is_identity": None,
                }
            ]
        }
    )
    report = collect_inventory(connection, configured_database())
    row = category(report, "columns")["rows"][0]
    assert row["data_type"] is None and row["data_type_schema"] is None
    assert row["base_data_type"] == "nvarchar"
    assert row["max_length_bytes"] == -1
    assert row["is_identity"] is None
    assert "bytes" in report["units"]["max_length_bytes"]
    assert "privado_externo" not in json.dumps(report)


def test_permission_failure_keeps_other_schema_categories_without_error_details() -> None:
    error = Exception("42501", "SELECT permission denied; senha-ficticia; tabela-privada")
    connection = FakeConnection({("escopo_a", "objects"): error})
    report = collect_inventory(connection, configured_database())
    failure = category(report, "objects")
    assert failure["status"] == "failed"
    assert failure["error"]["category"] == "permission"
    assert failure["error"]["stage"] == "inventory"
    assert len(connection.calls) == 8
    assert "senha-ficticia" not in json.dumps(report)
    assert "tabela-privada" not in json.dumps(report)


def test_connection_failure_stops_further_queries_and_preserves_successes() -> None:
    error = DBAPIError(
        "sql-nao-deve-vazar",
        {},
        Exception("08S01", "servidor-privado"),
        connection_invalidated=True,
    )
    connection = FakeConnection(
        {
            ("escopo_a", "objects"): [
                {
                    "schema_name": "escopo_a",
                    "object_name": "objeto_ficticio",
                    "object_type": "table",
                }
            ],
            ("escopo_a", "columns"): error,
        }
    )
    report = collect_inventory(connection, configured_database())
    assert len(connection.calls) == 2
    assert category(report, "objects")["rows"][0]["object_name"] == "objeto_ficticio"
    assert category(report, "columns")["status"] == "failed"
    assert category(report, "keys")["status"] == "not_executed"
    assert category(report, "objects", 1)["status"] == "not_executed"
    assert report["status"] == "partial"
    assert "servidor-privado" not in json.dumps(report)
    assert "sql-nao-deve-vazar" not in json.dumps(report)


def test_inventory_refuses_unconfirmed_configuration_before_executing() -> None:
    connection = FakeConnection()
    with pytest.raises(DatabaseConfigurationError):
        collect_inventory(connection, replace(configured_database(), scope_approved=False))
    assert not connection.calls
