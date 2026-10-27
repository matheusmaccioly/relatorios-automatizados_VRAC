"""Configuração explícita do operador; não procura arquivos ou variáveis privadas."""

import ctypes
import os
import tomllib
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from vrac.db.errors import DatabaseConfigurationError

_PRIVATE_DIRECTORIES = {".git", ".aws", ".agents", ".codex", ".ssh"}
_DATABASE_REQUIRED = {
    "dbms",
    "server",
    "port",
    "database",
    "schemas",
    "driver",
    "auth_mode",
    "sqlserver_confirmed",
    "scope_approved",
}
_DATABASE_OPTIONAL = {
    "connect_timeout_seconds",
    "query_timeout_seconds",
    "metadata_row_limit",
}


def _text(value: object, *, maximum: int = 255) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and len(value) <= maximum
        and all(not unicodedata.category(char).startswith("C") for char in value)
    )


def _integer(value: object, *, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def _windows_drive_type(anchor: str) -> int:
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
    kernel.GetDriveTypeW.restype = wintypes.UINT
    return kernel.GetDriveTypeW(anchor)


def _remote_storage(path: Path) -> bool:
    if path.anchor.startswith("\\\\") or path.as_posix().startswith("//"):
        return True
    return os.name == "nt" and _windows_drive_type(path.anchor) == 4  # DRIVE_REMOTE


@dataclass(frozen=True, slots=True, repr=False)
class DatabaseConfig:
    dbms: str
    server: str
    port: int
    database: str
    schemas: tuple[str, ...]
    driver: str
    auth_mode: str
    sqlserver_confirmed: bool
    scope_approved: bool
    connect_timeout_seconds: int = 10
    query_timeout_seconds: int = 30
    metadata_row_limit: int = 1000
    username: str | None = field(default=None, repr=False)
    password: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return "DatabaseConfig(<configuração privada>)"

    def __post_init__(self) -> None:
        if (
            self.dbms != "mssql"
            or not all(_text(value) for value in (self.server, self.database, self.driver))
            or not _integer(self.port, minimum=1, maximum=65535)
            or type(self.sqlserver_confirmed) is not bool
            or type(self.scope_approved) is not bool
            or not isinstance(self.auth_mode, str)
            or self.auth_mode not in {"windows", "sql_password"}
            or not _integer(self.connect_timeout_seconds, minimum=1, maximum=120)
            or not _integer(self.query_timeout_seconds, minimum=1, maximum=300)
            or not _integer(self.metadata_row_limit, minimum=1, maximum=5000)
            or not isinstance(self.schemas, tuple)
            or not 1 <= len(self.schemas) <= 8
            or not all(_text(schema, maximum=128) for schema in self.schemas)
        ):
            raise DatabaseConfigurationError()
        if len({schema.casefold() for schema in self.schemas}) != len(self.schemas):
            raise DatabaseConfigurationError()
        if self.auth_mode == "windows":
            if self.username not in (None, "") or self.password not in (None, ""):
                raise DatabaseConfigurationError()
        elif not _text(self.username) or not _text(self.password, maximum=4096):
            raise DatabaseConfigurationError()


def assert_ready(config: DatabaseConfig) -> None:
    """Confirmações humanas são pré-condições, nunca inferidas de credenciais."""
    if (
        not isinstance(config, DatabaseConfig)
        or config.dbms != "mssql"
        or config.sqlserver_confirmed is not True
        or config.scope_approved is not True
    ):
        raise DatabaseConfigurationError()


def load_database_config(path: Path, *, workspace: Path) -> DatabaseConfig:
    """Ler somente dbconfig.toml externo indicado explicitamente pelo operador.

    Esta função é usada pelos comandos manuais depois do opt-in de execução.
    O agente testa apenas arquivos temporários fictícios; não deve chamá-la com
    configuração institucional nesta sessão.
    """
    try:
        if not path.is_absolute() or not workspace.is_absolute() or _remote_storage(path):
            raise DatabaseConfigurationError()
        resolved = path.resolve(strict=True)
        project = workspace.resolve(strict=True)
        if (
            _remote_storage(resolved)
            or resolved.name != "dbconfig.toml"
            or resolved.is_relative_to(project)
            or any(part.casefold() in _PRIVATE_DIRECTORIES for part in resolved.parts)
            or not resolved.is_file()
        ):
            raise DatabaseConfigurationError()
        with resolved.open("rb") as source:
            content = source.read(65537)
        if len(content) > 65536:
            raise DatabaseConfigurationError()
        document = tomllib.loads(content.decode("utf-8"))
        if set(document) - {"database", "credentials"}:
            raise DatabaseConfigurationError()
        values = document.get("database")
        credentials = document.get("credentials", {})
        if (
            not isinstance(values, dict)
            or not isinstance(credentials, dict)
            or not _DATABASE_REQUIRED <= set(values)
            or set(values) - (_DATABASE_REQUIRED | _DATABASE_OPTIONAL)
            or set(credentials) - {"username", "password"}
            or not isinstance(values["schemas"], list)
        ):
            raise DatabaseConfigurationError()
        values = dict(values)
        values["schemas"] = tuple(values["schemas"])
        return DatabaseConfig(**values, **credentials)
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, TypeError, ValueError):
        raise DatabaseConfigurationError() from None
