from uuid import UUID

import pytest
from psycopg import sql

from vrac.dev.faculty_csv import LAYOUTS
from vrac.dev.faculty_csv_remote import CHUNK, load_in_chunks, render_chunk, render_load


def test_payload_cannot_change_sql_or_templates():
    batch = UUID("10000000-0000-4000-8000-000000000001")
    bundle = {key: [] for key in LAYOUTS}
    text = "D'Ávila \\ {{batch}}'); DROP SCHEMA public; --"
    row = dict.fromkeys(LAYOUTS["cadastro"].columns)
    row.update(nome_ficticio=text, departamento_alocacao="IND", vinculo_id="A" * 64)
    bundle["cadastro"] = [tuple(row.values())]
    rendered = render_load(bundle, batch)
    assert rendered.startswith("BEGIN;") and rendered.endswith("COMMIT;")
    assert rendered.count("PREPARE vrac_csv_rows(jsonb)") == 7
    assert rendered.count("EXCEPT ALL") == 14
    assert "D''Ávila" in rendered
    assert "{{batch}}" in rendered  # literal de origem preservado, não interpretado
    assert sql.Literal(str(batch)).as_string() in rendered
    assert "vrac_sintetico" not in rendered and "vrac_app" not in rendered


def test_incomplete_bundle_is_rejected():
    with pytest.raises(ValueError, match="incompleto"):
        render_load({}, UUID(int=1))


def test_chunked_load_creates_blocked_batch_checks_each_range_and_writes_manifest_last():
    batch = UUID("10000000-0000-4000-8000-000000000002")
    bundle = {key: [] for key in LAYOUTS}
    row = dict.fromkeys(LAYOUTS["historico_mensal"].columns)
    row.update(departamento_alocacao="IND", vinculo_id="A" * 64, ano=2022, mes=1)
    bundle["historico_mensal"] = [tuple(row.values())] * (CHUNK + 1)
    statements = []
    counts = load_in_chunks(bundle, batch, statements.append)
    assert counts["historico_mensal"] == CHUNK + 1
    assert statements[0].startswith("BEGIN; INSERT INTO vrac_docentes.cargas")
    blocks = [s for s in statements if "jsonb_populate_recordset" in s]
    assert len(blocks) == 2
    assert f"linha > 0 AND linha <= {CHUNK}" in blocks[0]
    assert f"linha > {CHUNK} AND linha <= {CHUNK + 1}" in blocks[1]
    assert all("NOT liberada" in s and s.count("EXCEPT ALL") == 2 for s in blocks)
    assert "vrac_docentes.arquivos" in statements[-1] and "Contagem divergente" in statements[-1]
    assert not any("liberada=true" in s.replace(" ", "") for s in statements)


def test_chunk_payload_cannot_change_sql():
    text = "D'Ávila \ {{batch}}'); DROP SCHEMA public; --"
    row = dict.fromkeys(LAYOUTS["cadastro"].columns, None) | {"nome_ficticio": text}
    rendered = render_chunk("cadastro", [row], UUID(int=1), 0)
    assert "D''Ávila" in rendered and "{{batch}}" in rendered
    with pytest.raises(ValueError):
        render_chunk("outra; DROP", [row], UUID(int=1), 0)
    with pytest.raises(ValueError):
        render_chunk("cadastro", [row] * (CHUNK + 1), UUID(int=1), 0)
