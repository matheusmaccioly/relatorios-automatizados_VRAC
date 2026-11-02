"""Fluxos dos seis roteiros, totalmente offline e com cenários em memória."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from vrac.academic_ui import ALL_ANALYSES
from vrac.demo_data import DemoDataError

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_all_six_routes_generate_tables_charts_downloads_and_clear_on_filter_change() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception and "suite_results" not in app.session_state
    app.button(key="suite_load").click().run()
    assert not app.exception and not app.error
    assert app.selectbox(key="suite_analysis").value == ALL_ANALYSES
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert len(app.session_state["suite_results"]) == 5
    assert any(t.label == "R01 · Situação geral" for t in app.tabs)
    assert len(app.metric) > 10
    assert len(app.get("download_button")) > 20
    assert any("Simulação" in c.value or "Parcial" in c.value for c in app.caption)
    app.selectbox(key="suite_last").select("2026.1").run()
    assert "suite_results" not in app.session_state
    assert not app.metric
    assert not app.get("download_button")


def test_empty_department_and_invalid_range_are_explicit_without_fake_results() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.selectbox(key="suite_department").select("SINT-VAZIO").run()
    app.button(key="suite_load").click().run()
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert all(r.status == "Sem dados" for r in app.session_state["suite_results"])
    app.selectbox(key="suite_first").select("2026.2").run()
    app.selectbox(key="suite_last").select("2024.1").run()
    app.button(key="suite_run").click().run()
    assert not app.exception and app.error
    assert "suite_results" not in app.session_state
    assert not app.get("download_button")


def test_refresh_failure_removes_data_and_does_not_switch_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="suite_load").click().run()
    assert "suite_source" in app.session_state

    def fail(*args, **kwargs):
        raise DemoDataError("A origem selecionada está indisponível.")

    monkeypatch.setattr("vrac.academic_ui.load_academic_source", fail)
    app.button(key="suite_load").click().run()
    assert not app.exception and app.error
    assert "suite_source" not in app.session_state
    assert "suite_results" not in app.session_state
    assert not app.get("download_button")
