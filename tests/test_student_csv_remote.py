from uuid import UUID

import pytest

from vrac.dev.student_csv_remote import render_chunk


def test_chunk_escapes_payload_and_keeps_ordinals():
    text = "D'Ávila \\ {{batch}}'); DROP SCHEMA public; --"
    rendered = render_chunk(((text, None, "", "001"),), UUID(int=1), 5000)
    assert "D''Ávila" in rendered
    assert "{{batch}}" in rendered  # conteúdo literal não reinterpretado
    assert "5000" in rendered and "5001" in rendered
    assert rendered.count("EXCEPT ALL") == 2
    assert "BEGIN;" in rendered and rendered.endswith("COMMIT;\n")
    assert "NOT liberada" in rendered
    assert "vrac_docentes" not in rendered and "vrac_sintetico" not in rendered


def test_chunk_limits():
    for rows, offset in (((), 0), (((),), -1), (((),) * 5001, 0)):
        with pytest.raises(ValueError):
            render_chunk(rows, UUID(int=1), offset)


def test_load_fills_filter_options_while_batch_is_blocked(monkeypatch):
    from vrac.dev import student_csv_remote as remote
    from vrac.dev.student_csv import COLUMNS, StudentBundle

    row = ["MATRICULADOS", 20261, 20261, "A" * 64, "DIR", *[None] * (len(COLUMNS) - 7), 0, 0]
    bundle = StudentBundle((tuple(row),), 20261, 20262, "utf-8-sig", "NULL")
    batch = UUID("10000000-0000-4000-8000-000000000003")
    executed = []

    def query(*, sql=None, path=None, read_only=True):
        if path is not None:
            executed.append(path.read_text(encoding="utf-8"))
            return []
        if "count(*)" in sql:
            return [{"rows": 1, "first": 1, "last": 1}]
        return [{"linhas": 1, "hash_conteudo": bundle.digest(), "liberada": False}]

    monkeypatch.setattr(remote, "remote_query", query)
    monkeypatch.setattr(remote, "existing_fingerprints", lambda: {})
    result = remote.run_load(bundle, batch)
    assert result["liberada"] is False
    assert "preencher_opcoes_filtros" in executed[-1]
    assert all("preencher_opcoes_filtros" not in text for text in executed[:-1])
