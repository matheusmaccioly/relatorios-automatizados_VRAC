"""A proteção offline permite IPC interno, mas não conexões de aplicação."""

import socket

import pytest


def test_internal_socketpair_can_exchange_bytes() -> None:
    first, second = socket.socketpair()
    with first, second:
        first.settimeout(1)
        second.settimeout(1)
        first.sendall(b"ipc-local")
        assert second.recv(9) == b"ipc-local"


def test_normal_loopback_and_external_connections_remain_blocked() -> None:
    for address in [("127.0.0.1", 9), ("192.0.2.1", 9)]:
        with socket.socket() as connection:
            for connect in [connection.connect, connection.connect_ex, socket.create_connection]:
                with pytest.raises(pytest.fail.Exception, match="sem conexão de rede"):
                    connect(address)
