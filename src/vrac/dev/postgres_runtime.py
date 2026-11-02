"""Executar exclusivamente um PostgreSQL portátil sintético em loopback.

Sem instalação de serviço, sem acesso à configuração institucional e sem leitura
de credenciais existentes. Credenciais novas ficam no diretório temporário privado.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import tempfile
from pathlib import Path

from vrac.dev.semantic_postgres import DATABASE, SCHEMA, VERSION

ADMIN = "vrac_sintetico_admin"
READER = "vrac_sintetico_reader"
PORT = 55432


class RuntimeErrorSafe(RuntimeError):
    """Erro sem senhas, strings de conexão ou stderr potencialmente sensível."""


def runtime_directory(project: Path) -> Path:
    tag = hashlib.sha256(str(project.resolve()).encode("utf-8")).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / f"vrac-synthetic-postgres-{tag}"


def _run(arguments: list[str], *, env: dict[str, str], input_text: str | None = None) -> str:
    try:
        # pg_ctl pode deixar descendentes com os handles herdados no Windows.
        # Arquivos temporários evitam esperar EOF de pipes mantidos pelo servidor.
        with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
            result = subprocess.run(
                arguments,
                input=input_text,
                stdout=stdout_file,
                stderr=stderr_file,
                encoding="utf-8",
                env=env,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            stdout_file.seek(0)
            output = stdout_file.read().decode("utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeErrorSafe("Não foi possível executar a ferramenta PostgreSQL local.") from exc
    if result.returncode:
        raise RuntimeErrorSafe(f"Falha na ferramenta local {Path(arguments[0]).stem}.")
    return output.strip()


def _environment(runtime: Path) -> dict[str, str]:
    # Não herdar PGHOST, PGSERVICE ou credenciais de outras conexões da máquina.
    env = {
        key: os.environ[key]
        for key in ("SystemRoot", "WINDIR", "PATH", "TEMP", "TMP")
        if key in os.environ
    }
    env.update(
        {
            "PGPASSFILE": str(runtime / "pgpass.conf"),
            "PGSSLMODE": "verify-full",
            "PGSSLROOTCERT": str(runtime / "server.crt"),
            "PGCONNECT_TIMEOUT": "5",
            "PGCLIENTENCODING": "UTF8",
        }
    )
    return env


def _sql(bin_directory: Path, runtime: Path, database: str, sql: str) -> str:
    return _run(
        [
            str(bin_directory / "psql.exe"),
            "-X",
            "-w",
            "-h",
            "127.0.0.1",
            "-p",
            str(PORT),
            "-U",
            ADMIN,
            "-d",
            database,
            "-v",
            "ON_ERROR_STOP=1",
            "-A",
            "-t",
            "-c",
            sql,
        ],
        env=_environment(runtime),
    )


def _file(bin_directory: Path, runtime: Path, filename: Path) -> str:
    return _run(
        [
            str(bin_directory / "psql.exe"),
            "-X",
            "-w",
            "-h",
            "127.0.0.1",
            "-p",
            str(PORT),
            "-U",
            ADMIN,
            "-d",
            DATABASE,
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            str(filename),
        ],
        env=_environment(runtime),
    )


def _protect(runtime: Path) -> None:
    if os.name == "nt":
        from vrac.db.private_io import _restrict_windows_directory

        _restrict_windows_directory(runtime)
    else:
        runtime.chmod(0o700)


def _initialize(
    bin_directory: Path, runtime: Path, openssl: Path, marker: dict[str, object]
) -> None:
    runtime.mkdir(exist_ok=False)
    _protect(runtime)
    admin_password = secrets.token_urlsafe(36)
    reader_password = secrets.token_urlsafe(36)
    password_file = runtime / "initdb.password"
    password_file.write_text(admin_password + "\n", encoding="utf-8")
    pgpass = "\n".join(
        [
            f"127.0.0.1:{PORT}:postgres:{ADMIN}:{admin_password}",
            f"127.0.0.1:{PORT}:{DATABASE}:{ADMIN}:{admin_password}",
            f"127.0.0.1:{PORT}:{DATABASE}:{READER}:{reader_password}",
            "",
        ]
    )
    (runtime / "pgpass.conf").write_text(pgpass, encoding="utf-8")
    if os.name != "nt":
        password_file.chmod(0o600)
        (runtime / "pgpass.conf").chmod(0o600)
    env = _environment(runtime)
    _run(
        [
            str(bin_directory / "initdb.exe"),
            "-D",
            str(runtime / "data"),
            "-U",
            ADMIN,
            "--encoding=UTF8",
            "--locale=C",
            "--auth-host=scram-sha-256",
            "--auth-local=scram-sha-256",
            f"--pwfile={password_file}",
            "--no-instructions",
        ],
        env=env,
    )
    (runtime / "server-cert.conf").write_text(
        "[req]\ndistinguished_name=dn\nprompt=no\n[dn]\nCN=localhost\n", encoding="utf-8"
    )
    _run(
        [
            str(openssl),
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-sha256",
            "-days",
            "365",
            "-nodes",
            "-config",
            str(runtime / "server-cert.conf"),
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=IP:127.0.0.1,DNS:localhost",
            "-keyout",
            str(runtime / "server.key"),
            "-out",
            str(runtime / "server.crt"),
        ],
        env=env,
    )
    config = "\n".join(
        [
            "listen_addresses = '127.0.0.1'",
            f"port = {PORT}",
            "ssl = on",
            "ssl_min_protocol_version = 'TLSv1.2'",
            f"ssl_cert_file = '{(runtime / 'server.crt').as_posix()}'",
            f"ssl_key_file = '{(runtime / 'server.key').as_posix()}'",
            "password_encryption = 'scram-sha-256'",
            "max_connections = 20",
            "shared_buffers = '32MB'",
            "log_statement = 'none'",
            "",
        ]
    )
    (runtime / "data/postgresql.conf").write_text(config, encoding="utf-8")
    (runtime / "data/pg_hba.conf").write_text(
        f"hostssl postgres {ADMIN} 127.0.0.1/32 scram-sha-256\n"
        f"hostssl {DATABASE} {ADMIN},{READER} 127.0.0.1/32 scram-sha-256\n",
        encoding="utf-8",
    )
    # A senha não é argumento de processo nem parte do pacote gerado no workspace.
    (runtime / "create-reader.sql").write_text(
        f"CREATE ROLE {READER} LOGIN PASSWORD '{reader_password}';\n", encoding="utf-8"
    )
    (runtime / "runtime.json").write_text(json.dumps(marker, indent=2), encoding="utf-8")
    (runtime / "pg_service.conf").write_text(
        "[vrac_sintetico]\n"
        f"host=127.0.0.1\nport={PORT}\ndbname={DATABASE}\nuser={READER}\n"
        f"passfile={(runtime / 'pgpass.conf').as_posix()}\n"
        f"sslmode=verify-full\nsslrootcert={(runtime / 'server.crt').as_posix()}\n",
        encoding="utf-8",
    )


def operate(
    action: str, project: Path, bundle: Path, bin_directory: Path, openssl: Path
) -> dict[str, object]:
    """Destino fixo criado por esta ferramenta; não aceita host ou banco arbitrário."""
    runtime = runtime_directory(project)
    seed = bundle / "01-seed.sql"
    checks = bundle / "02-check.sql"
    if not seed.is_file() or not checks.is_file():
        raise RuntimeErrorSafe("Gere primeiro o pacote sintético local.")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    seed_hash = hashlib.sha256(seed.read_bytes()).hexdigest()
    if (
        manifest.get("synthetic") is not True
        or manifest.get("database") != DATABASE
        or manifest.get("schema") != SCHEMA
        or manifest.get("version") != VERSION
        or manifest.get("seed_sql_sha256") != seed_hash
    ):
        raise RuntimeErrorSafe("Pacote sintético incompatível ou SQL alterado após a geração.")
    marker = {
        "synthetic": True,
        "project": str(project.resolve()),
        "database": DATABASE,
        "port": PORT,
        "seed_sql_sha256": seed_hash,
    }
    for binary in ("initdb.exe", "pg_ctl.exe", "psql.exe"):
        if not (bin_directory / binary).is_file():
            raise RuntimeErrorSafe("Binários do PostgreSQL portátil ausentes.")
    if runtime.exists():
        marker_file = runtime / "runtime.json"
        if runtime.is_symlink() or not marker_file.is_file():
            raise RuntimeErrorSafe(
                "Diretório existente sem identificação sintética; operação recusada."
            )
        if json.loads(marker_file.read_text(encoding="utf-8")) != marker:
            raise RuntimeErrorSafe("Diretório pertence a outro projeto ou outra carga; recusado.")
    elif action == "stop":
        return {"synthetic": True, "running": False}
    else:
        if not openssl.is_file():
            raise RuntimeErrorSafe("OpenSSL ausente para criar o certificado local.")
        _initialize(bin_directory, runtime, openssl, marker)
    ctl = str(bin_directory / "pg_ctl.exe")
    env = _environment(runtime)
    if action == "stop":
        _run([ctl, "stop", "-D", str(runtime / "data"), "-m", "fast", "-w"], env=env)
        return {"synthetic": True, "running": False, "runtime": str(runtime)}
    try:
        _run([ctl, "status", "-D", str(runtime / "data")], env=env)
    except RuntimeErrorSafe:
        _run(
            [
                ctl,
                "start",
                "-D",
                str(runtime / "data"),
                "-l",
                str(runtime / "server.log"),
                "-w",
                "-t",
                "30",
            ],
            env=env,
        )
    exists = _sql(
        bin_directory,
        runtime,
        "postgres",
        f"SELECT count(*) FROM pg_database WHERE datname = '{DATABASE}';",
    )
    if exists == "0":
        _sql(bin_directory, runtime, "postgres", f"CREATE DATABASE \"{DATABASE}\" ENCODING 'UTF8';")
    schema_exists = _sql(
        bin_directory,
        runtime,
        DATABASE,
        f"SELECT count(*) FROM pg_namespace WHERE nspname = '{SCHEMA}';",
    )
    if schema_exists == "0":
        _file(bin_directory, runtime, seed)
    reader_exists = _sql(
        bin_directory,
        runtime,
        "postgres",
        f"SELECT count(*) FROM pg_roles WHERE rolname = '{READER}';",
    )
    if reader_exists == "0":
        _file(bin_directory, runtime, runtime / "create-reader.sql")
    _sql(
        bin_directory,
        runtime,
        DATABASE,
        f"REVOKE ALL ON DATABASE {DATABASE} FROM PUBLIC; "
        f"GRANT CONNECT ON DATABASE {DATABASE} TO {READER}; "
        f"REVOKE CREATE ON SCHEMA public FROM PUBLIC; "
        f"GRANT USAGE ON SCHEMA {SCHEMA} TO {READER}; "
        f"GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA} TO {READER}; "
        f"ALTER ROLE {READER} SET default_transaction_read_only = on; "
        f"ALTER ROLE {READER} SET search_path = {SCHEMA}, pg_catalog;",
    )
    _file(bin_directory, runtime, checks)
    metadata = _sql(
        bin_directory,
        runtime,
        DATABASE,
        f"SELECT synthetic, version, seed FROM {SCHEMA}.dataset_metadata;",
    )
    if metadata != f"t|{VERSION}|{manifest['seed']}":
        raise RuntimeErrorSafe("Banco existente diverge do pacote sintético esperado.")
    reader_check = _run(
        [
            str(bin_directory / "psql.exe"),
            "-X",
            "-w",
            "-h",
            "127.0.0.1",
            "-p",
            str(PORT),
            "-U",
            READER,
            "-d",
            DATABASE,
            "-A",
            "-t",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            "SELECT (SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()), "
            "current_setting('transaction_read_only'), "
            "bool_and(has_table_privilege(current_user, c.oid, 'SELECT') "
            "AND NOT has_table_privilege(current_user, c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE')), "
            f"NOT has_schema_privilege(current_user, '{SCHEMA}', 'CREATE') "
            "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            f"WHERE n.nspname = '{SCHEMA}' AND c.relkind = 'r';",
        ],
        env=env,
    )
    if reader_check != "t|on|t|t":
        raise RuntimeErrorSafe("A conta sintética de leitura ou o TLS diverge do esperado.")
    return {
        "synthetic": True,
        "running": True,
        "host": "127.0.0.1",
        "port": PORT,
        "database": DATABASE,
        "schema": SCHEMA,
        "user": READER,
        "sslmode": "verify-full",
        "service_file": str(runtime / "pg_service.conf"),
        "runtime": str(runtime),
        "checks": "passed",
        "reader_permissions": "select_only",
    }


def main() -> None:
    project = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description="PostgreSQL portátil exclusivamente SINTÉTICO.")
    parser.add_argument("action", choices=("start", "stop"))
    parser.add_argument(
        "--bundle", type=Path, default=project / ".cache/synthetic-postgres/bundle-v1"
    )
    parser.add_argument("--bin", type=Path, default=project / ".tools/postgres/pgsql/bin")
    parser.add_argument(
        "--openssl", type=Path, default=Path("C:/Program Files/Git/usr/bin/openssl.exe")
    )
    args = parser.parse_args()
    try:
        result = operate(args.action, project, args.bundle, args.bin, args.openssl)
    except RuntimeErrorSafe as exc:
        parser.exit(1, f"Falha ao preparar PostgreSQL sintético: {exc}\n")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Falha ao preparar PostgreSQL sintético: {type(exc).__name__}.\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
