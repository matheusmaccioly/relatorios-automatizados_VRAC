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


def test_workload_period_invalidates_results_and_downloads() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="suite_load").click().run()
    app.button(key="suite_run").click().run()
    assert "suite_results" in app.session_state and app.get("download_button")
    app.selectbox(key="suite_workload_period").select("2026.1").run()
    assert "suite_results" not in app.session_state and not app.get("download_button")


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


def test_r01_can_be_selected_and_shows_all_breakdowns_and_details():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.selectbox(key="suite_analysis").select("R01 · Situação geral do departamento").run()
    app.button(key="suite_load").click().run()
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert len(app.get("vega_lite_chart")) == 3
    assert len(app.metric) == 1 and app.metric[0].value == "5"
    assert any("Estado das Horas Reais" in frame.value.columns for frame in app.dataframe)
    app.multiselect(key="suite_categories").select("Não informado").run()
    assert "suite_results" not in app.session_state and not app.get("download_button")
    app.button(key="suite_run").click().run()
    assert not app.exception and app.metric[0].value == "1"


def test_snapshot_refresh_and_origin_failure_remove_every_previous_result(monkeypatch):
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.selectbox(key="suite_analysis").select("R02 · Corpo docente geral e QP").run()
    app.button(key="suite_load").click().run()
    app.button(key="suite_run").click().run()
    assert app.metric and app.get("download_button")
    app.button(key="suite_load").click().run()
    assert not app.metric and not app.get("download_button")
    assert "suite_results" not in app.session_state
    app.button(key="suite_run").click().run()
    monkeypatch.setenv("VRAC_DEMO_SOURCE", "postgres")

    def fail(*args, **kwargs):
        raise DemoDataError("Origem selecionada indisponível; sem fallback.")

    monkeypatch.setattr("vrac.ui.load_demo_options", fail)
    app.run()
    assert not app.exception and app.error
    assert "suite_results" not in app.session_state and "suite_source" not in app.session_state
    assert not app.get("download_button")


def test_history_only_category_is_empty_in_r01_without_blocking_the_flow(monkeypatch):
    from dataclasses import replace

    from vrac.analyses.academic_fixture import load_fixture

    source = load_fixture("SINT-A")
    source = replace(
        source, history=tuple(replace(r, category="Categoria só histórica") for r in source.history)
    )
    monkeypatch.setattr("vrac.academic_ui.load_academic_source", lambda *a, **k: source)
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.selectbox(key="suite_analysis").select("R01 · Situação geral do departamento").run()
    app.button(key="suite_load").click().run()
    app.multiselect(key="suite_categories").select("Categoria só histórica").run()
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error and not app.metric
    assert any("não acrescentam vínculos" in i.value for i in app.info)
