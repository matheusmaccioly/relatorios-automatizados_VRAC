"""Configurações exclusivamente fictícias em diretórios temporários."""

import os
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from vrac.db import config as database_config
from vrac.db.config import DatabaseConfig, assert_ready, load_database_config
from vrac.db.errors import DatabaseConfigurationError


def _config() -> DatabaseConfig:
    return DatabaseConfig(
        dbms="mssql",
        server="synthetic.example.invalid",
        port=1444,
        database="synthetic_database",
        schemas=("synthetic_schema",),
        driver="Synthetic ODBC driver",
        auth_mode="windows",
        sqlserver_confirmed=False,
        scope_approved=False,
    )


_TEMPLATE = """[database]
dbms = "mssql"
server = "synthetic.example.invalid"
port = 1444
database = "synthetic_database"
schemas = ["synthetic_schema"]
driver = "Synthetic ODBC driver"
auth_mode = "windows"
sqlserver_confirmed = false
scope_approved = false
"""


@pytest.fixture
def external_config(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    private = tmp_path / "operator"
    private.mkdir()
    path = private / "dbconfig.toml"
    path.write_text(_TEMPLATE, encoding="utf-8")
    return path, workspace


def test_explicit_external_config_remains_blocked_until_both_confirmations(
    external_config: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    path, workspace = external_config
    monkeypatch.setenv("VRAC_DB_SERVER", "must_not_be_read")
    config = load_database_config(path, workspace=workspace)
    assert config == _config()
    for confirmed, approved in [(False, False), (True, False), (False, True)]:
        with pytest.raises(DatabaseConfigurationError):
            assert_ready(replace(config, sqlserver_confirmed=confirmed, scope_approved=approved))
    assert_ready(replace(config, sqlserver_confirmed=True, scope_approved=True))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dbms", "postgresql"),
        ("server", ""),
        ("server", "server\nidentity"),
        ("database", " "),
        ("driver", "driver\x00"),
        ("port", True),
        ("port", 0),
        ("port", 65536),
        ("sqlserver_confirmed", 1),
        ("scope_approved", "true"),
        ("auth_mode", "automatic"),
        ("auth_mode", []),
        ("connect_timeout_seconds", False),
        ("connect_timeout_seconds", 121),
        ("query_timeout_seconds", 0),
        ("query_timeout_seconds", 301),
        ("metadata_row_limit", True),
        ("metadata_row_limit", 5001),
        ("schemas", ()),
        ("schemas", ("Synthetic", "synthetic")),
        ("schemas", ("schema\r",)),
        ("schemas", ["synthetic_schema"]),
        ("schemas", tuple(f"schema_{index}" for index in range(9))),
    ],
)
def test_invalid_configuration_has_one_fixed_safe_error(field: str, value: object) -> None:
    with pytest.raises(DatabaseConfigurationError) as caught:
        replace(_config(), **{field: value})
    assert str(caught.value) == str(DatabaseConfigurationError())


def test_sql_credentials_required_windows_ignores_only_empty_fields() -> None:
    assert replace(_config(), username="", password="").auth_mode == "windows"
    with pytest.raises(DatabaseConfigurationError):
        replace(_config(), username="synthetic_user")
    with pytest.raises(DatabaseConfigurationError):
        replace(_config(), auth_mode="sql_password", username="synthetic_user")
    config = replace(
        _config(), auth_mode="sql_password", username="synthetic_user", password="} ;= password"
    )
    assert config.password == "} ;= password"
    rendered = repr(config)
    for private_value in [
        config.server,
        config.database,
        config.schemas[0],
        config.username,
        config.password,
        config.driver,
    ]:
        assert private_value not in rendered


@pytest.mark.parametrize("private_directory", [".git", ".aws", ".agents", ".codex", ".ssh"])
def test_configuration_in_workspace_or_restricted_directory_is_not_read(
    external_config: tuple[Path, Path], private_directory: str
) -> None:
    external, workspace = external_config
    for directory in [workspace, external.parent / private_directory]:
        directory.mkdir(exist_ok=True)
        path = directory / "dbconfig.toml"
        path.write_text("this is deliberately invalid TOML", encoding="utf-8")
        with pytest.raises(DatabaseConfigurationError):
            load_database_config(path, workspace=workspace)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda content: content.replace("port = 1444\n", ""),
        lambda content: content.replace('auth_mode = "windows"\n', ""),
        lambda content: content.replace('driver = "Synthetic ODBC driver"\n', ""),
        lambda content: content + "TrustServerCertificate = true\n",
        lambda content: content + "[unknown]\noption = true\n",
        lambda content: content + '[credentials]\nunknown = "private"\n',
        lambda content: content.replace("port = 1444", "port = true"),
        lambda content: "broken = [",
    ],
)
def test_missing_malformed_or_unknown_configuration_never_defaults_silently(
    external_config: tuple[Path, Path], mutation: object
) -> None:
    path, workspace = external_config
    path.write_text(mutation(_TEMPLATE), encoding="utf-8")
    with pytest.raises(DatabaseConfigurationError) as caught:
        load_database_config(path, workspace=workspace)
    assert caught.value.__suppress_context__


def test_only_explicit_external_dbconfig_name_and_bounded_content_are_loaded(
    external_config: tuple[Path, Path],
) -> None:
    path, workspace = external_config
    for candidate in [
        Path("dbconfig.toml"),
        path.parent / "missing.toml",
        path.parent / ".env",
        path.parent / "secrets.toml",
    ]:
        with pytest.raises(DatabaseConfigurationError):
            load_database_config(candidate, workspace=workspace)
    path.write_bytes(b"x" * 65537)
    with pytest.raises(DatabaseConfigurationError):
        load_database_config(path, workspace=workspace)


def test_external_loader_accepts_sql_credentials_without_printing_them(
    external_config: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    path, workspace = external_config
    path.write_text(
        _TEMPLATE.replace('auth_mode = "windows"', 'auth_mode = "sql_password"')
        + '[credentials]\nusername = "synthetic_user"\npassword = "} ;= password"\n',
        encoding="utf-8",
    )
    config = load_database_config(path, workspace=workspace)
    assert config.password == "} ;= password"
    assert capsys.readouterr().out == ""


@pytest.mark.skipif(os.name != "nt", reason="Resolução de caminhos UNC é específica do Windows.")
def test_local_path_resolving_to_unc_is_rejected_before_read(
    external_config: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    path, workspace = external_config
    original_resolve = Path.resolve

    def resolve(candidate: Path, *args: object, **kwargs: object) -> Path:
        if candidate == path:
            return Path(r"\\synthetic.invalid\share\dbconfig.toml")
        return original_resolve(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    read = Mock(side_effect=AssertionError("Não ler configuração remota."))
    monkeypatch.setattr(Path, "open", read)
    with pytest.raises(DatabaseConfigurationError):
        load_database_config(path, workspace=workspace)
    read.assert_not_called()


@pytest.mark.skipif(os.name != "nt", reason="DriveType é específico do Windows.")
def test_mapped_remote_drive_is_rejected_before_read(
    external_config: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    path, workspace = external_config
    monkeypatch.setattr(database_config, "_windows_drive_type", lambda anchor: 4)
    read = Mock(side_effect=AssertionError("Não ler unidade de rede mapeada."))
    monkeypatch.setattr(Path, "open", read)
    with pytest.raises(DatabaseConfigurationError):
        load_database_config(path, workspace=workspace)
    read.assert_not_called()
