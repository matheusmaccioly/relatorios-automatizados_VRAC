"""Validação offline e carga explícita do CSV da Análise Geral de alunos."""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from vrac.dev.faculty_csv import DEPARTMENTS, ImportErrorSafe

COLUMNS = tuple(
    (
        "indicador periodo_eixo periodo_linha aluno_id departamento_curso sigla_centro centro "
        "nivel subnivel curso_codigo curso habilitacao_codigo habilitacao turno forma_ingresso "
        "situacao_atual ingresso_cadastro_nulo ajustes_individuais_informados"
    ).split()
)
INDICATORS = frozenset({"MATRICULADOS", "BOLSISTAS_MATRICULADOS", "FORMADOS", "INGRESSANTES"})
REQUIRED = frozenset(COLUMNS[:5] + COLUMNS[-2:])


def valid_period(value: int) -> bool:
    return 10001 <= value <= 99992 and value % 10 in (1, 2)


def convert(column: str, value: str, null_token: str) -> str | int | None:
    if value == null_token:
        if column in REQUIRED:
            raise ValueError
        return None
    if "\x00" in value:
        raise ValueError
    if column in {"periodo_eixo", "periodo_linha", *COLUMNS[-2:]}:
        if not re.fullmatch(r"[0-9]+", value):
            raise ValueError
        number = int(value)
        if number > 2147483647:
            raise ValueError
        if column.startswith("periodo_") and not valid_period(number):
            raise ValueError
        if column == "ingresso_cadastro_nulo" and number not in (0, 1):
            raise ValueError
        return number
    if column == "aluno_id" and not re.fullmatch(r"[0-9A-F]{64}", value):
        raise ValueError
    if column == "indicador" and value not in INDICATORS:
        raise ValueError
    if column == "departamento_curso" and value not in DEPARTMENTS:
        raise ValueError
    return value


@dataclass(frozen=True)
class StudentBundle:
    rows: tuple[tuple, ...]
    start: int
    end: int
    encoding: str
    null_token: str

    def digest(self) -> str:
        digest = hashlib.sha256()
        for row in self.rows:
            digest.update(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode())
            digest.update(b"\n")
        return digest.hexdigest()


def read_csv(path: Path, *, encoding: str, null_token: str, start: int, end: int) -> StudentBundle:
    """Layout sem cabeçalho; mantém strings vazias e espaços distintos de NULL."""
    if not valid_period(start) or not valid_period(end) or start > end:
        raise ImportErrorSafe("Intervalo de extração inválido.")
    if not null_token or null_token.isspace() or null_token in {"0", "1"}:
        raise ImportErrorSafe("Informe um marcador de nulo distinto de vazio e zero.")
    rows = []
    _ordinal = 0
    try:
        if path.stat().st_size > 200 * 1024 * 1024:
            raise ImportErrorSafe("CSV excede 200 MiB.")
        with path.open(encoding=encoding, newline="") as stream:
            for _ordinal, raw in enumerate(csv.reader(stream, delimiter=";", strict=True), 1):
                if len(raw) != len(COLUMNS):
                    raise ValueError
                row = tuple(convert(c, v, null_token) for c, v in zip(COLUMNS, raw, strict=True))
                if not start <= row[1] <= end:
                    raise ValueError
                if row[0] != "INGRESSANTES" and row[1] != row[2]:
                    raise ValueError
                if row[0] in {"FORMADOS", "INGRESSANTES"} and row[-2] != 0:
                    raise ValueError
                rows.append(row)
    except (OSError, UnicodeError, ValueError, csv.Error):
        raise ImportErrorSafe(f"CSV inválido ou indisponível; registro {_ordinal}.") from None
    if not rows:
        raise ImportErrorSafe("CSV vazio; carga bloqueada.")
    if len({row[-1] for row in rows}) != 1:
        raise ImportErrorSafe("Metadado de ajustes inconsistente entre registros.")
    registered = {row[1:-1] for row in rows if row[0] == "MATRICULADOS"}
    if any(row[1:-1] not in registered for row in rows if row[0] == "BOLSISTAS_MATRICULADOS"):
        raise ImportErrorSafe("Bolsistas sem evento de matrícula correspondente.")
    return StudentBundle(tuple(rows), start, end, encoding, null_token)


def summary(bundle: StudentBundle) -> dict:
    """Apenas totais estruturais; não imprime IDs, categorias ou registros individuais."""
    return {
        "linhas": len(bundle.rows),
        "linhas_por_serie": dict(Counter(row[0] for row in bundle.rows)),
        "departamentos_presentes": len({row[4] for row in bundle.rows}),
        "linhas_duplicadas": len(bundle.rows) - len(set(bundle.rows)),
        "linhas_ingresso_cadastro_nulo": sum(row[-2] for row in bundle.rows),
        "ajustes_individuais_informados": bundle.rows[0][-1],
    }


def queries() -> dict[str, str]:
    path = Path(__file__).resolve().parents[3] / "sql" / "student_import.sql"
    if not path.is_file():
        path = Path(__file__).resolve().parents[1] / "sql" / "student_import.sql"
    return dict(
        (name.strip(), statement.strip())
        for name, statement in (
            block.split("\n", 1)
            for block in path.read_text(encoding="utf-8").split("-- query: ")[1:]
        )
    )


def import_bundle(bundle: StudentBundle, *, service: str, batch: UUID) -> None:
    """Operador: conexão privada externa, TLS validado, COPY e conferência atômicos."""
    import psycopg

    sql = queries()
    with psycopg.connect(service=service, sslmode="verify-full", connect_timeout=15) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql["timeout"])
            cursor.execute(
                sql["batch"],
                (
                    batch,
                    bundle.start,
                    bundle.end,
                    len(bundle.rows),
                    bundle.digest(),
                    bundle.encoding,
                    bundle.null_token,
                    bundle.rows[0][-1],
                ),
            )
            with cursor.copy(sql["copy"]) as copy:
                for ordinal, row in enumerate(bundle.rows, 1):
                    copy.write_row((batch, ordinal, *row))
            cursor.execute(sql["verify"], (batch,))
            for expected in bundle.rows:
                if cursor.fetchone() != expected:
                    raise ImportErrorSafe("Conferência de conteúdo falhou; carga revertida.")
            if cursor.fetchone() is not None:
                raise ImportErrorSafe("Conferência de quantidade falhou; carga revertida.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "import"))
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument(
        "--encoding", choices=("utf-8-sig", "utf-16", "cp1252"), default="utf-8-sig"
    )
    parser.add_argument("--null-token", required=True)
    parser.add_argument("--start", required=True, type=int)
    parser.add_argument("--end", required=True, type=int)
    parser.add_argument("--service")
    parser.add_argument("--batch", type=UUID)
    parser.add_argument("--authorized-destination", action="store_true")
    args = parser.parse_args()
    if args.action == "import" and not (
        args.service and args.batch and args.authorized_destination
    ):
        parser.error("Carga exige --service, --batch e --authorized-destination.")
    try:
        bundle = read_csv(
            args.file,
            encoding=args.encoding,
            null_token=args.null_token,
            start=args.start,
            end=args.end,
        )
        if args.action == "import":
            import_bundle(bundle, service=args.service, batch=args.batch)
        print(json.dumps({"acao": args.action, **summary(bundle)}, ensure_ascii=False))
        return 0
    except ImportErrorSafe as exc:
        print(str(exc))
    except Exception:
        print("Operação não concluída. Confira configuração privada e banco; detalhes omitidos.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
