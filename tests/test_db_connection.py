"""Contrato de conexão e falhas usando somente DBAPI e engines simulados."""

import logging
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from vrac.db import connection
from vrac.db.config import DatabaseConfig
from vrac.db.errors import (
    DatabaseConfigurationError,
    DatabaseOperationError,
    classify_database_error,
)


@pytest.fixture
def config() -> DatabaseConfig:
    return DatabaseConfig(
        dbms="mssql",
        server="synthetic.example.invalid",
        port=1444,
        database="synthetic_database",
        schemas=("synthetic_schema",),
        driver="Synthetic ODBC driver",
        auth_mode="windows",
        sqlserver_confirmed=True,
        scope_approved=True,
        connect_timeout_seconds=11,
        query_timeout_seconds=41,
    )


@pytest.fixture
def adapter(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    engine = Mock()
    dbapi = SimpleNamespace(pooling=True, connect=Mock(), drivers=Mock())
    factory = Mock(return_value=engine)
    url_class = SimpleNamespace(create=Mock(return_value=object()))
    events = SimpleNamespace(listen=Mock())
    pool = object()
    dependencies = Mock(return_value=(dbapi, factory, events, url_class, pool))
    monkeypatch.setattr(connection, "_load_sqlserver_dependencies", dependencies)
    return SimpleNamespace(
        engine=engine,
        dbapi=dbapi,
        factory=factory,
        url=url_class,
        events=events,
        pool=pool,
        dependencies=dependencies,
    )


def test_engine_is_lazy_tls_bound_and_has_no_pool(config: DatabaseConfig, adapter: SimpleNamespace):
    def create_engine(*args: object, **kwargs: object) -> Mock:
        assert adapter.dbapi.pooling is False
        return adapter.engine

    adapter.factory.side_effect = create_engine
    assert connection.create_database_engine(config) is adapter.engine
    adapter.dbapi.connect.assert_not_called()
    adapter.dbapi.drivers.assert_not_called()
    adapter.engine.connect.assert_not_called()
    options = adapter.factory.call_args.kwargs
    assert {key: value for key, value in options.items() if not key.endswith("logging_name")} == {
        "poolclass": adapter.pool,
        "connect_args": {"timeout": 11},
        "echo": False,
        "echo_pool": False,
        "hide_parameters": True,
    }
    assert options["logging_name"] == options["pool_logging_name"]
    assert options["logging_name"].startswith("vrac_private_")
    assert config.server not in options["logging_name"]
    odbc = adapter.url.create.call_args.kwargs["query"]["odbc_connect"]
    assert "Encrypt=yes;TrustServerCertificate=no;ApplicationIntent=ReadOnly;" in odbc
    assert "SERVER={tcp:synthetic.example.invalid,1444};" in odbc
    assert odbc.endswith("Trusted_Connection=yes;")


def _odbc_fields(text: str) -> dict[str, str]:
    """Decodificador de teste para validar o limite de cada valor ODBC."""
    fields: dict[str, str] = {}
    position = 0
    while position < len(text):
        equals = text.index("=", position)
        key = text[position:equals]
        position = equals + 1
        characters: list[str] = []
        if text[position] == "{":
            position += 1
            while True:
                if text[position] != "}":
                    characters.append(text[position])
                    position += 1
                elif text[position + 1 : position + 2] == "}":
                    characters.append("}")
                    position += 2
                else:
                    position += 1
                    break
        else:
            while text[position] != ";":
                characters.append(text[position])
                position += 1
        assert text[position] == ";"
        position += 1
        assert key not in fields
        fields[key] = "".join(characters)
    return fields


def test_odbc_metacharacters_round_trip_without_adding_options(
    config: DatabaseConfig, adapter: SimpleNamespace
) -> None:
    attack = "literal};Encrypt=no;TrustServerCertificate=yes;{= tail }"
    config = replace(
        config,
        auth_mode="sql_password",
        server=attack,
        database=attack,
        driver=attack,
        username=attack,
        password="  " + attack + "  ",
    )
    connection.create_database_engine(config)
    raw = adapter.url.create.call_args.kwargs["query"]["odbc_connect"]
    values = _odbc_fields(raw)
    assert values == {
        "DRIVER": attack,
        "SERVER": f"tcp:{attack},1444",
        "DATABASE": attack,
        "Encrypt": "yes",
        "TrustServerCertificate": "no",
        "ApplicationIntent": "ReadOnly",
        "UID": attack,
        "PWD": "  " + attack + "  ",
    }


def test_login_and_query_timeout_apply_before_initial_queries(
    config: DatabaseConfig, adapter: SimpleNamespace
) -> None:
    connection.create_database_engine(config)
    hooks = {call.args[1]: call.args[2] for call in adapter.events.listen.call_args_list}
    raw = SimpleNamespace(timeout=0)
    adapter.dbapi.connect.return_value = raw
    result = hooks["do_connect"](None, None, ["private_odbc"], {"timeout": 11})
    adapter.dbapi.connect.assert_called_once_with("private_odbc", timeout=11)
    # first_connect/initialização do dialeto só recebe a conexão depois deste retorno.
    assert result.timeout == 41
    result.timeout = 0
    hooks["connect"](result, None)
    assert result.timeout == 41
    assert adapter.events.listen.call_args.kwargs == {"insert": True}


def test_query_timeout_setter_failure_closes_dbapi_connection(
    config: DatabaseConfig, adapter: SimpleNamespace
) -> None:
    class BrokenTimeout:
        close = Mock()

        @property
        def timeout(self) -> int:
            return 0

        @timeout.setter
        def timeout(self, value: int) -> None:
            raise RuntimeError("private failure")

    connection.create_database_engine(config)
    hook = adapter.events.listen.call_args_list[0].args[2]
    raw = BrokenTimeout()
    raw.close.side_effect = RuntimeError("private cleanup failure")
    adapter.dbapi.connect.return_value = raw
    with pytest.raises(RuntimeError, match="private failure"):
        hook(None, None, [], {"timeout": 11})
    raw.close.assert_called_once()


def test_unapproved_configuration_does_not_import_optional_dependencies(
    config: DatabaseConfig, adapter: SimpleNamespace
) -> None:
    with pytest.raises(DatabaseConfigurationError):
        connection.create_database_engine(replace(config, scope_approved=False))
    adapter.dependencies.assert_not_called()


def test_missing_optional_dependencies_have_safe_messages(
    config: DatabaseConfig, adapter: SimpleNamespace
) -> None:
    adapter.dependencies.side_effect = ModuleNotFoundError("secret host and driver path")
    with pytest.raises(DatabaseOperationError) as caught:
        connection.create_database_engine(config)
    assert caught.value.issue.category == "dependency"
    assert "secret" not in str(caught.value)
    assert caught.value.__suppress_context__


def test_event_registration_failure_disposes_engine_and_sanitizes(
    config: DatabaseConfig, adapter: SimpleNamespace
) -> None:
    adapter.events.listen.side_effect = RuntimeError("private registration details")
    adapter.engine.dispose.side_effect = RuntimeError("private dispose details")
    with pytest.raises(DatabaseOperationError) as caught:
        connection.create_database_engine(config)
    adapter.engine.dispose.assert_called_once()
    assert "private" not in str(caught.value)


def test_session_closes_connection_and_disposes_engine(
    config: DatabaseConfig, adapter: SimpleNamespace
) -> None:
    with connection.database_session(config) as session:
        assert session is adapter.engine.connect.return_value
    session.close.assert_called_once()
    adapter.engine.dispose.assert_called_once()


@pytest.mark.parametrize("stage", ["connection", "query"])
def test_primary_failure_survives_cleanup_failures(
    config: DatabaseConfig, adapter: SimpleNamespace, stage: str
) -> None:
    error = RuntimeError("28000", "[28000] synthetic credentials rejected (18456)")
    if stage == "connection":
        adapter.engine.connect.side_effect = error
    session = adapter.engine.connect.return_value
    session.close.side_effect = RuntimeError("private close details")
    adapter.engine.dispose.side_effect = RuntimeError("private dispose details")
    with pytest.raises(DatabaseOperationError) as caught, connection.database_session(config):
        raise error
    assert caught.value.issue.category == "authentication"
    assert caught.value.issue.stage == stage
    adapter.engine.dispose.assert_called_once()
    assert "private" not in str(caught.value)
    if stage == "query":
        session.close.assert_called_once()


def test_cleanup_failure_after_success_is_reported_safely(
    config: DatabaseConfig, adapter: SimpleNamespace
) -> None:
    adapter.engine.connect.return_value.close.side_effect = RuntimeError("private close details")
    with pytest.raises(DatabaseOperationError) as caught, connection.database_session(config):
        pass
    assert caught.value.issue.category == "unknown"
    assert "private" not in str(caught.value)
    adapter.engine.dispose.assert_called_once()


def test_keyboard_interrupt_is_preserved_while_resources_are_closed(
    config: DatabaseConfig, adapter: SimpleNamespace
) -> None:
    adapter.engine.dispose.side_effect = RuntimeError("private cleanup details")
    with pytest.raises(KeyboardInterrupt), connection.database_session(config):
        raise KeyboardInterrupt()
    adapter.engine.connect.return_value.close.assert_called_once()
    adapter.engine.dispose.assert_called_once()


@pytest.mark.parametrize(
    ("error", "category"),
    [
        (DatabaseConfigurationError(), "configuration"),
        (ImportError("private module location"), "dependency"),
        (RuntimeError("IM002", "private driver location"), "driver"),
        (RuntimeError("01000", "Can't open lib private path"), "driver"),
        (RuntimeError("08001", "private endpoint"), "network"),
        (RuntimeError("08001", "SSL Provider: certificate chain private subject"), "certificate"),
        (RuntimeError("08001", "private (-2146893019)"), "certificate"),
        (RuntimeError("28000", "private account (18456)"), "authentication"),
        (RuntimeError("42000", "private database (4060)"), "permission"),
        (RuntimeError("42000", "private object (229)"), "permission"),
        (RuntimeError("42501", "private scope"), "permission"),
        (RuntimeError("HYT00", "private timeout details"), "timeout"),
        (RuntimeError("HYT01", "private timeout details"), "timeout"),
        (TimeoutError("private endpoint"), "timeout"),
        (RuntimeError("42000", "private query syntax"), "unknown"),
    ],
)
def test_error_classification_returns_only_fixed_safe_text(error: Exception, category: str) -> None:
    issue = classify_database_error(error, stage="inventory")
    assert issue.category == category
    assert issue.stage == "inventory"
    assert "private" not in repr(issue)


def test_sqlalchemy_wrappers_and_untrusted_stages_do_not_expose_exception_text() -> None:
    class NoStringError(Exception):
        def __str__(self) -> str:
            pytest.fail("A classificação não deve formatar exceções privadas.")

    wrapper = NoStringError("private SQL and parameters")
    wrapper.orig = NoStringError("42000", "[42000] private table denied (229)")
    issue = classify_database_error(wrapper, stage="private stage")
    assert issue.category == "permission"
    assert issue.stage == "operation"
    assert "private" not in repr(issue)


def test_library_reset_and_close_failures_do_not_emit_raw_logs(
    config: DatabaseConfig, caplog: pytest.LogCaptureFixture
) -> None:
    pytest.importorskip("sqlalchemy")
    pytest.importorskip("pyodbc")
    from sqlalchemy.pool import NullPool

    application_logger = logging.getLogger("vrac.application.synthetic_test")
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    initial_state = [
        (logger.disabled, logger.propagate) for logger in (application_logger, sqlalchemy_logger)
    ]
    engines = [connection.create_database_engine(config), connection.create_database_engine(config)]
    pools = []
    try:
        assert engines[0].logging_name != engines[1].logging_name
        for engine in engines:
            assert engine.logger.disabled
            assert not engine.logger.propagate
            assert engine.pool.logger.disabled
            assert not engine.pool.logger.propagate
            raw = Mock()
            raw.rollback.side_effect = RuntimeError("synthetic_private_reset_marker")
            raw.close.side_effect = RuntimeError("synthetic_private_close_marker")
            # Pool da própria biblioteca com o mesmo logger dedicado e DBAPI fictícia.
            # Não usa Engine.connect, pyodbc.connect/drivers ou consultas.
            pool = NullPool(creator=lambda raw=raw: raw, logging_name=engine.pool.logging_name)
            pools.append(pool)
            with caplog.at_level(logging.DEBUG, logger="sqlalchemy"):
                handle = pool.connect()
                handle.close()
            raw.rollback.assert_called_once()
            raw.close.assert_called_once()
        assert not [record for record in caplog.records if record.name.startswith("sqlalchemy")]
        assert "synthetic_private" not in caplog.text
    finally:
        for pool in pools:
            pool.dispose()
        for engine in engines:
            engine.dispose()
    assert initial_state == [
        (logger.disabled, logger.propagate) for logger in (application_logger, sqlalchemy_logger)
    ]
    assert all(engine.logger.disabled and engine.pool.logger.disabled for engine in engines)
