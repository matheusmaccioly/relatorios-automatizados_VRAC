"""A visão docente mantém composição disponível e nunca reapresenta histórico antigo."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from vrac.demo_data import DemoDataError

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_failed_history_refresh_removes_old_charts_and_files_but_keeps_composition(monkeypatch):
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="overview_run").click().run()
    assert not app.exception and len(app.get("vega_lite_chart")) == 5
    original = __import__("vrac.ui", fromlist=["load_academic_source"]).load_academic_source

    def fail(*args, **kwargs):
        raise DemoDataError("Histórico sintético indisponível.")

    monkeypatch.setattr("vrac.ui.load_academic_source", fail)
    app.button(key="overview_run").click().run()
    assert not app.exception and not app.error
    assert "overview_history" not in app.session_state
    assert "overview_result" in app.session_state
    assert len(app.get("vega_lite_chart")) == 3
    assert all(
        not (button.key or "").startswith("overview_R03") for button in app.get("download_button")
    )
    assert any("Histórico indisponível" in warning.value for warning in app.warning)

    monkeypatch.setattr("vrac.ui.load_academic_source", original)
    app.button(key="overview_run").click().run()
    assert not app.exception and len(app.get("vega_lite_chart")) == 5
    assert "overview_history_error" not in app.session_state


def test_invalid_history_interval_only_blocks_history_and_changing_period_clears_results():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.selectbox(key="overview_first").select("2026.2").run()
    app.selectbox(key="overview_last").select("2024.1").run()
    app.button(key="overview_run").click().run()
    assert not app.exception and not app.error
    assert "overview_history" not in app.session_state
    assert app.metric[0].label == "Quantidade de professores"
    assert len(app.get("vega_lite_chart")) == 3
    assert any("Histórico indisponível" in warning.value for warning in app.warning)
    app.selectbox(key="overview_last").select("2026.2").run()
    assert "overview_result" not in app.session_state
    assert not app.get("download_button")


def test_main_faculty_page_and_history_workbench_can_keep_results_together():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="overview_run").click().run()
    app.selectbox(key="suite_analysis").select("R03 · Histórico semestral docente").run()
    app.button(key="suite_load").click().run()
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert "overview_history" in app.session_state and "suite_results" in app.session_state
    assert len(app.get("vega_lite_chart")) == 9
    keys = [button.key for button in app.get("download_button")]
    assert "overview_R03_monthly_history_csv" in keys
    assert "suite_R03_monthly_history_csv" in keys
