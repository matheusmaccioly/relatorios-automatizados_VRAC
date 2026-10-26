"""Suíte sintética: ambiente público controlado e rede proibida."""

import socket
from contextvars import ContextVar

import pytest


@pytest.fixture(autouse=True)
def offline_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VRAC_ENVIRONMENT", raising=False)
    monkeypatch.delenv("VRAC_DATA_MODE", raising=False)
    monkeypatch.setenv("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

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
