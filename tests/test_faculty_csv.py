"""Casos inteiramente sintéticos; sem acesso aos CSVs institucionais."""

import csv
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest

from vrac.db import faculty_csv_reader
from vrac.demo_data import DemoDataError
from vrac.dev.faculty_csv import INTEGERS, LAYOUTS, NUMERICS, ImportErrorSafe, convert, read_bundle


@pytest.mark.parametrize("mismatch", [False, True])
def test_import_verifies_before_commit(monkeypatch, mismatch):
    import psycopg

    from vrac.dev.faculty_csv import import_bundle

    events = []
    row = ("IND", "A" * 64, 20261, "FICTICIO", Decimal("0"), None)

    class Copy:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def write_row(self, value):
            events.append(("copy", value))

    class Cursor(Copy):
        def execute(self, query, params=None):
            events.append(("query", params))

        def copy(self, query):
            return Copy()

        def fetchall(self):
            return [] if mismatch else [row]

    class Connection(Copy):
        def cursor(self):
            return Cursor()

        def __exit__(self, error_type, *args):
            events.append("rollback" if error_type else "commit")
            return False

    def connect(**kwargs):
        assert kwargs["sslmode"] == "verify-full"
        assert kwargs["service"] == "ficticio"
        return Connection()

    monkeypatch.setattr(psycopg, "connect", connect)
    batch = UUID("10000000-0000-4000-8000-000000000001")
    if mismatch:
        with pytest.raises(ImportErrorSafe, match="Conferência"):
            import_bundle({"horas_reais": [row]}, service="ficticio", batch=batch)
        assert events[-1] == "rollback"
    else:
        import_bundle({"horas_reais": [row]}, service="ficticio", batch=batch)
        assert events[-1] == "commit"
    assert ("copy", (batch, 1, *row)) in events


def make_bundle(directory: Path) -> None:
    for layout in LAYOUTS.values():
        values = []
        for column in layout.columns:
            value = "texto fictício"
            if column.endswith("_id"):
                value = "A" * 64
            elif column == "departamento_alocacao":
                value = "IND"
            elif column in NUMERICS:
                value = "0"
            elif column in INTEGERS:
                value = {"ano": "2026", "mes": "01", "semestre": "20261"}.get(column, "1")
            values.append(value)
        with (directory / layout.filename).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow(values)
            writer.writerow(values)  # duplicidade legítima deve ser preservada


def test_preserves_duplicates_and_opaque_competence(tmp_path):
    make_bundle(tmp_path)
    data = read_bundle(tmp_path, encoding="utf-8-sig", null_token="NULL")
    assert all(len(rows) == 2 for rows in data.values())
    assert data["cadastro"][0][-1] == Decimal("0")
    assert data["historico_cargos"][0][2] == "texto fictício"


def test_null_zero_and_empty_are_distinct():
    assert convert("horas_reais", "NULL", "NULL") is None
    assert convert("horas_reais", "0", "NULL") == Decimal(0)
    assert convert("categoria", "", "NULL") == ""
    with pytest.raises(ValueError):
        convert("horas_reais", "", "NULL")


@pytest.mark.parametrize(
    "column,value",
    [
        ("horas_reais", "NaN"),
        ("horas_reais", "1,5"),
        ("vinculo_id", "123"),
        ("departamento_alocacao", "OUTRO"),
        ("mes", "13"),
        ("semestre", "20251"),
        ("ativo", "2"),
    ],
)
def test_invalid_values_are_rejected(column, value):
    with pytest.raises(ValueError):
        convert(column, value, "NULL")


def test_orphan_is_rejected_without_leaking_value(tmp_path):
    make_bundle(tmp_path)
    path = tmp_path / LAYOUTS["horas_reais"].filename
    path.write_text(
        path.read_text(encoding="utf-8-sig").replace("A" * 64, "B" * 64), encoding="utf-8"
    )
    with pytest.raises(ImportErrorSafe, match="vínculo sem cadastro") as error:
        read_bundle(tmp_path, encoding="utf-8-sig", null_token="NULL")
    assert "B" * 64 not in str(error.value)


def test_wrong_column_count(tmp_path):
    make_bundle(tmp_path)
    (tmp_path / LAYOUTS["cadastro"].filename).write_text("a;b\n", encoding="utf-8")
    with pytest.raises(ImportErrorSafe):
        read_bundle(tmp_path, encoding="utf-8-sig", null_token="NULL")


def test_ambiguous_alias_rejected(tmp_path):
    make_bundle(tmp_path)
    (tmp_path / "04_historico_cargos_com_antecedentes.csv").touch()
    with pytest.raises(ImportErrorSafe, match="Dois arquivos"):
        read_bundle(tmp_path, encoding="utf-8-sig", null_token="NULL")


def test_reader_paginates_and_rejects_wrong_scope(monkeypatch):
    batch = UUID("10000000-0000-4000-8000-000000000001")
    calls = []
    bad = False

    def rpc(name, params):
        calls.append(params["p_apos"])
        row = dict.fromkeys(LAYOUTS["horas_reais"].columns)
        row["departamento_alocacao"] = "ECO" if bad else "IND"
        items = [dict(row, linha=n) for n in range(1, 1001)] if params["p_apos"] == 0 else []
        result = {
            "synthetic": False,
            "origin": "institucional_pseudonimizada",
            "batch": str(batch),
            "component": "horas_reais",
            "rows": items,
        }
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=result))

    monkeypatch.setattr(
        faculty_csv_reader,
        "current_session",
        lambda: SimpleNamespace(client=SimpleNamespace(rpc=rpc)),
    )
    assert (
        len(
            faculty_csv_reader.load_component(
                batch=batch, component="horas_reais", department="IND"
            )
        )
        == 1000
    )
    assert calls == [0, 1000]
    bad = True
    with pytest.raises(DemoDataError):
        faculty_csv_reader.load_component(batch=batch, component="horas_reais", department="IND")
