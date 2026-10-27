"""CLI com funções de I/O e banco simuladas; não ler configuração institucional."""

import json
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import pytest

from vrac.db import cli, diagnostic
from vrac.db.config import DatabaseConfig
from vrac.db.errors import DatabaseConfigurationError, DatabaseIssue, DatabaseOperationError
from vrac.db.private_io import PrivateOutputError


@pytest.fixture
def config() -> DatabaseConfig:
    return DatabaseConfig(
        dbms="mssql",
        server="synthetic.invalid",
        port=12345,
        database="synthetic-db",
        schemas=("synthetic",),
        driver="Synthetic Driver",
        auth_mode="windows",
        sqlserver_confirmed=True,
        scope_approved=True,
    )


def test_help_and_missing_opt_in_never_read_config_or_open_database(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loader = Mock(side_effect=AssertionError("Não ler config sem opt-in."))
    monkeypatch.setattr(cli, "load_database_config", loader)
    for command in ("diagnose", "inventory"):
        assert cli.main([command, "--config", "private-path-marker"]) == 2
        with pytest.raises(SystemExit) as exit_info:
            cli.main([command, "--help"])
        assert exit_info.value.code == 0
    loader.assert_not_called()
    assert "private-path-marker" not in capsys.readouterr().out


def test_bad_arguments_do_not_echo_arbitrary_input(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["unknown-sensitive-marker", "--password", "sensitive-marker"]) == 2
    output = capsys.readouterr()
    assert "sensitive-marker" not in output.out + output.err


def test_missing_config_or_unapproved_scope_stops_before_output(
    config: DatabaseConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert cli.main(["diagnose", "--execute"]) == 2
    monkeypatch.setattr(cli, "load_database_config", Mock(side_effect=DatabaseConfigurationError()))
    output = Mock()
    monkeypatch.setattr(cli, "create_private_run_directory", output)
    assert cli.main(["inventory", "--execute", "--config", "unused-marker"]) == 2
    output.assert_not_called()


def test_output_protection_failure_precedes_database_access(
    config: DatabaseConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "load_database_config", lambda *args, **kwargs: config)
    monkeypatch.setattr(
        cli,
        "create_private_run_directory",
        Mock(side_effect=PrivateOutputError("Saída indisponível.")),
    )
    operation = Mock()
    monkeypatch.setattr(diagnostic, "diagnose_database", operation)
    assert cli.main(["diagnose", "--execute", "--config", str(Path.cwd() / "unused")]) == 1
    operation.assert_not_called()


@pytest.mark.parametrize(("status", "code"), [("passed", 0), ("partial", 3), ("failed", 1)])
def test_cli_writes_private_result_without_printing_metadata(
    status: str,
    code: int,
    config: DatabaseConfig,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "load_database_config", lambda *args, **kwargs: config)
    directory = tmp_path / "private-path-marker"
    mkdir = Mock(return_value=directory)
    writer = Mock()
    monkeypatch.setattr(cli, "create_private_run_directory", mkdir)
    monkeypatch.setattr(cli, "write_private_report", writer)
    monkeypatch.setattr(
        cli, "_inventory", lambda config: {"status": status, "database": "physical-name-marker"}
    )
    assert cli.main(["inventory", "--execute", "--config", str(tmp_path / "dbconfig.toml")]) == code
    mkdir.assert_called_once()
    writer.assert_called_once()
    payload = writer.call_args.args[2]
    assert payload["read_privileges_validated_by_code"] is False
    assert payload["started_at"] <= payload["finished_at"]
    assert payload["result"]["database"] == "physical-name-marker"
    output = capsys.readouterr()
    assert "physical-name-marker" not in output.out + output.err
    assert "private-path-marker" not in output.out + output.err


def test_cli_unknown_failure_never_serializes_raw_exception(
    config: DatabaseConfig,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "load_database_config", lambda *args, **kwargs: config)
    monkeypatch.setattr(cli, "create_private_run_directory", lambda *args, **kwargs: tmp_path)
    writer = Mock()
    monkeypatch.setattr(cli, "write_private_report", writer)
    monkeypatch.setattr(cli, "_inventory", Mock(side_effect=RuntimeError("raw-private-marker")))
    assert cli.main(["inventory", "--execute", "--config", str(tmp_path / "dbconfig.toml")]) == 1
    assert "raw-private-marker" not in json.dumps(writer.call_args.args[2])
    output = capsys.readouterr()
    assert "raw-private-marker" not in output.out + output.err


def test_diagnostic_executes_only_select_one_and_closes_result(
    config: DatabaseConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("sqlalchemy")
    result = Mock()
    result.scalar_one.return_value = 1
    connection = Mock()
    connection.execute.return_value = result

    @contextmanager
    def session(config: DatabaseConfig):
        yield connection

    monkeypatch.setattr(diagnostic, "database_session", session)
    report = diagnostic.diagnose_database(config)
    assert report["status"] == "passed"
    assert report["privileges_validated"] is False
    assert str(connection.execute.call_args.args[0]).strip() == "SELECT 1"
    assert connection.execute.call_count == 1
    result.close.assert_called_once()


def test_diagnostic_preserves_sanitized_connection_category(
    config: DatabaseConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issue = DatabaseIssue("certificate", "Falha sanitizada de certificado.", "connection")
    monkeypatch.setattr(
        diagnostic, "database_session", Mock(side_effect=DatabaseOperationError(issue))
    )
    report = diagnostic.diagnose_database(config)
    assert report["status"] == "failed"
    assert report["category"] == "certificate"
    assert report["stage"] == "connection"
