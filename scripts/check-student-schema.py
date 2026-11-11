"""Teste SQL offline em cluster novo, loopback/TLS, sem credenciais ou dados reais."""

import argparse
import os
import re
import secrets
import socket
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from pathlib import Path
from uuid import UUID

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from vrac.dev.student_csv_remote import render_chunk

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres-bin", required=True, type=Path)
    args = parser.parse_args()
    directory = Path(tempfile.mkdtemp(prefix="vrac-student-sql-fixture-"))
    cluster = directory / "cluster"
    password = secrets.token_urlsafe(32)
    password_file = directory / "fixture-password"
    password_file.write_text(password, encoding="utf-8")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    # Apenas variáveis do sistema; não herda configuração PG, tokens ou senhas.
    env = {
        key: os.environ[key]
        for key in ("SystemRoot", "WINDIR", "PATH", "TEMP", "TMP")
        if key in os.environ
    }
    suffix = ".exe" if os.name == "nt" else ""
    init = subprocess.run(
        [
            str(args.postgres_bin / ("initdb" + suffix)),
            "-D",
            str(cluster),
            "--auth=scram-sha-256",
            "--pwfile=" + str(password_file),
            "--username=fixture_admin",
            "--encoding=UTF8",
            "--no-locale",
        ],
        env=env,
        capture_output=True,
        timeout=60,
    )
    if init.returncode:
        print("Falha na preparação do cluster sintético isolado.")
        return 1
    password_file.unlink()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "vrac-fixture")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(minutes=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ip_address("127.0.0.1"))]), False
        )
        .sign(key, hashes.SHA256())
    )
    (cluster / "server.key").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    (cluster / "server.key").chmod(0o600)
    (cluster / "server.crt").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    with (cluster / "postgresql.conf").open("a", encoding="utf-8") as config:
        config.write(f"\nlisten_addresses='127.0.0.1'\nport={port}\nssl=on\n")
    (cluster / "pg_hba.conf").write_text(
        "hostssl all all 127.0.0.1/32 scram-sha-256\n", encoding="utf-8"
    )
    bootstrap = """
CREATE ROLE anon;
CREATE ROLE authenticated;
CREATE SCHEMA auth;
CREATE SCHEMA vrac_app;
CREATE TABLE auth.users(id uuid PRIMARY KEY,aud text,role text,email text);
CREATE TABLE auth.sessions(id uuid PRIMARY KEY,user_id uuid,not_after timestamptz);
CREATE FUNCTION auth.jwt() RETURNS jsonb LANGUAGE sql STABLE AS $$
 SELECT current_setting('request.jwt.claims',true)::jsonb; $$;
CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS $$
 SELECT (auth.jwt()->>'sub')::uuid; $$;
GRANT USAGE ON SCHEMA auth,vrac_app TO authenticated;
"""
    session = (
        (ROOT / "supabase/migrations/20261105124056_vrac_active_sessions.sql")
        .read_text(encoding="utf-8")
        .split("DO $$", 1)[0]
    )
    migration = (
        ROOT / "supabase/migrations/20261111142817_vrac_alunos_analise_geral.sql"
    ).read_text(encoding="utf-8")
    checks = (ROOT / "supabase/tests/alunos_authorization.sql").read_text(encoding="utf-8")
    policy_fix = (
        ROOT / "supabase/migrations/20261111144715_vrac_alunos_rls_initplan.sql"
    ).read_text(encoding="utf-8")
    interface = (ROOT / "supabase/migrations/20261111145559_vrac_alunos_interface.sql").read_text(
        encoding="utf-8"
    )
    performance = (
        ROOT / "supabase/migrations/20261111150800_vrac_alunos_filter_performance.sql"
    ).read_text(encoding="utf-8")
    load_fixture = """
INSERT INTO vrac_alunos.cargas
(id,periodo_inicio,periodo_fim,linhas,hash_conteudo,encoding,marcador_nulo,ajustes_individuais_informados)
VALUES ('30000000-0000-4000-8000-000000000022',20261,20262,1,repeat('a',64),'utf-8-sig','NULL',0);
"""
    row = (
        "MATRICULADOS",
        20261,
        20261,
        "A" * 64,
        "IND",
        "CTC",
        "Centro fictício",
        "Graduação",
        "Bacharelado",
        "001",
        "D'Ávila {{batch}}",
        "01",
        "Hab fictícia",
        "",
        "Vestibular  ",
        None,
        0,
        0,
    )
    chunk = render_chunk((row,), UUID("30000000-0000-4000-8000-000000000022"), 0)
    verify_chunk = """
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM vrac_alunos.eventos
 WHERE carga_id='30000000-0000-4000-8000-000000000022' AND linha=1
 AND curso='D''Ávila {{batch}}' AND curso_codigo='001' AND situacao_atual IS NULL
 AND turno='' AND forma_ingresso='Vestibular  ')
 THEN RAISE EXCEPTION 'Carga CLI não preservou conteúdo'; END IF;
END $$;
"""
    statements = "\n".join(
        (
            bootstrap,
            session,
            migration,
            policy_fix,
            interface,
            performance,
            checks,
            load_fixture,
            chunk,
            verify_chunk,
        )
    )
    ctl = str(args.postgres_bin / ("pg_ctl" + suffix))
    try:
        # No Windows, o servidor pode herdar pipes do pg_ctl; arquivos evitam esperar EOF.
        with (directory / "control.log").open("wb") as control_log:
            subprocess.run(
                [ctl, "-D", str(cluster), "-l", str(directory / "server.log"), "-w", "start"],
                env=env,
                stdout=control_log,
                stderr=control_log,
                timeout=60,
                check=True,
            )
        env.update(
            PGPASSWORD=password,
            PGSSLMODE="verify-full",
            PGSSLROOTCERT=str(cluster / "server.crt"),
            PGCLIENTENCODING="UTF8",
            PGSERVICEFILE=str(directory / "unused-service"),
            PGSYSCONFDIR=str(directory),
        )
        result = subprocess.run(
            [
                str(args.postgres_bin / ("psql" + suffix)),
                "-X",
                "-w",
                "-h",
                "127.0.0.1",
                "-p",
                str(port),
                "-U",
                "fixture_admin",
                "-d",
                "postgres",
                "-v",
                "ON_ERROR_STOP=1",
            ],
            input=statements.encode("utf-8"),
            env=env,
            capture_output=True,
            timeout=60,
        )
    finally:
        with (directory / "control.log").open("ab") as control_log:
            subprocess.run(
                [ctl, "-D", str(cluster), "-m", "fast", "-w", "stop"],
                env=env,
                stdout=control_log,
                stderr=control_log,
                timeout=60,
            )
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    # Só fixture sintética neste log, preservado para diagnóstico e reprodução.
    (directory / "verification.txt").write_text(output, encoding="utf-8")
    if result.returncode or re.search(r"\b(ERROR|FATAL|PANIC):", output):
        print(f"Teste SQL falhou; log sintético em {directory / 'verification.txt'}")
        return 1
    print(
        "SQL/RLS offline aprovado em PostgreSQL local com TLS; Auth simulado, servidor encerrado."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
