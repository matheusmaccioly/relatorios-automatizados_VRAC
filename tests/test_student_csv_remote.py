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
