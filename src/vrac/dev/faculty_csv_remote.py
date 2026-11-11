"""Carga autorizada via CLI autenticada, sem ler tokens ou senhas no Python."""

import argparse
import json
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

from psycopg import sql

from vrac.db.private_io import create_private_run_directory
from vrac.dev.faculty_csv import LAYOUTS, digest, read_bundle
from vrac.dev.supabase_migration import PROJECT_REF, ROOT, fingerprint_sql, remote_query


def render_load(bundle: dict[str, list[tuple]], batch: UUID) -> str:
    """Somente os sete conjuntos conhecidos; escape pelo adaptador oficial do driver."""
    if set(bundle) != set(LAYOUTS):
        raise ValueError("Pacote incompleto.")
    template = (ROOT / "sql/faculty_remote_import.sql").read_text(encoding="utf-8")
    batch_sql = sql.Literal(str(batch)).as_string()
    statements = [
        "BEGIN;",
        "SET LOCAL statement_timeout='120s';",
        "PREPARE vrac_csv_batch(uuid) AS INSERT INTO vrac_docentes.cargas(id) VALUES ($1);",
        f"EXECUTE vrac_csv_batch({batch_sql});",
        "DEALLOCATE vrac_csv_batch;",
    ]
    for table, layout in LAYOUTS.items():
        rows = [
            dict(zip(layout.columns, row, strict=True), carga_id=str(batch), linha=i)
            for i, row in enumerate(bundle[table], 1)
        ]
        payload = json.dumps(rows, ensure_ascii=False, default=str, separators=(",", ":"))
        values = {
            "table": table,
            "batch": batch_sql,
            "component": sql.Literal(table).as_string(),
            "count": str(len(rows)),
            "hash": sql.Literal(digest(bundle[table])).as_string(),
            "payload": sql.Literal(payload).as_string(),
        }
        # Substituir payload por último: textos do CSV nunca são templates.
        statement = template
        for key, value in values.items():
            statement = statement.replace("{{" + key + "}}", value)
        statements.append(statement)
    statements.append("COMMIT;")
    return "\n".join(statements)


CHUNK = 5000


def render_chunk(table: str, rows: list[dict], batch: UUID, offset: int) -> str:
    """Bloco fechado de até CHUNK linhas; conferência integral do intervalo de ordinais."""
    if table not in LAYOUTS or not rows or offset < 0 or len(rows) > CHUNK:
        raise ValueError("Bloco inválido.")
    template = (ROOT / "sql/faculty_remote_chunk.sql").read_text(encoding="utf-8")
    payload = json.dumps(rows, ensure_ascii=False, default=str, separators=(",", ":"))
    values = {
        "table": table,
        "batch": sql.Literal(str(batch)).as_string(),
        "offset": str(offset),
        "end": str(offset + len(rows)),
        "payload": sql.Literal(payload).as_string(),
    }
    # Payload por último: textos do CSV nunca são templates.
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def load_in_chunks(bundle: dict[str, list[tuple]], batch: UUID, run) -> dict[str, int]:
    """Cria o lote bloqueado, carrega cada conjunto em blocos e grava o manifesto no fim."""
    if set(bundle) != set(LAYOUTS):
        raise ValueError("Pacote incompleto.")
    batch_sql = sql.Literal(str(batch)).as_string()
    run(f"BEGIN; INSERT INTO vrac_docentes.cargas(id) VALUES ({batch_sql}); COMMIT;")
    for table, layout in LAYOUTS.items():
        rows = [
            dict(zip(layout.columns, row, strict=True), carga_id=str(batch), linha=i)
            for i, row in enumerate(bundle[table], 1)
        ]
        for offset in range(0, len(rows), CHUNK):
            run(render_chunk(table, rows[offset : offset + CHUNK], batch, offset))
            print(
                json.dumps(
                    {"conjunto": table, "conferidas": min(offset + CHUNK, len(rows))},
                    ensure_ascii=False,
                ),
                flush=True,
            )
    checks = " OR ".join(
        f"(SELECT count(*) FROM vrac_docentes.{table} WHERE carga_id={batch_sql})"
        f" <> {len(bundle[table])}"
        for table in LAYOUTS
    )
    manifest = ",".join(
        f"({batch_sql},{sql.Literal(table).as_string()},{len(bundle[table])},"
        f"{sql.Literal(digest(bundle[table])).as_string()})"
        for table in LAYOUTS
    )
    run(
        "BEGIN; DO $$ BEGIN IF "
        + checks
        + " THEN RAISE EXCEPTION 'Contagem divergente'; END IF; END $$; "
        "INSERT INTO vrac_docentes.arquivos(carga_id,conjunto,linhas,hash_conteudo) VALUES "
        + manifest
        + "; COMMIT;"
    )
    return {table: len(rows) for table, rows in bundle.items()}


def synthetic_fingerprints() -> dict:
    tables = remote_query(
        sql="SELECT n.nspname AS schema, c.relname AS name "
        "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname IN ('vrac_app','vrac_sintetico') "
        "AND c.relkind IN ('r','p') ORDER BY 1,2"
    )
    return {
        schema: remote_query(
            sql=fingerprint_sql(schema, [r["name"] for r in tables if r["schema"] == schema])
        )
        for schema in ("vrac_app", "vrac_sintetico")
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--project-ref", required=True, choices=(PROJECT_REF,))
    parser.add_argument("--batch", required=True, type=UUID)
    parser.add_argument("--null-token", required=True)
    parser.add_argument("--authorized-destination", required=True, action="store_true")
    args = parser.parse_args()
    try:
        bundle = read_bundle(args.directory, encoding="utf-8-sig", null_token=args.null_token)
        before = synthetic_fingerprints()
        directory = create_private_run_directory(
            Path(tempfile.gettempdir()) / "vrac-csv-load", str(uuid4()), workspace=ROOT
        )
        path = directory / "load.sql"

        def run(statement: str) -> None:
            path.write_text(statement, encoding="utf-8")
            remote_query(path=path, read_only=False)

        try:
            load_in_chunks(bundle, args.batch, run)
        finally:
            path.unlink(missing_ok=True)
            directory.rmdir()
        after = synthetic_fingerprints()
        if before != after:
            raise RuntimeError("A conferência sintética mudou; não liberar a carga.")
        batch_sql = sql.Literal(str(args.batch)).as_string()
        observed = remote_query(
            sql="SELECT conjunto, linhas FROM vrac_docentes.arquivos "
            f"WHERE carga_id={batch_sql} ORDER BY conjunto"
        )
        if {r["conjunto"]: r["linhas"] for r in observed} != {
            key: len(value) for key, value in bundle.items()
        }:
            raise RuntimeError("Manifesto divergente.")
        print(
            json.dumps(
                {
                    "batch": str(args.batch),
                    "counts": observed,
                    "synthetic_unchanged": True,
                    "released": False,
                }
            )
        )
        return 0
    except Exception:
        print("Carga não confirmada. Consulte o lote antes de repetir; detalhes privados omitidos.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
