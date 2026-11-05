"""Migração explícita da base SINTÉTICA local; artefatos de transferência fora do Git.

Não lê dumps existentes, dicionários privados, .env ou arquivos de credenciais.
O pg_dump/libpq usa o passfile externo já configurado pela base sintética.
"""

# SQL revisado é mantido legível em linhas completas no gerador de desenvolvimento.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from collections import Counter
from dataclasses import asdict, fields
from datetime import date, datetime
from pathlib import Path
from typing import get_args, get_type_hints
from uuid import UUID

from vrac.db import synthetic_postgres as source
from vrac.db.supabase_reader import COMPONENTS
from vrac.dev.postgres_runtime import DATABASE, PORT, READER, runtime_directory
from vrac.dev.semantic_postgres import identifier, literal
from vrac.settings import DemoSource, Settings

PROJECT_REF = "uaauqyjbsqvfhepualur"
ROOT = Path(__file__).resolve().parents[3]
MIGRATION_NAME = "vrac_authenticated_readonly"


def render_schema() -> str:
    """DDL de desenvolvimento, fechado nos contratos já usados pela aplicação."""
    sql = [
        "-- DEMONSTRAÇÃO SINTÉTICA. Projeções de leitura R01–R06, sem novas fórmulas.",
        "CREATE SCHEMA vrac_app;",
        "REVOKE ALL ON SCHEMA vrac_app FROM PUBLIC, anon, authenticated;",
        "GRANT USAGE ON SCHEMA vrac_app TO authenticated;",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA vrac_app REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated;",
        "CREATE TABLE vrac_app.departments (department text PRIMARY KEY);",
        "CREATE TABLE vrac_app.access_grants (user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE, department text NOT NULL REFERENCES vrac_app.departments(department), enabled boolean NOT NULL DEFAULT true, PRIMARY KEY(user_id, department));",
        "CREATE TABLE vrac_app.dataset_metadata (singleton boolean PRIMARY KEY CHECK(singleton), synthetic boolean NOT NULL CHECK(synthetic), version text NOT NULL, seed bigint NOT NULL, periods text[] NOT NULL, policy jsonb NOT NULL);",
    ]
    types = {
        str: "text",
        int: "bigint",
        float: "double precision",
        bool: "boolean",
        date: "timestamp without time zone",
        datetime: "timestamp without time zone",
    }
    for name, row_type in COMPONENTS.items():
        hints = get_type_hints(row_type)
        declarations = [
            "scope_department text NOT NULL REFERENCES vrac_app.departments(department)",
            "ordinal integer NOT NULL CHECK(ordinal >= 0)",
        ]
        for column in fields(row_type):
            hint = hints[column.name]
            candidates = get_args(hint) or (hint,)
            kinds = {types[t] for t in candidates if t is not type(None)}
            if len(kinds) != 1:
                raise ValueError("Contrato de tipo incompatível.")
            declarations.append(f"{identifier(column.name)} {kinds.pop()}")
        declarations.append("PRIMARY KEY(scope_department, ordinal)")
        sql.append(f"CREATE TABLE vrac_app.{identifier(name)} (" + ", ".join(declarations) + ");")
    all_tables = ("access_grants", "departments", "dataset_metadata", *COMPONENTS)
    for table in all_tables:
        qualified = f"vrac_app.{identifier(table)}"
        sql.extend(
            [
                f"ALTER TABLE {qualified} ENABLE ROW LEVEL SECURITY;",
                f"ALTER TABLE {qualified} FORCE ROW LEVEL SECURITY;",
                f"REVOKE ALL ON {qualified} FROM PUBLIC, anon, authenticated;",
                f"GRANT SELECT ON {qualified} TO authenticated;",
            ]
        )
        if table == "access_grants":
            predicate = "user_id = (SELECT auth.uid()) AND enabled"
        elif table == "dataset_metadata":
            predicate = "EXISTS (SELECT 1 FROM vrac_app.access_grants)"
        else:
            scope = "department" if table == "departments" else "scope_department"
            predicate = f"{scope} IN (SELECT department FROM vrac_app.access_grants)"
        # Anonymous Auth users are also authenticated; deny them explicitly.
        predicate += " AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'"
        sql.append(
            f"CREATE POLICY read_authorized ON {qualified} FOR SELECT TO authenticated USING ({predicate});"
        )
    sql.extend(
        [
            "CREATE FUNCTION public.vrac_options() RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$",
            "SELECT COALESCE((SELECT jsonb_build_object('synthetic', synthetic, 'version', version, 'periods', periods, 'departments', (SELECT COALESCE(jsonb_agg(department ORDER BY department), '[]'::jsonb) FROM vrac_app.departments)) FROM vrac_app.dataset_metadata), '{\"synthetic\":true,\"departments\":[],\"periods\":[]}'::jsonb); $$;",
            "REVOKE ALL ON FUNCTION public.vrac_options() FROM PUBLIC, anon;",
            "GRANT EXECUTE ON FUNCTION public.vrac_options() TO authenticated;",
            "CREATE FUNCTION public.vrac_snapshot(p_departments text[]) RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = '' SET statement_timeout = '15s' AS $$",
            "DECLARE result jsonb; BEGIN",
            "IF p_departments IS NULL OR cardinality(p_departments) NOT BETWEEN 1 AND 1000 OR EXISTS (SELECT 1 FROM unnest(p_departments) d WHERE d IS NULL OR d NOT IN (SELECT department FROM vrac_app.departments)) OR cardinality(p_departments) <> (SELECT count(DISTINCT d) FROM unnest(p_departments) d) THEN RAISE EXCEPTION 'Recorte não autorizado' USING ERRCODE = '42501'; END IF;",
        ]
    )
    for name in COMPONENTS:
        sql.append(
            f"IF (SELECT count(*) FROM vrac_app.{identifier(name)} WHERE scope_department = ANY(p_departments)) > 5000 THEN RAISE EXCEPTION 'Limite do snapshot excedido'; END IF;"
        )
    sql.append(
        "SELECT jsonb_build_object('synthetic', synthetic, 'version', version, 'periods', periods, 'policy', policy) INTO STRICT result FROM vrac_app.dataset_metadata;"
    )
    for name in COMPONENTS:
        sql.append(
            f"result := result || jsonb_build_object('{name}', (SELECT COALESCE(jsonb_agg(to_jsonb(r) - 'scope_department' - 'ordinal' ORDER BY scope_department, ordinal), '[]'::jsonb) FROM vrac_app.{identifier(name)} r WHERE scope_department = ANY(p_departments)));"
        )
    sql.extend(
        [
            "RETURN result; END; $$;",
            "REVOKE ALL ON FUNCTION public.vrac_snapshot(text[]) FROM PUBLIC, anon;",
            "GRANT EXECUTE ON FUNCTION public.vrac_snapshot(text[]) TO authenticated;",
            "NOTIFY pgrst, 'reload schema';",
            "",
        ]
    )
    return "\n".join(sql)


def fingerprint_sql(schema: str, tables: list[str]) -> str:
    return (
        " UNION ALL ".join(
            f"SELECT {literal(table)} AS table_name, count(*) AS rows, md5(COALESCE(string_agg(digest, '' ORDER BY digest), '')) AS fingerprint FROM (SELECT md5(to_jsonb(r)::text) AS digest FROM {identifier(schema)}.{identifier(table)} r) s"
            for table in tables
        )
        + ";"
    )


def _insert(table: str, names: list[str], rows: list[list]) -> str:
    if not rows:
        return ""
    return (
        f"INSERT INTO vrac_app.{identifier(table)} ("
        + ",".join(map(identifier, names))
        + ") VALUES\n"
        + ",\n".join("(" + ",".join(literal(v) for v in row) + ")" for row in rows)
        + ";\n"
    )


def prepare() -> Path:
    """Exportar um snapshot conferido; nunca substituir uma base ou um pacote existente."""
    from psycopg.conninfo import make_conninfo

    destination = Path(tempfile.mkdtemp(prefix="vrac-supabase-transfer-"))
    runtime = runtime_directory(ROOT)
    settings = Settings(demo_source=DemoSource.POSTGRES)
    counts: Counter[str] = Counter()
    projection = []
    with source._connection(settings) as (connection, version):
        options = source._options(connection)
        metadata = source._rows(connection, source.Query.METADATA)[0]
        snapshot = connection.execute("SELECT pg_export_snapshot() AS snapshot").fetchone()[
            "snapshot"
        ]
        tables = [
            r["table_name"]
            for r in connection.execute(
                "SELECT c.relname AS table_name FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='vrac_sintetico' AND c.relkind IN ('r','p') ORDER BY c.relname"
            ).fetchall()
        ]
        reference = connection.execute(fingerprint_sql("vrac_sintetico", tables)).fetchall()
        conninfo = make_conninfo(
            host="127.0.0.1",
            port=PORT,
            dbname=DATABASE,
            user=READER,
            passfile=str(runtime / "pgpass.conf"),
            sslmode="verify-full",
            sslrootcert=str(runtime / "server.crt"),
            connect_timeout=5,
        )
        dump = subprocess.run(
            [
                str(ROOT / ".tools/postgres/pgsql/bin/pg_dump.exe"),
                "--dbname",
                conninfo,
                "--schema=vrac_sintetico",
                "--no-owner",
                "--no-privileges",
                "--inserts",
                "--no-tablespaces",
                "--no-publications",
                "--no-subscriptions",
                f"--snapshot={snapshot}",
            ],
            capture_output=True,
            check=False,
        )
        if dump.returncode:
            raise RuntimeError(
                "A exportação sintética falhou. Nenhuma alteração remota foi aplicada."
            )
        # pg_dump 18 emits psql-only markers and transaction_timeout (not in Postgres 17).
        exported = "\n".join(
            line
            for line in dump.stdout.decode("utf-8").splitlines()
            if not line.startswith(("\\", "SET transaction_timeout"))
        )
        (destination / "source.sql").write_text(exported, encoding="utf-8")
        projection.append(
            _insert("departments", ["department"], [[d] for d in options.departments])
        )
        policy = None
        for department in options.departments:
            academic = source._read_academic_source(connection, version, department=department)
            expected = {
                "register",
                "real_hours",
                "policy",
                "history",
                "workloads",
                "allocations",
                "functions",
                "appointments",
                "students",
                "student_history",
                "scholarships",
            }
            if set(academic.available) != expected or academic.errors:
                raise RuntimeError("Fonte sintética incompleta: a transferência foi interrompida.")
            current_policy = asdict(academic.policy)
            if policy is not None and current_policy != policy:
                raise RuntimeError("Metadados de simulação divergentes.")
            policy = current_policy
            values = {
                name: getattr(academic, name)
                for name in expected - {"register", "real_hours", "policy"}
            }
            values.update(
                register=academic.faculty.register, real_hours=academic.faculty.real_hours
            )
            for name, query in (
                ("demo_faculty", source.Query.FACULTY),
                ("demo_allocations", source.Query.ALLOCATIONS),
            ):
                values[name] = tuple(
                    COMPONENTS[name](**row)
                    for period in options.periods
                    for row in source._rows(
                        connection, query, {"department": department, "period": period}
                    )
                )
            for name, rows in values.items():
                names = [f.name for f in fields(COMPONENTS[name])]
                projection.append(
                    _insert(
                        name,
                        ["scope_department", "ordinal", *names],
                        [
                            [department, ordinal, *[getattr(row, column) for column in names]]
                            for ordinal, row in enumerate(rows)
                        ],
                    )
                )
                counts[name] += len(rows)
        projection.append(
            "INSERT INTO vrac_app.dataset_metadata VALUES (true, true, "
            + literal(version)
            + ","
            + literal(metadata["seed"])
            + ",ARRAY["
            + ",".join(map(literal, options.periods))
            + "],"
            + literal(json.dumps(policy))
            + "::jsonb);\n"
        )
    (destination / "projection.sql").write_text("\n".join(projection), encoding="utf-8")
    manifest = {
        "synthetic": True,
        "project_ref": PROJECT_REF,
        "version": version,
        "departments": len(options.departments),
        "periods": len(options.periods),
        "source_reference": reference,
        "projection_counts": dict(counts),
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    return destination


def remote_query(
    *, sql: str | None = None, path: Path | None = None, read_only: bool = True
) -> list:
    command = ["npx.cmd", "--yes", "supabase@3.0.0", "db", "query", f"--remote={PROJECT_REF}"]
    command += ["--read-only"] if read_only else ["--yes"]
    # SQL nunca passa como código de shell: arquivos evitam limites e escapes do cmd.exe.
    with tempfile.TemporaryDirectory(prefix="vrac-supabase-query-") as temporary:
        if path is None:
            path = Path(temporary) / "query.sql"
            path.write_text(sql or "", encoding="utf-8")
        command += ["--file", str(path.resolve())]
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
        )
    if result.returncode:
        raise RuntimeError(
            "A operação Supabase falhou. Nenhuma mensagem privada do provedor foi exibida."
        )
    response = json.loads(result.stdout)
    if response.get("error") or response.get("_tag") == "Error":
        raise RuntimeError("A consulta Supabase não foi concluída.")
    return response.get("rows", [])


def apply(destination: Path) -> dict:
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("synthetic") is not True or manifest.get("project_ref") != PROJECT_REF:
        raise ValueError("Pacote incompatível com o destino autorizado.")
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    if len(migrations) != 2:
        raise ValueError("Conjunto de migrações de aplicação incompatível com este pacote.")
    # One transaction: a collision or error rolls back source, projection and permissions.
    combined = [
        "BEGIN;",
        (destination / "source.sql").read_text(encoding="utf-8"),
        *(migration.read_text(encoding="utf-8") for migration in migrations),
        (destination / "projection.sql").read_text(encoding="utf-8"),
        "REVOKE ALL ON SCHEMA vrac_sintetico FROM PUBLIC, anon, authenticated;",
        "REVOKE ALL ON ALL TABLES IN SCHEMA vrac_sintetico FROM PUBLIC, anon, authenticated;",
        "REVOKE ALL ON ALL FUNCTIONS IN SCHEMA vrac_sintetico FROM PUBLIC, anon, authenticated;",
        history_sql(),
        "COMMIT;",
    ]
    restore = destination / "restore.sql"
    restore.write_text("\n".join(combined), encoding="utf-8")
    remote_query(path=restore, read_only=False)
    return verify(destination)


def history_sql() -> str:
    """Formato do ledger da CLI 3.0.0, conferido no código oficial migration-history.ts.

    Aplicável somente às migrações já executadas; não apaga nem reescreve histórico.
    Os arquivos são armazenados como uma entrada SQL completa, válida para replay.
    """
    sql = [
        "CREATE SCHEMA IF NOT EXISTS supabase_migrations;",
        "CREATE TABLE IF NOT EXISTS supabase_migrations.schema_migrations "
        "(version text NOT NULL PRIMARY KEY, statements text[], name text);",
        "REVOKE ALL ON SCHEMA supabase_migrations FROM PUBLIC, anon, authenticated;",
        "REVOKE ALL ON supabase_migrations.schema_migrations FROM PUBLIC, anon, authenticated;",
    ]
    for migration in sorted((ROOT / "supabase/migrations").glob("*.sql")):
        version, name = migration.stem.split("_", 1)
        sql.append(
            "INSERT INTO supabase_migrations.schema_migrations(version,name,statements) VALUES ("
            + literal(version)
            + ","
            + literal(name)
            + ",ARRAY["
            + literal(migration.read_text(encoding="utf-8"))
            + "]) ON CONFLICT (version) DO NOTHING;"
        )
    return "\n".join(sql)


def grant_access(user_id: str) -> int:
    """Operação administrativa explícita, sem convidar usuários ou receber senhas."""
    user = str(UUID(user_id))
    return len(
        remote_query(
            sql="INSERT INTO vrac_app.access_grants (user_id,department) "
            f"SELECT '{user}'::uuid, department FROM vrac_app.departments "
            "ON CONFLICT (user_id,department) DO UPDATE SET enabled=true RETURNING department;",
            read_only=False,
        )
    )


def verify(destination: Path) -> dict:
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    reference = manifest["source_reference"]
    observed = remote_query(
        sql=fingerprint_sql("vrac_sintetico", [r["table_name"] for r in reference])
    )
    if sorted(reference, key=lambda r: r["table_name"]) != sorted(
        observed, key=lambda r: r["table_name"]
    ):
        raise RuntimeError("A conciliação do schema original encontrou divergências.")
    observed_counts = remote_query(
        sql=" UNION ALL ".join(
            f"SELECT '{name}' AS component, count(*) AS rows FROM vrac_app.{identifier(name)}"
            for name in COMPONENTS
        )
    )
    if {r["component"]: r["rows"] for r in observed_counts} != manifest["projection_counts"]:
        raise RuntimeError("A conciliação das projeções encontrou divergências.")
    result = {
        "synthetic": True,
        "source_tables": len(reference),
        "source_rows": sum(r["rows"] for r in reference),
        "projection_rows": sum(manifest["projection_counts"].values()),
        "departments": manifest["departments"],
        "periods": manifest["periods"],
        "source_fingerprints_match": True,
        "projection_counts_match": True,
    }
    (destination / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("schema", "prepare", "apply", "verify", "grant", "rls-check")
    )
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--user-id", help="UUID da conta criada manualmente no Supabase Auth.")
    args = parser.parse_args()
    try:
        if args.action == "schema":
            migration = next((ROOT / "supabase/migrations").glob(f"*_{MIGRATION_NAME}.sql"))
            migration.write_text(render_schema(), encoding="utf-8")
            print("Migração SQL dos contratos gravada.")
        elif args.action == "prepare":
            print(json.dumps({"bundle": str(prepare()), "synthetic": True}))
        elif args.action == "grant" and args.user_id:
            print(json.dumps({"authorized_departments": grant_access(args.user_id)}))
        elif args.action == "rls-check":
            remote_query(path=ROOT / "supabase/tests/authorization.sql", read_only=False)
            print("Políticas de acesso verificadas; dados de teste revertidos.")
        elif args.bundle:
            print(json.dumps(apply(args.bundle) if args.action == "apply" else verify(args.bundle)))
        else:
            parser.error("Informe o pacote sintético com --bundle.")
    except Exception as error:
        parser.exit(
            1, f"Migração interrompida ({type(error).__name__}). Nenhum dado privado foi exibido.\n"
        )


if __name__ == "__main__":
    main()
