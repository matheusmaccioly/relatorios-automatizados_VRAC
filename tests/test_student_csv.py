"""Fixtures exclusivamente sintéticas; nenhuma conexão com fontes institucionais."""

import csv
from dataclasses import replace
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from vrac.dev.faculty_csv import ImportErrorSafe
from vrac.dev.student_csv import COLUMNS, import_bundle, read_csv, summary


def event(**changes):
    row = dict(
        zip(
            COLUMNS,
            (
                "MATRICULADOS",
                "20261",
                "20261",
                "A" * 64,
                "IND",
                "CTC",
                "Centro fictício",
                "Graduação",
                "Bacharelado",
                "0001",
                "Curso fictício",
                "001",
                "Hab fictícia",
                "",
                "Vestibular  ",
                "NULL",
                "0",
                "0",
            ),
            strict=True,
        )
    )
    row.update(changes)
    return [row[c] for c in COLUMNS]


def load(tmp_path, rows):
    path = tmp_path / "fixture.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        csv.writer(stream, delimiter=";").writerows(rows)
    return read_csv(path, encoding="utf-8-sig", null_token="NULL", start=20261, end=20262)


def test_preserves_null_empty_codes_and_whitespace(tmp_path):
    bundle = load(tmp_path, [event()])
    row = dict(zip(COLUMNS, bundle.rows[0], strict=True))
    assert row["situacao_atual"] is None
    assert row["turno"] == ""
    assert row["curso_codigo"] == "0001"
    assert row["forma_ingresso"] == "Vestibular  "
    assert row["ingresso_cadastro_nulo"] == 0
    assert len(bundle.digest()) == 64


def test_preserves_duplicate_events_and_ingress_axis(tmp_path):
    bundle = load(
        tmp_path,
        [
            event(),
            event(),
            event(
                indicador="INGRESSANTES", periodo_linha="20272", forma_ingresso="Dupla Diplomacao"
            ),
        ],
    )
    assert summary(bundle)["linhas_duplicadas"] == 1
    assert bundle.rows[2][1:3] == (20261, 20272)


@pytest.mark.parametrize(
    "changes",
    [
        {"aluno_id": "1234567"},
        {"aluno_id": "NULL"},
        {"departamento_curso": "XXX"},
        {"periodo_eixo": "20263"},
        {"periodo_eixo": "20251"},
        {"periodo_linha": "20262"},
        {"indicador": "OUTRO"},
        {"ingresso_cadastro_nulo": "2"},
        {"indicador": "FORMADOS", "ingresso_cadastro_nulo": "1"},
        {"ajustes_individuais_informados": "-1"},
        {"curso": "invalido\x00"},
    ],
)
def test_rejects_invalid_rows_without_echoing_data(tmp_path, changes):
    with pytest.raises(ImportErrorSafe, match="registro 1") as exc:
        load(tmp_path, [event(**changes)])
    assert "A" * 64 not in str(exc.value)


def test_rejects_wrong_layout_empty_and_header(tmp_path):
    for rows in ([], [event()[:-1]], [list(COLUMNS)]):
        with pytest.raises(ImportErrorSafe):
            load(tmp_path, rows)


def test_scholarship_requires_matching_enrollment(tmp_path):
    with pytest.raises(ImportErrorSafe, match="Bolsistas"):
        load(tmp_path, [event(indicador="BOLSISTAS_MATRICULADOS")])
    assert len(load(tmp_path, [event(), event(indicador="BOLSISTAS_MATRICULADOS")]).rows) == 2


def test_inconsistent_adjustments(tmp_path):
    with pytest.raises(ImportErrorSafe, match="Metadado"):
        load(tmp_path, [event(), event(ajustes_individuais_informados="1")])


def test_import_tls_bound_parameters_and_verification(tmp_path, monkeypatch):
    import psycopg

    bundle = load(tmp_path, [event(curso="'; DROP TABLE nada; --")])
    connect = MagicMock()
    monkeypatch.setattr(psycopg, "connect", connect)
    cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchone.side_effect = [bundle.rows[0], None]
    batch = UUID("30000000-0000-4000-8000-000000000020")
    import_bundle(bundle, service="servico_ficticio", batch=batch)
    connect.assert_called_once_with(
        service="servico_ficticio", sslmode="verify-full", connect_timeout=15
    )
    assert cursor.execute.call_args_list[1].args[1][0] == batch
    assert "DROP TABLE" not in cursor.execute.call_args_list[1].args[0]
    cursor.copy.return_value.__enter__.return_value.write_row.assert_called_once_with(
        (batch, 1, *bundle.rows[0])
    )
    cursor.fetchone.side_effect = [replace(bundle, rows=(tuple([None] * 18),)).rows[0]]
    with pytest.raises(ImportErrorSafe, match="Conferência"):
        import_bundle(bundle, service="servico_ficticio", batch=batch)
    assert connect.return_value.__exit__.call_args.args[0] is ImportErrorSafe


def test_bad_encoding_and_null_choice(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_bytes(b"\xff\xff")
    with pytest.raises(ImportErrorSafe):
        read_csv(path, encoding="utf-8-sig", null_token="NULL", start=20261, end=20262)
    for token in ("", "0", "1", " "):
        with pytest.raises(ImportErrorSafe):
            read_csv(path, encoding="utf-8-sig", null_token=token, start=20261, end=20262)
