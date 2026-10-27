"""Adaptador SQL Server opt-in, sem conexão durante importação ou criação do engine."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from vrac.db.config import DatabaseConfig, assert_ready
from vrac.db.errors import (
    DatabaseConfigurationError,
    DatabaseOperationError,
    classify_database_error,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection, Engine


def _load_sqlserver_dependencies() -> tuple[Any, Any, Any, Any, Any]:
    """Importação tardia mantém a demonstração independente do extra sqlserver."""
    import pyodbc
    from sqlalchemy import create_engine, event
    from sqlalchemy.engine import URL
    from sqlalchemy.pool import NullPool

    return pyodbc, create_engine, event, URL, NullPool


def _odbc_value(value: str) -> str:
    # ODBC delimita valores com chaves; uma chave de fechamento literal é duplicada.
    return "{" + value.replace("}", "}}") + "}"


def _connection_string(config: DatabaseConfig) -> str:
    fields = [
        "DRIVER=" + _odbc_value(config.driver),
        "SERVER=" + _odbc_value(f"tcp:{config.server},{config.port}"),
        "DATABASE=" + _odbc_value(config.database),
        "Encrypt=yes",
        "TrustServerCertificate=no",
        # É uma intenção de roteamento, não comprova nem restringe privilégios.
        "ApplicationIntent=ReadOnly",
    ]
    if config.auth_mode == "windows":
        fields.append("Trusted_Connection=yes")
    else:
        fields.extend(
            [
                "UID=" + _odbc_value(config.username),
                "PWD=" + _odbc_value(config.password),
            ]
        )
    return ";".join(fields) + ";"


def _close_without_overriding(resource: Any, method: str) -> Exception | None:
    try:
        getattr(resource, method)()
    except Exception as error:
        return error
    return None


def _prepare_private_logging() -> str:
    """Erros de reset/close do pool podem conter detalhes mesmo com echo=False.

    Reservar loggers exclusivos antes de criar o engine evita emissão bruta da
    biblioteca. Não alterar loggers do aplicativo ou de outros engines. Eles
    continuam desabilitados após dispose, inclusive durante finalizadores.
    """
    name = "vrac_private_" + uuid4().hex
    for namespace in ("sqlalchemy.engine.Engine", "sqlalchemy.pool.impl.NullPool"):
        logger = logging.getLogger(f"{namespace}.{name}")
        logger.disabled = True
        logger.propagate = False
    return name


def create_database_engine(config: DatabaseConfig) -> Engine:
    """Preparar um engine privado; o chamador não deve imprimir o engine ou sua URL."""
    assert_ready(config)
    engine = None
    try:
        pyodbc, create_engine, event, url_class, null_pool = _load_sqlserver_dependencies()
        # pyodbc controla seu pool global antes de criar qualquer conexão.
        pyodbc.pooling = False
        url = url_class.create("mssql+pyodbc", query={"odbc_connect": _connection_string(config)})
        private_logging_name = _prepare_private_logging()
        engine = create_engine(
            url,
            poolclass=null_pool,
            connect_args={"timeout": config.connect_timeout_seconds},
            echo=False,
            echo_pool=False,
            hide_parameters=True,
            logging_name=private_logging_name,
            pool_logging_name=private_logging_name,
        )

        def set_query_timeout(dbapi_connection: Any, connection_record: Any) -> None:
            dbapi_connection.timeout = config.query_timeout_seconds

        def connect_with_timeout(
            dialect: Any, connection_record: Any, args: list[Any], parameters: dict[str, Any]
        ) -> Any:
            connection = pyodbc.connect(*args, **parameters)
            try:
                # Antes de first_connect e das consultas de inicialização do dialeto.
                connection.timeout = config.query_timeout_seconds
            except Exception:
                _close_without_overriding(connection, "close")
                raise
            return connection

        event.listen(engine, "do_connect", connect_with_timeout)
        event.listen(engine, "connect", set_query_timeout, insert=True)
        return engine
    except Exception as error:
        if engine is not None:
            _close_without_overriding(engine, "dispose")
        raise DatabaseOperationError(classify_database_error(error, stage="connection")) from None


@contextmanager
def database_session(config: DatabaseConfig) -> Iterator[Connection]:
    """Fechar conexão e engine inclusive quando conexão, consulta ou limpeza falham."""
    engine = None
    connection = None
    stage = "connection"
    primary_failure = False
    try:
        engine = create_database_engine(config)
        connection = engine.connect()
        stage = "query"
        yield connection
    except BaseException as error:
        primary_failure = True
        if isinstance(error, (DatabaseOperationError, DatabaseConfigurationError)):
            raise
        if isinstance(error, Exception):
            raise DatabaseOperationError(classify_database_error(error, stage=stage)) from None
        raise
    finally:
        cleanup_error = None
        if connection is not None:
            cleanup_error = _close_without_overriding(connection, "close")
        if engine is not None:
            dispose_error = _close_without_overriding(engine, "dispose")
            if cleanup_error is None:
                cleanup_error = dispose_error
        if cleanup_error is not None and not primary_failure:
            raise DatabaseOperationError(
                classify_database_error(cleanup_error, stage="connection")
            ) from None
