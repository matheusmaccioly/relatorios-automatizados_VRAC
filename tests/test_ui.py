"""Verificações locais da tela sem navegador, banco ou conexão de rede."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_demo_is_identified_and_loads_only_on_explicit_action() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert "DEMONSTRAÇÃO" in app.warning[0].value
    assert not app.dataframe
    app.button[0].click().run()
    assert not app.exception
    assert len(app.dataframe) == 2
    assert app.table[0].value.iloc[0]["Modo"] == "Sintético"
    assert app.table[0].value.iloc[0]["Departamento"] == "SINT-A"


def test_changing_either_filter_removes_previous_data() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    for widget, value in [(0, "SINT-B"), (1, "2025.2")]:
        app.button[0].click().run()
        assert app.dataframe
        app.selectbox[widget].select(value).run()
        assert not app.exception
        assert not app.dataframe
        assert not app.table
        assert "demo_data" not in app.session_state


def test_empty_period_is_explained_without_a_zero_result() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.selectbox[1].select("2026.2").run()
    app.button[0].click().run()
    assert not app.exception
    assert not app.dataframe
    assert app.table[0].value.iloc[0]["Período"] == "2026.2"
    assert any("Ausência de registros não significa zero" in item.value for item in app.info)
    assert not app.metric


def test_real_mode_never_loads_demo_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VRAC_DATA_MODE", "real")

    def forbidden_loader(*args: object, **kwargs: object) -> None:
        pytest.fail("Dados fictícios não podem ser carregados em modo real.")

    monkeypatch.setattr("vrac.ui.load_demo_data", forbidden_loader)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert "Dados reais bloqueados" in app.error[0].value
    assert not app.button
    assert not app.dataframe
    assert not app.warning


def test_invalid_ui_configuration_stops_without_leaking_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VRAC_DATA_MODE", "valor-sensivel-de-teste")
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert "Configuração inválida" in app.error[0].value
    assert "valor-sensivel-de-teste" not in app.error[0].value
    assert not app.button
    assert not app.dataframe
