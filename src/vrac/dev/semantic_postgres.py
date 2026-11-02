"""Gerar uma carga PostgreSQL sintética a partir de dicionários semânticos locais.

Não conecta a bancos, não executa DAX e não lê valores de registros. Nomes e tipos
internos são recebidos somente do documento e da receita locais, nunca empacotados.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

DATABASE = "vrac_sintetico"
SCHEMA = "vrac_sintetico"
VERSION = "semantic-postgres-synthetic-v1"
Value = str | int | float | Decimal | bool | date | datetime | None

PG_TYPES = {
    "texto": "text",
    "inteiro": "bigint",
    "data/hora": "timestamp without time zone",
    "decimal/ponto flutuante": "double precision",
    "decimal fixo/moeda": "numeric(19,4)",
    "booleano": "boolean",
}


@dataclass(frozen=True)
class Column:
    name: str
    model_type: str
    calculated: bool

    @property
    def postgres_type(self) -> str:
        try:
            return PG_TYPES[self.model_type]
        except KeyError as exc:
            raise ValueError(f"Tipo semântico não suportado: {self.model_type}") from exc


@dataclass(frozen=True)
class Table:
    model: str
    name: str
    columns: tuple[Column, ...]


@dataclass(frozen=True)
class SyntheticTable:
    definition: Table
    rows: tuple[Mapping[str, Value], ...]


def identifier(value: str) -> str:
    """Preservar maiúsculas, acentos e espaços sem permitir escape do identificador."""
    if not value or "\x00" in value or len(value.encode("utf-8")) > 63:
        raise ValueError("Identificador vazio, inválido ou maior que 63 bytes.")
    return '"' + value.replace('"', '""') + '"'


def literal(value: Value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (float, Decimal)):
        if not math.isfinite(value):
            raise ValueError("Número não finito não é aceito na carga sintética.")
        return str(value)
    if isinstance(value, (date, datetime)):
        value = value.isoformat()
    if not isinstance(value, str) or "\x00" in value:
        raise ValueError("Valor não suportado na carga sintética.")
    return "'" + value.replace("'", "''") + "'"


def read_dictionary(document: Path, selections: Mapping[str, Sequence[str]]) -> tuple[Table, ...]:
    """Ler somente nomes/tipos do dicionário de colunas dos anexos acadêmicos A/B."""
    if not selections or set(selections) - {"A", "B"}:
        raise ValueError("Selecione somente os modelos acadêmicos A e B.")
    content = document.read_text(encoding="utf-8")
    tables: dict[tuple[str, str], Table] = {}
    model: str | None = None
    in_dictionary = False
    current_name: str | None = None
    columns: list[Column] = []

    def finish_table() -> None:
        if model and current_name and current_name in selections.get(model, ()):
            if not columns or len({c.name for c in columns}) != len(columns):
                raise ValueError("Dicionário vazio ou com colunas duplicadas.")
            table = Table(model, current_name, tuple(columns))
            if (model, current_name) in tables:
                raise ValueError("Tabela duplicada no dicionário.")
            for column in table.columns:
                identifier(column.name)
                _ = column.postgres_type
            identifier(table.name)
            tables[(model, current_name)] = table

    for line in content.splitlines():
        annex = re.match(r"^## Anexo ([A-Z])\b", line)
        if annex:
            finish_table()
            model = annex[1]
            in_dictionary = False
            current_name, columns = None, []
        elif line.startswith("### "):
            finish_table()
            in_dictionary = bool(re.match(r"^### [AB]\.2 Dicionário de colunas", line))
            current_name, columns = None, []
        elif in_dictionary and line.startswith("#### "):
            finish_table()
            current_name, columns = line[5:].strip(), []
        elif in_dictionary and current_name and line.startswith("| "):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and cells[0] not in {"Coluna", "---"}:
                columns.append(Column(cells[0], cells[1], cells[3] == "DAX"))
    finish_table()
    requested = [(model, name) for model, names in selections.items() for name in names]
    if len(set(requested)) != len(requested) or any(key not in tables for key in requested):
        raise ValueError("Seleção duplicada ou tabela ausente no dicionário semântico.")
    if len({name for _, name in requested}) != len(requested):
        raise ValueError("Tabelas homônimas exigem esquemas separados; seleção recusada.")
    return tuple(tables[key] for key in requested)


def _check_value(column: Column, value: Value) -> None:
    if value is None:
        return
    kind = column.postgres_type
    valid = (
        (kind == "text" and isinstance(value, str))
        or (kind == "bigint" and type(value) is int and -(2**63) <= value < 2**63)
        or (kind == "boolean" and type(value) is bool)
        or (kind.startswith("timestamp") and isinstance(value, (date, datetime)))
        or (
            kind in {"double precision", "numeric(19,4)"}
            and type(value) in {int, float, Decimal}
            and math.isfinite(value)
        )
    )
    if not valid:
        raise ValueError(f"Valor sintético incompatível com o tipo {column.model_type}.")


def render_seed(tables: Sequence[SyntheticTable], *, seed: int) -> str:
    """SQL somente para banco dedicado; colisões falham sem sobrescrever a carga."""
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError("A semente deve ser um inteiro de 64 bits.")
    if not tables or len({t.definition.name for t in tables}) != len(tables):
        raise ValueError("A carga exige tabelas distintas.")
    sql = [
        "-- DEMONSTRAÇÃO: DADOS TOTALMENTE SINTÉTICOS. SEM DADOS INSTITUCIONAIS.",
        r"\set ON_ERROR_STOP on",
        r"\encoding UTF8",
        "SET standard_conforming_strings = on;",
        "BEGIN;",
        "DO $$ BEGIN",
        f"IF current_database() <> '{DATABASE}' OR "
        "COALESCE(host(inet_server_addr()) NOT IN ('127.0.0.1', '::1'), false) THEN",
        "RAISE EXCEPTION 'Carga permitida somente no banco sintético local dedicado.';",
        "END IF; END $$;",
        f"CREATE SCHEMA {identifier(SCHEMA)};",
        f"COMMENT ON SCHEMA {identifier(SCHEMA)} IS 'DEMONSTRAÇÃO — DADOS SINTÉTICOS';",
        f"CREATE TABLE {identifier(SCHEMA)}.dataset_metadata "
        "(synthetic boolean NOT NULL CHECK (synthetic), "
        "version text NOT NULL, seed bigint NOT NULL);",
        f"INSERT INTO {identifier(SCHEMA)}.dataset_metadata VALUES "
        f"(TRUE, {literal(VERSION)}, {literal(seed)});",
    ]
    for dataset in tables:
        table = dataset.definition
        qualified = f"{identifier(SCHEMA)}.{identifier(table.name)}"
        names = {c.name for c in table.columns}
        declarations = ",\n".join(
            f"    {identifier(c.name)} {c.postgres_type}" for c in table.columns
        )
        sql.append(f"CREATE TABLE {qualified} (\n{declarations}\n);")
        sql.append(f"COMMENT ON TABLE {qualified} IS 'DEMONSTRAÇÃO — DADOS SINTÉTICOS';")
        values = []
        for row in dataset.rows:
            if set(row) - names:
                raise ValueError("Receita usa coluna ausente no dicionário documentado.")
            for column in table.columns:
                _check_value(column, row.get(column.name))
            values.append("(" + ", ".join(literal(row.get(c.name)) for c in table.columns) + ")")
        column_names = ", ".join(identifier(c.name) for c in table.columns)
        for offset in range(0, len(values), 100):
            sql.append(
                f"INSERT INTO {qualified} ({column_names}) VALUES\n"
                + ",\n".join(values[offset : offset + 100])
                + ";"
            )
    sql.extend(["COMMIT;", ""])
    return "\n".join(sql)


def write_bundle(
    destination: Path,
    tables: Sequence[SyntheticTable],
    *,
    document: Path,
    seed: int,
    scenarios: Mapping[str, object],
) -> Path:
    """Gravar um pacote novo local. Nunca ler registros reais nem substituir arquivos."""
    seed_sql = render_seed(tables, seed=seed)
    manifest = {
        "synthetic": True,
        "version": VERSION,
        "seed": seed,
        "database": DATABASE,
        "schema": SCHEMA,
        "document_sha256": hashlib.sha256(document.read_bytes()).hexdigest(),
        "seed_sql_sha256": hashlib.sha256(seed_sql.encode("utf-8")).hexdigest(),
        "scenarios": scenarios,
        "limitations": [
            "Tipos são do modelo semântico, não DDL do banco institucional.",
            "Colunas sem valores gerados permanecem NULL, inclusive DAX não reproduzido.",
            "Não executa DAX, RLS ou Power Query; não replica o modelo Power BI completo.",
            "Sem PK/FK institucional presumida; relações da fixture são cenários de teste.",
        ],
        "tables": [
            {
                "model": t.definition.model,
                "name": t.definition.name,
                "rows": len(t.rows),
                "columns": len(t.definition.columns),
                "always_null_columns": [
                    c.name
                    for c in t.definition.columns
                    if all(row.get(c.name) is None for row in t.rows)
                ],
                "calculated_columns": [c.name for c in t.definition.columns if c.calculated],
            }
            for t in tables
        ],
    }
    # Todos os dados são gerados/checados antes de criar o diretório.
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "01-seed.sql").write_text(seed_sql, encoding="utf-8", newline="\n")
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return destination
