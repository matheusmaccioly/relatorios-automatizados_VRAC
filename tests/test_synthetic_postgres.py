"""Gerador offline: tipos e SQL seguros, sem metadados internos ou PostgreSQL real."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

import pytest

from vrac.dev.postgres_runtime import RuntimeErrorSafe, _environment, operate
from vrac.dev.semantic_postgres import (
    Column,
    SyntheticTable,
    Table,
    identifier,
    literal,
    read_dictionary,
    render_seed,
    write_bundle,
)


def sample() -> SyntheticTable:
    return SyntheticTable(
        Table(
            "A",
            'Tabela "fictícia"',
            (
                Column("Identificador", "inteiro", False),
                Column("Nome", "texto", False),
                Column("Horas", "inteiro", False),
                Column("Data", "data/hora", False),
                Column("Cálculo pendente", "decimal/ponto flutuante", True),
            ),
        ),
        (
            {
                "Identificador": 1,
                "Nome": "Sintético d'Água",
                "Horas": 0,
                "Data": datetime(2026, 1, 1),
            },
            {"Identificador": 2, "Nome": "Sintético 2", "Horas": None},
        ),
    )


def test_dictionary_preserves_names_types_and_model_boundaries(tmp_path: Path) -> None:
    document = tmp_path / "dictionary.md"
    document.write_text(
        "## Anexo A — Exemplo\n### A.2 Dicionário de colunas\n#### Cadastro\n"
        "| Coluna | Tipo | Código | Construção |\n| --- | --- | --- | --- |\n"
        "| ID | inteiro | 6 | Modelo |\n| Nome com espaço | texto | 2 | DAX |\n"
        "### A.3 Relacionamentos\n| Ignorar | tipo-desconhecido | x | Modelo |\n"
        "## Anexo B — Exemplo\n### B.2 Dicionário de colunas\n#### Série\n"
        "| Valor | decimal/ponto flutuante | 8 | Modelo |\n"
        "## Anexo C — Fora do escopo\n### C.2 Dicionário de colunas\n#### Cadastro\n"
        "| Não ler | inteiro | 6 | Modelo |\n",
        encoding="utf-8",
    )
    result = read_dictionary(document, {"A": ["Cadastro"], "B": ["Série"]})
    assert result[0].columns == (
        Column("ID", "inteiro", False),
        Column("Nome com espaço", "texto", True),
    )
    assert result[1].model == "B"
    assert result[1].columns[0].postgres_type == "double precision"
    with pytest.raises(ValueError, match="ausente"):
        read_dictionary(document, {"A": ["Inexistente"]})
    with pytest.raises(ValueError, match="acadêmicos"):
        read_dictionary(document, {"C": ["Cadastro"]})


@pytest.mark.parametrize("value", ["", "nome\0inválido", "á" * 32])
def test_invalid_identifiers_are_refused(value: str) -> None:
    with pytest.raises(ValueError):
        identifier(value)


def test_sql_literals_preserve_text_without_interpreting_sql() -> None:
    assert identifier('Nome"; DROP SCHEMA x; --') == '"Nome""; DROP SCHEMA x; --"'
    assert literal("x'); DELETE FROM x; --") == "'x''); DELETE FROM x; --'"
    assert literal(None) == "NULL"
    assert literal(0) == "0"
    assert literal(False) == "FALSE"
    assert literal(datetime(2026, 1, 1)) == "'2026-01-01T00:00:00'"
    with pytest.raises(ValueError):
        literal(float("nan"))
    with pytest.raises(ValueError):
        literal("texto\x00")


def test_seed_is_reproducible_transactional_and_keeps_zero_distinct_from_null() -> None:
    sql = render_seed([sample()], seed=42)
    assert sql == render_seed([sample()], seed=42)
    assert "BEGIN;" in sql and "COMMIT;" in sql
    assert "current_database() <> 'vrac_sintetico'" in sql
    assert "inet_server_addr()" in sql
    assert "host(inet_server_addr()) NOT IN ('127.0.0.1', '::1')" in sql
    assert "CREATE SCHEMA IF NOT EXISTS" not in sql
    assert '"Horas" bigint' in sql
    assert "(1, 'Sintético d''Água', 0, '2026-01-01T00:00:00', NULL)" in sql
    assert "(2, 'Sintético 2', NULL, NULL, NULL)" in sql
    assert not any(word in sql for word in ("DROP ", "TRUNCATE ", "DELETE "))


@pytest.mark.parametrize("value", ["1", 1.1, True, 2**63])
def test_invalid_integer_values_fail_before_writing(value: object) -> None:
    table = SyntheticTable(
        Table("A", "Exemplo", (Column("ID", "inteiro", False),)), ({"ID": value},)
    )
    with pytest.raises(ValueError, match="incompatível"):
        render_seed([table], seed=42)


def test_recipe_cannot_add_undocumented_columns() -> None:
    table = sample()
    invalid = SyntheticTable(table.definition, ({"Coluna inventada": 10},))
    with pytest.raises(ValueError, match="ausente"):
        render_seed([invalid], seed=42)
    with pytest.raises(ValueError, match="distintas"):
        render_seed([table, table], seed=42)


def test_bundle_records_provenance_null_columns_and_refuses_overwrite(tmp_path: Path) -> None:
    document = tmp_path / "dictionary.md"
    document.write_text("Dicionário de teste sem dados reais.", encoding="utf-8")
    bundle = tmp_path / "bundle"
    write_bundle(bundle, [sample()], document=document, seed=42, scenarios={"synthetic": True})
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["synthetic"] is True
    assert manifest["document_sha256"] == hashlib.sha256(document.read_bytes()).hexdigest()
    assert (
        manifest["seed_sql_sha256"]
        == hashlib.sha256((bundle / "01-seed.sql").read_bytes()).hexdigest()
    )
    assert manifest["tables"][0]["always_null_columns"] == ["Cálculo pendente"]
    assert manifest["tables"][0]["calculated_columns"] == ["Cálculo pendente"]
    original = (bundle / "01-seed.sql").read_bytes()
    with pytest.raises(FileExistsError):
        write_bundle(bundle, [sample()], document=document, seed=43, scenarios={})
    assert (bundle / "01-seed.sql").read_bytes() == original


def test_runtime_rejects_tampered_bundle_before_starting_process(tmp_path: Path) -> None:
    document = tmp_path / "dictionary.md"
    document.write_text("Sintético.", encoding="utf-8")
    bundle = tmp_path / "bundle"
    write_bundle(bundle, [sample()], document=document, seed=42, scenarios={})
    (bundle / "02-check.sql").write_text("SELECT 1;", encoding="utf-8")
    (bundle / "01-seed.sql").write_text("SELECT 2;", encoding="utf-8")
    with pytest.raises(RuntimeErrorSafe, match="alterado"):
        operate("start", tmp_path, bundle, tmp_path / "bin", tmp_path / "openssl")


def test_runtime_does_not_inherit_database_connection_from_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PGHOST", "servidor-institucional-de-teste")
    monkeypatch.setenv("PGPASSWORD", "senha-ficticia-do-teste")
    monkeypatch.setenv("PGSERVICE", "outro-servico-ficticio")
    env = _environment(tmp_path)
    assert not set(env) & {"PGHOST", "PGPASSWORD", "PGSERVICE"}
    assert env["PGSSLMODE"] == "verify-full"
    assert env["PGSSLROOTCERT"] == str(tmp_path / "server.crt")
