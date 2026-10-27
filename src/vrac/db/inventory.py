"""Inventário manual e limitado de metadados; nunca consulta registros acadêmicos."""

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection
from sqlalchemy.sql.elements import TextClause

from vrac.db.config import DatabaseConfig, assert_ready
from vrac.db.errors import classify_database_error

CATALOG_VERSION = "sqlserver-catalog-v1"
VISIBILITY_WARNING = (
    "A cobertura dos metadados é desconhecida: permissões podem ocultar objetos, colunas e "
    "relações. Ausência de linhas não comprova inexistência."
)
STOP_WARNING = "Consulta não executada após falha que pode comprometer a conexão."


@dataclass(frozen=True)
class _Category:
    name: str
    columns: tuple[str, ...]
    expanding_schemas: bool = False


_CATEGORIES = (
    _Category("objects", ("schema_name", "object_name", "object_type")),
    _Category(
        "columns",
        (
            "schema_name",
            "object_name",
            "column_name",
            "column_ordinal",
            "data_type",
            "data_type_schema",
            "base_data_type",
            "max_length_bytes",
            "numeric_precision",
            "numeric_scale",
            "is_nullable",
            "is_identity",
        ),
        expanding_schemas=True,
    ),
    _Category(
        "keys",
        (
            "schema_name",
            "object_name",
            "constraint_name",
            "constraint_type",
            "column_name",
            "key_ordinal",
        ),
    ),
    _Category(
        "foreign_keys",
        (
            "source_schema",
            "source_table",
            "source_column",
            "constraint_name",
            "column_ordinal",
            "target_schema",
            "target_table",
            "target_column",
            "is_disabled",
            "is_not_trusted",
        ),
        expanding_schemas=True,
    ),
)


def _catalog_statement(category: _Category) -> TextClause:
    """Carregar somente arquivos da lista fechada, no checkout ou wheel instalado."""
    filename = f"{category.name}.sql"
    checkout_path = Path(__file__).resolve().parents[3] / "sql" / "catalog" / filename
    if checkout_path.is_file():
        query = checkout_path.read_text(encoding="utf-8")
    else:
        query = files("vrac").joinpath("sql", "catalog", filename).read_text(encoding="utf-8")
    statement = text(query)
    if category.expanding_schemas:
        statement = statement.bindparams(bindparam("allowed_schemas", expanding=True))
    return statement


def _unavailable_category(status: str, warning: str) -> dict[str, Any]:
    return {
        "status": status,
        "coverage": "unknown",
        "truncated": False,
        "rows": [],
        "warnings": [warning],
    }


def _normalize_rows(
    category: _Category,
    rows: list[Mapping[str, Any]],
    *,
    schema: str,
    allowed_schemas: tuple[str, ...],
    row_limit: int,
) -> dict[str, Any]:
    truncated = len(rows) > row_limit
    warnings: list[str] = []
    selected: list[dict[str, Any]] = []
    rejected = False
    for row in rows[:row_limit]:
        if category.name == "foreign_keys":
            in_scope = (
                row.get("source_schema") == schema and row.get("target_schema") in allowed_schemas
            )
        else:
            in_scope = row.get("schema_name") == schema
        if not in_scope:
            rejected = True
            continue
        normalized = {name: row.get(name) for name in category.columns}
        if category.name == "columns" and normalized.get("data_type_schema") not in (
            None,
            "sys",
            *allowed_schemas,
        ):
            normalized["data_type_schema"] = None
            normalized["data_type"] = None
            rejected = True
        # Os campos selecionados no catálogo são apenas strings, inteiros e bits.
        # Um retorno inesperado não deve serializar objetos ou conteúdo adicional.
        for name, value in normalized.items():
            if value is not None and not isinstance(value, (str, int, float, bool)):
                normalized[name] = None
                rejected = True
        selected.append(normalized)
    if truncated:
        warnings.append("Limite de metadados atingido; a categoria foi truncada.")
    if rejected:
        warnings.append("Metadados inesperados ou fora do escopo foram omitidos.")
    if not selected:
        warnings.append("Nenhum metadado visível; a existência permanece desconhecida.")
    return {
        "status": "partial" if warnings else "valid",
        "coverage": "unknown",
        "truncated": truncated,
        "rows": selected,
        "warnings": warnings,
    }


def _aggregate_status(categories: list[dict[str, Any]]) -> str:
    statuses = [category["status"] for category in categories]
    if all(status in {"failed", "not_executed"} for status in statuses):
        return "failed"
    return "valid" if all(status == "valid" for status in statuses) else "partial"


def collect_inventory(connection: Connection, config: DatabaseConfig) -> dict[str, Any]:
    """Consultar até quatro categorias por schema na conexão criada para este config.

    O chamador deve criar a conexão a partir da configuração aprovada e descartá-la
    ao terminar. O catálogo usa apenas o banco atual dessa conexão, sem USE,
    enumeração de bancos ou reflexão automática. A saída contém metadados físicos
    privados: não enviá-la ao agente sem sanitização e autorização humanas.
    """
    assert_ready(config)
    schemas: list[dict[str, Any]] = []
    categories: list[dict[str, Any]] = []
    stop = False
    queries_executed = 0
    fetch_limit = config.metadata_row_limit + 1
    for schema in config.schemas:
        schema_categories: dict[str, dict[str, Any]] = {}
        for category in _CATEGORIES:
            if stop:
                result_data = _unavailable_category("not_executed", STOP_WARNING)
            else:
                try:
                    statement = _catalog_statement(category)
                    parameters: dict[str, Any] = {"schema": schema, "row_limit": fetch_limit}
                    if category.expanding_schemas:
                        parameters["allowed_schemas"] = config.schemas
                    queries_executed += 1
                    result = connection.execute(statement, parameters)
                    try:
                        rows = list(result.mappings().fetchmany(fetch_limit))
                    finally:
                        result.close()
                    result_data = _normalize_rows(
                        category,
                        rows,
                        schema=schema,
                        allowed_schemas=config.schemas,
                        row_limit=config.metadata_row_limit,
                    )
                except Exception as error:
                    issue = classify_database_error(error, stage="inventory")
                    result_data = _unavailable_category(
                        "failed",
                        "Falha ao consultar esta categoria; os demais resultados são parciais.",
                    )
                    result_data["error"] = asdict(issue)
                    stop = (
                        issue.category
                        in {
                            "network",
                            "certificate",
                            "authentication",
                            "driver",
                            "dependency",
                            "configuration",
                            "timeout",
                        }
                        or getattr(error, "connection_invalidated", False) is True
                        or getattr(connection, "invalidated", False) is True
                        or getattr(connection, "closed", False) is True
                    )
            schema_categories[category.name] = result_data
            categories.append(result_data)
        schemas.append(
            {
                "schema": schema,
                "status": _aggregate_status(list(schema_categories.values())),
                "coverage": "unknown",
                "categories": schema_categories,
            }
        )
    return {
        "catalog_version": CATALOG_VERSION,
        "database": config.database,
        "status": _aggregate_status(categories),
        "coverage": "unknown",
        "warnings": [VISIBILITY_WARNING],
        "limits": {
            "rows_per_category_per_schema": config.metadata_row_limit,
            "max_queries": len(config.schemas) * len(_CATEGORIES),
            "queries_executed": queries_executed,
        },
        "units": {"max_length_bytes": "bytes; -1 indica comprimento máximo"},
        "schemas": schemas,
    }
