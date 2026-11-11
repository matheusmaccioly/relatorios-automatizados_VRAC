"""Carga explícita dos sete CSVs docentes; nunca executada pelo startup do app.

Layout v2 (11/11/2026): seis quadros docentes e todas as situações no cadastro; histórico
mensal pela folha (departamento de cada competência, inclusive desligados) desde 2022;
disciplinas e gratificações legíveis. Pessoa e vínculo continuam pseudonimizados.
"""

import argparse
import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from uuid import UUID

DEPARTMENTS = frozenset({"ADM", "ECO", "EDU", "ELE", "FIL", "IND", "INF", "DIR"})


@dataclass(frozen=True)
class Layout:
    filename: str
    columns: tuple[str, ...]


# Ordem dos SELECTs do pacote docentes v2 (docs/operations/departamentos.local/docentes_v2).
LAYOUTS = {
    "cadastro": Layout(
        "01_cadastro.csv",
        tuple(
            (
                "pessoa_id nome_ficticio vinculo_id departamento_alocacao quadro categoria "
                "situacao dupla_funcao carga_semanal titulacao tempo_casa_anos "
                "vinculo_extraordinario"
            ).split()
        ),
    ),
    "horas_reais": Layout(
        "02_horas_reais_2026.csv",
        tuple(
            "departamento_alocacao vinculo_id semestre quadro horas_contratuais horas_reais".split()
        ),
    ),
    "historico_mensal": Layout(
        "03_historico_mensal_2026.csv",
        tuple(
            (
                "departamento_alocacao vinculo_id pessoa_id ano mes lote ativo "
                "excluido_a4 carga_horaria"
            ).split()
        ),
    ),
    "historico_cargos": Layout(
        "04_historico_cargos_com_antecedente.csv",
        tuple("departamento_alocacao vinculo_id competencia categoria quadro".split()),
    ),
    "historico_carga": Layout(
        "05_historico_carga_com_antecedentes.csv",
        tuple("departamento_alocacao vinculo_id ano mes carga_horaria".split()),
    ),
    "alocacoes": Layout(
        "06_alocacoes_turmas_2026.csv",
        tuple(
            (
                "departamento_alocacao vinculo_id semestre unidade_oferta disciplina_id turma_id "
                "nivel tipo obrigatoria horas_alocadas compartilhada vagas_ofertadas "
                "vagas_preenchidas professor_principal disciplina_codigo disciplina_nome "
                "turma creditos horas_distancia horas_extensao"
            ).split()
        ),
    ),
    "eventos_funcoes": Layout(
        "07_eventos_funcoes_2026.csv",
        tuple(
            (
                "departamento_alocacao vinculo_id evento_id ano mes descricao_id papel_id "
                "gratificacao papel departamento_distribuicao"
            ).split()
        ),
    ),
}
NUMERICS = frozenset(
    (
        "carga_semanal horas_contratuais horas_reais carga_horaria horas_alocadas "
        "tempo_casa_anos creditos horas_distancia horas_extensao"
    ).split()
)
# Histórico e gratificações cobrem a janela do painel Histórico do Departamento.
FIRST_YEAR, LAST_YEAR = 2022, 2026
# Histórico segue o departamento da folha: inclui desligados e quem mudou de unidade,
# por isso não exige o vínculo no cadastro atual do mesmo departamento.
HISTORY_TABLES = frozenset({"historico_mensal", "historico_cargos"})
INTEGERS = frozenset(
    (
        "semestre ano mes ativo excluido_a4 vagas_ofertadas vagas_preenchidas professor_principal"
    ).split()
)
FLAGS = frozenset("ativo excluido_a4 professor_principal".split())


class ImportErrorSafe(ValueError):
    """Mensagens não incluem registros, caminhos privados ou respostas do servidor."""


def convert(column: str, raw: str, null_token: str) -> object:
    if raw == null_token:
        if column in {"departamento_alocacao", "vinculo_id"}:
            raise ValueError
        return None
    if column.endswith("_id"):
        if not re.fullmatch("[0-9A-F]{64}", raw):
            raise ValueError
    if column == "departamento_alocacao" and raw not in DEPARTMENTS:
        raise ValueError
    if column in NUMERICS:
        if not re.fullmatch(r"-?\d+(?:\.\d+)?", raw):
            raise ValueError
        value = Decimal(raw)
        if not value.is_finite():
            raise ValueError
        return value
    if column in INTEGERS:
        if not re.fullmatch(r"\d+", raw):
            raise ValueError
        value = int(raw)
        if value > 2147483647:
            raise ValueError
        if column in FLAGS and value not in {0, 1}:
            raise ValueError
        if column == "mes" and not 1 <= value <= 12:
            raise ValueError
        if column == "ano" and not 1 <= value <= 2026:
            raise ValueError
        if column == "semestre" and value not in {20261, 20262}:
            raise ValueError
        return value
    if "\x00" in raw:
        raise ValueError
    return raw


def read_bundle(directory: Path, *, encoding: str, null_token: str) -> dict[str, list[tuple]]:
    """Sem cabeçalho, separador ;, nulo explicitamente escolhido pelo operador."""
    result = {}
    for table, layout in LAYOUTS.items():
        path = directory / layout.filename
        # O pacote usa plural, mas o CSV recebido usa singular; aceitar ambos, nunca ambos juntos.
        if table == "historico_cargos":
            alternate = directory / "04_historico_cargos_com_antecedentes.csv"
            if alternate.exists():
                if path.exists():
                    raise ImportErrorSafe("Dois arquivos de histórico de cargos encontrados.")
                path = alternate
        try:
            if path.stat().st_size > 100 * 1024 * 1024:
                raise ImportErrorSafe("Arquivo excede o limite de 100 MiB.")
            content = path.read_bytes().decode(encoding)
            rows = []
            for row in csv.reader(io.StringIO(content), delimiter=";", strict=True):
                if len(row) != len(layout.columns):
                    raise ValueError
                rows.append(
                    tuple(
                        convert(c, v, null_token) for c, v in zip(layout.columns, row, strict=True)
                    )
                )
            result[table] = rows
        except (OSError, UnicodeError, ValueError, csv.Error):
            raise ImportErrorSafe(
                f"Arquivo {layout.filename}: formato inválido ou indisponível."
            ) from None
    register = LAYOUTS["cadastro"].columns
    keys = {
        (r[register.index("departamento_alocacao")], r[register.index("vinculo_id")])
        for r in result["cadastro"]
    }
    if not keys:
        raise ImportErrorSafe("Cadastro vazio; carga bloqueada.")
    for table, rows in result.items():
        columns = LAYOUTS[table].columns
        for row in rows:
            if (
                table not in HISTORY_TABLES
                and (
                    row[columns.index("departamento_alocacao")],
                    row[columns.index("vinculo_id")],
                )
                not in keys
            ):
                raise ImportErrorSafe(f"{table}: vínculo sem cadastro no mesmo departamento.")
            if table in {"historico_mensal", "eventos_funcoes"} and not (
                FIRST_YEAR <= row[columns.index("ano")] <= LAST_YEAR
            ):
                raise ImportErrorSafe(f"{table}: ano fora do recorte.")
    history_keys = {
        (r[0], r[1]) for r in result["historico_mensal"]
    }  # departamento_alocacao, vinculo_id
    if any((r[0], r[1]) not in history_keys | keys for r in result["historico_cargos"]):
        raise ImportErrorSafe("historico_cargos: vínculo fora do histórico e do cadastro.")
    return result


def digest(rows: list[tuple]) -> str:
    return hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def import_bundle(bundle: dict[str, list[tuple]], *, service: str, batch: UUID) -> None:
    """Somente operador: serviço libpq privado externo; TLS obrigatório; carga atômica."""
    import psycopg

    query_file = Path(__file__).resolve().parents[3] / "sql" / "faculty_import.sql"
    if not query_file.is_file():
        query_file = Path(__file__).resolve().parents[1] / "sql" / "faculty_import.sql"
    queries = {}
    for block in query_file.read_text(encoding="utf-8").split("-- query: ")[1:]:
        name, statement = block.split("\n", 1)
        queries[name.strip()] = statement.strip()
    if not set(bundle).issubset(LAYOUTS):
        raise ImportErrorSafe("Conjunto indisponível.")

    with psycopg.connect(service=service, sslmode="verify-full", connect_timeout=15) as connection:
        with connection.cursor() as cursor:
            cursor.execute(queries["timeout"])
            cursor.execute(queries["batch"], (batch,))
            for table, rows in bundle.items():
                with cursor.copy(queries["copy_" + table]) as copy:
                    for ordinal, row in enumerate(rows, 1):
                        copy.write_row((batch, ordinal, *row))
                cursor.execute(queries["verify_" + table], (batch,))
                if cursor.fetchall() != rows:
                    raise ImportErrorSafe("Conferência de conteúdo falhou; transação revertida.")
                cursor.execute(
                    queries["manifest"],
                    (batch, table, len(rows), digest(rows)),
                )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "import"))
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument(
        "--encoding", choices=("utf-8-sig", "cp1252", "utf-16"), default="utf-8-sig"
    )
    parser.add_argument(
        "--null-token", required=True, help="Ex.: NULL; vazio não é convertido por padrão."
    )
    parser.add_argument("--service", help="Nome de serviço libpq configurado fora do workspace.")
    parser.add_argument("--batch", type=UUID)
    parser.add_argument("--authorized-destination", action="store_true")
    args = parser.parse_args()
    try:
        bundle = read_bundle(args.directory, encoding=args.encoding, null_token=args.null_token)
        if args.action == "import":
            if not args.service or not args.authorized_destination or not args.batch:
                parser.error("Importação exige --service, --batch e --authorized-destination.")
            import_bundle(bundle, service=args.service, batch=args.batch)
        print(
            json.dumps(
                {"action": args.action, "counts": {k: len(v) for k, v in bundle.items()}},
                ensure_ascii=False,
            )
        )
        return 0
    except Exception:
        print(
            "Operação não concluída. Confira arquivos, formato e configuração privada; "
            "nenhum detalhe pessoal foi registrado."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
