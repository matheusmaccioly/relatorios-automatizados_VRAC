"""Diagnóstico sanitizado, sempre sem conexão durante os testes."""

import pytest

from vrac.dev import synthetic_connection_diagnostic as diagnostic


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("password authentication failed SECRET_VALUE", "AUTENTICACAO"),
        ("SSL certificate verify failed SECRET_VALUE", "CERTIFICADO_OU_TLS"),
        ("connection refused SECRET_VALUE", "SERVIDOR_INDISPONIVEL"),
        ("SECRET_VALUE", "OUTRA_FALHA"),
    ],
)
def test_driver_errors_are_classified_without_including_driver_text(message, expected):
    assert diagnostic.failure_category(Exception(message)) == expected


def test_failure_is_returned_sanitized_without_network(monkeypatch, capsys):
    def fail():
        raise RuntimeError("password authentication failed SECRET_VALUE")

    monkeypatch.setattr(diagnostic.reader, "_connect", fail)
    assert diagnostic.diagnose() == "AUTENTICACAO"
    assert "SECRET_VALUE" not in capsys.readouterr().out
