"""Suíte sintética: ambiente público controlado e rede proibida."""

import socket
from contextvars import ContextVar
from importlib.util import find_spec

import pytest


@pytest.fixture(autouse=True)
def offline_environment(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    monkeypatch.delenv("VRAC_ENVIRONMENT", raising=False)
    monkeypatch.delenv("VRAC_DATA_MODE", raising=False)
    monkeypatch.setenv("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    if (
        request.node.get_closest_marker("integration")
        and request.config.getoption("--run-db-integration")
        and request.config.getoption("--db-config")
    ):
        return  # somente execução manual explícita fora da sessão do agente

    def deny_network(*args: object, **kwargs: object) -> None:
        pytest.fail("A suíte padrão deve funcionar sem conexão de rede.")

    # No Windows, asyncio usa socketpair como canal interno entre threads.
    # A exceção existe somente dentro da implementação original de socketpair;
    # uma conexão normal de loopback continua proibida.
    in_socketpair = ContextVar("internal_socketpair_connect", default=False)
    original_connect = socket.socket.connect
    original_socketpair = socket.socketpair

    def guarded_connect(connection: socket.socket, address: object) -> None:
        if not (
            in_socketpair.get()
            and isinstance(address, tuple)
            and address[0] in {"127.0.0.1", "::1"}
        ):
            deny_network()
        original_connect(connection, address)

    def internal_socketpair(*args: object, **kwargs: object) -> tuple[socket.socket, socket.socket]:
        token = in_socketpair.set(True)
        try:
            return original_socketpair(*args, **kwargs)
        finally:
            in_socketpair.reset(token)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket, "socketpair", internal_socketpair)

    # Drivers nativos não passam pelo socket Python. Bloquear também esses acessos.
    if find_spec("pyodbc") is not None:
        import pyodbc

        monkeypatch.setattr(pyodbc, "connect", deny_network)
        monkeypatch.setattr(pyodbc, "drivers", deny_network)
    if find_spec("sqlalchemy") is not None:
        from sqlalchemy.engine import Engine

        monkeypatch.setattr(Engine, "connect", deny_network)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("vrac-manual-integration")
    group.addoption("--run-db-integration", action="store_true", default=False)
    group.addoption(
        "--db-config", default=None, help="Configuração externa: somente operador autorizado."
    )
