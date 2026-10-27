"""Prova de conexão mínima; nunca retorna identidade, SQL ou mensagens brutas."""

from dataclasses import asdict
from importlib.resources import files
from pathlib import Path

from vrac.db.config import DatabaseConfig, assert_ready
from vrac.db.connection import database_session
from vrac.db.errors import DatabaseOperationError, classify_database_error


def diagnose_database(config: DatabaseConfig) -> dict[str, object]:
    assert_ready(config)
    try:
        with database_session(config) as connection:
            from sqlalchemy import text

            probe = (
                Path(__file__).resolve().parents[3] / "sql" / "diagnostics" / "connection_probe.sql"
            )
            query = (
                probe.read_text(encoding="utf-8")
                if probe.is_file()
                else files("vrac")
                .joinpath("sql", "diagnostics", "connection_probe.sql")
                .read_text(encoding="utf-8")
            )
            result = connection.execute(text(query))
            try:
                verified = result.scalar_one() == 1
            finally:
                result.close()
            if not verified:
                return {
                    "status": "failed",
                    "category": "unknown",
                    "stage": "query",
                    "message": "A prova de conexão não retornou o valor esperado.",
                }
    except DatabaseOperationError as error:
        return {"status": "failed", **asdict(error.issue)}
    except Exception as error:
        return {"status": "failed", **asdict(classify_database_error(error, stage="query"))}
    return {
        "status": "passed",
        "category": "connection",
        "stage": "query",
        "message": "Prova de conexão concluída. Fontes e privilégios ainda exigem revisão do DBA.",
        "privileges_validated": False,
        "inventory_validated": False,
    }
