"""Tela da composição docente sem navegador, banco ou conexão de rede.

Índices dos widgets, na ordem do script: selectbox 0/1 e botão 0 pertencem à seção
da fixture; a composição docente usa selectbox 2 a 5, o date_input 0 e o botão 1.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"

DEPARTMENT, PERIOD, RULE, GROUPING = 2, 3, 4, 5
RUN = 1


def start() -> AppTest:
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    return app


def test_faculty_section_computes_nothing_before_the_explicit_action() -> None:
    app = start()
    assert any("composição docente" in item.value.lower() for item in app.subheader)
    assert not app.dataframe
    assert not app.table
    assert any("Pendências registradas" in item.value for item in app.info)


def test_pending_rule_produces_a_partial_result_with_the_pendencies_on_screen() -> None:
    app = start()
    app.selectbox[GROUPING].select("Categoria do vínculo").run()
    app.button[RUN].click().run()
    assert not app.exception
    assert any("parcial" in item.value.lower() for item in app.warning)
    assert any("aceite_funcional_docente" in item.value for item in app.info)
    assert any("não aprovada" in item.value for item in app.markdown)
    table = app.dataframe[0].value
    assert "Situação do dado" in table.columns


def test_people_and_registrations_show_different_totals_for_the_same_scope() -> None:
    totals = {}
    for rule_label, basis in (
        ("Pessoas distintas presentes em qualquer mês do período — NÃO APROVADA", "pessoas"),
        (
            "Matrículas funcionais na última referência de cada vínculo — NÃO APROVADA",
            "matriculas",
        ),
    ):
        app = start()
        app.selectbox[RULE].select(rule_label).run()
        app.button[RUN].click().run()
        assert not app.exception
        table = app.dataframe[0].value
        totals[basis] = int(table.loc[table["Métrica"] == "Total do recorte", "Valor"].iloc[0])
    assert totals == {"pessoas": 2, "matriculas": 3}


def test_snapshot_rule_asks_for_a_date_and_other_rules_do_not() -> None:
    app = start()
    # A primeira candidata é uma foto: exige data explícita.
    assert app.date_input
    app.selectbox[RULE].select(
        "Pessoas distintas presentes em qualquer mês do período — NÃO APROVADA"
    ).run()
    assert not app.date_input


def test_changing_a_filter_removes_the_previous_faculty_result() -> None:
    app = start()
    app.button[RUN].click().run()
    assert app.dataframe
    app.selectbox[DEPARTMENT].select("SINT-B").run()
    assert not app.exception
    assert "faculty_result" not in app.session_state
    assert not app.dataframe


def test_period_without_records_is_explained_without_a_zero() -> None:
    app = start()
    app.selectbox[PERIOD].select("2026.2").run()
    app.button[RUN].click().run()
    assert not app.exception
    assert any("não significa zero" in item.value for item in app.info)
    table = app.dataframe[0].value
    assert table.loc[0, "Situação do dado"] == "Sem registros"
    assert table.loc[0, "Valor"] is None
    assert not app.metric


def test_downloads_carry_the_scope_and_are_offered_after_a_result() -> None:
    app = start()
    assert not app.get("download_button")
    app.button[RUN].click().run()
    buttons = app.get("download_button")
    assert len(buttons) == 2
    assert {item.label for item in buttons} == {"Baixar CSV", "Baixar JSON"}


def test_real_mode_never_reaches_the_faculty_section(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VRAC_DATA_MODE", "real")
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert "Dados reais bloqueados" in app.error[0].value
    assert not app.button
    assert not app.selectbox
    assert not app.dataframe
