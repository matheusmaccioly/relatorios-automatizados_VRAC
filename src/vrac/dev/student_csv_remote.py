"""Carga de alunos por exceção autorizada via CLI; tokens nunca lidos pelo código."""

import argparse
import json
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

from psycopg import sql

from vrac.db.private_io import create_private_run_directory
from vrac.dev.student_csv import StudentBundle, queries, read_csv
from vrac.dev.supabase_migration import PROJECT_REF, ROOT, fingerprint_sql, remote_query


def render_chunk(rows: tuple[tuple, ...], batch: UUID, offset: int) -> str:
    if not rows or not 0 <= offset or len(rows) > 5000:
        raise ValueError("Bloco inválido.")
    template = (ROOT / "sql/student_remote_import.sql").read_text(encoding="utf-8")
    values = {
        "batch": sql.Literal(str(batch)).as_string(),
        "offset": str(offset),
        "end": str(offset + len(rows)),
        "payload": sql.Literal(
            json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
        ).as_string(),
    }
    # Payload por último, nunca reinterpretado como template ou identificador.
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def existing_fingerprints() -> dict:
    tables = remote_query(
        sql="SELECT n.nspname AS schema,c.relname AS name FROM pg_class c "
        "JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname IN ('vrac_app','vrac_sintetico','vrac_docentes') "
        "AND c.relkind IN ('r','p') ORDER BY 1,2"
    )
    return {
        schema: remote_query(
            sql=fingerprint_sql(schema, [r["name"] for r in tables if r["schema"] == schema])
        )
        for schema in ("vrac_app", "vrac_sintetico", "vrac_docentes")
    }


def run_load(bundle: StudentBundle, batch: UUID) -> dict:
    before = existing_fingerprints()
    directory = create_private_run_directory(
        Path(tempfile.gettempdir()) / "vrac-student-load", str(uuid4()), workspace=ROOT
    )
    path = directory / "load.sql"
    try:
        params = (
            str(batch),
            bundle.start,
            bundle.end,
            len(bundle.rows),
            bundle.digest(),
            bundle.encoding,
            bundle.null_token,
            bundle.rows[0][-1],
        )
        statement = queries()["batch"]
        # SQL fechado; placeholders convertidos em parâmetros PREPARE da CLI.
        for i in range(1, 9):
            statement = statement.replace("%s", f"${i}", 1)
        command = (
            "BEGIN; PREPARE vrac_student_batch"
            "(uuid,integer,integer,bigint,text,text,text,integer) AS "
            + statement
            + " EXECUTE vrac_student_batch("
            + ",".join(sql.Literal(v).as_string() for v in params)
            + "); DEALLOCATE vrac_student_batch; COMMIT;"
        )
        path.write_text(command, encoding="utf-8")
        remote_query(path=path, read_only=False)
        for offset in range(0, len(bundle.rows), 5000):
            chunk = bundle.rows[offset : offset + 5000]
            path.write_text(render_chunk(chunk, batch, offset), encoding="utf-8")
            remote_query(path=path, read_only=False)
            print(
                json.dumps({"eventos_conferidos": offset + len(chunk), "total": len(bundle.rows)}),
                flush=True,
            )
        batch_sql = sql.Literal(str(batch)).as_string()
        observed = remote_query(
            sql="SELECT count(*) AS rows,min(linha) AS first,max(linha) AS last "
            "FROM vrac_alunos.eventos WHERE carga_id=" + batch_sql
        )
        if observed != [{"rows": len(bundle.rows), "first": 1, "last": len(bundle.rows)}]:
            raise RuntimeError("Contagem final divergente.")
        if before != existing_fingerprints():
            raise RuntimeError("Conferência das bases existentes mudou; manter lote bloqueado.")
        metadata = remote_query(
            sql="SELECT linhas,hash_conteudo,liberada FROM vrac_alunos.cargas WHERE id=" + batch_sql
        )
        if metadata != [
            {"linhas": len(bundle.rows), "hash_conteudo": bundle.digest(), "liberada": False}
        ]:
            raise RuntimeError("Manifesto divergente.")
        return {
            "batch": str(batch),
            "eventos": len(bundle.rows),
            "liberada": False,
            "bases_existentes_inalteradas": True,
            "conferencia_integral_por_bloco": True,
        }
    finally:
        path.unlink(missing_ok=True)
        directory.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--project-ref", choices=(PROJECT_REF,), required=True)
    parser.add_argument("--batch", type=UUID, required=True)
    parser.add_argument("--authorized-destination", action="store_true", required=True)
    parser.add_argument("--null-token", required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    args = parser.parse_args()
    try:
        bundle = read_csv(
            args.file,
            encoding="utf-8-sig",
            null_token=args.null_token,
            start=args.start,
            end=args.end,
        )
        print(json.dumps(run_load(bundle, args.batch)), flush=True)
        return 0
    except Exception:
        print(
            "Carga não confirmada. Lote pode estar parcial e permanece bloqueado; "
            "conferir antes de repetir."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
