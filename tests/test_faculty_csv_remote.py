from uuid import UUID

import pytest
from psycopg import sql

from vrac.dev.faculty_csv import LAYOUTS
from vrac.dev.faculty_csv_remote import render_load


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
