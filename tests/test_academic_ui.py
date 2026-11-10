"""Fluxos dos seis roteiros, totalmente offline e com cenários em memória."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from vrac.demo_data import DemoDataError

APP = Path(__file__).resolve().parents[1] / "app.py"


def open_analysis(code: str) -> AppTest:
    """Abre a análise pelo atalho da página inicial; a aba aberta já lê a base."""
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key=f"home_open_{code}").click().run()
    return app


def r01_tab(app: AppTest):
    return next(tab for tab in app.tabs if tab.label == "R01 · Situação geral")


def test_all_six_routes_generate_tables_charts_downloads_and_clear_on_filter_change() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception and "suite_results" not in app.session_state
    app.button(key="home_open_todas").click().run()
    assert not app.exception and not app.error
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert [r.kind for r in app.session_state["suite_results"]] == ["R02", "R03", "R04", "R05"]
    assert any(t.label == "R01 · Situação geral" for t in app.tabs)
    assert len(app.metric) > 10
    assert len(app.get("download_button")) > 20
    assert any("Simulação" in c.value or "Parcial" in c.value for c in app.caption)
    app.selectbox(key="suite_last").select("2026.1").run()
    assert "suite_results" not in app.session_state
    assert not app.metric
    assert not app.get("download_button")


def test_workload_period_invalidates_results_and_downloads() -> None:
    app = open_analysis("R04")
    app.button(key="suite_run").click().run()
    assert "suite_results" in app.session_state and app.get("download_button")
    app.selectbox(key="suite_workload_period").select("2026.1").run()
    assert "suite_results" not in app.session_state and not app.get("download_button")


def test_empty_department_and_invalid_range_are_explicit_without_fake_results() -> None:
    app = open_analysis("todas")
    app.selectbox(key="suite_department").select("SINT-VAZIO").run()
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
    app = open_analysis("todas")
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
    from vrac.analyses.verification import RULE_ID, Status

    app = open_analysis("todas")
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert app.session_state["suite_verification"].outcomes[RULE_ID].status != Status.FAILED
    r01 = r01_tab(app)
    assert len(r01.get("vega_lite_chart")) == 3
    assert len(r01.metric) == 1 and r01.metric[0].value == "5"
    assert any("Estado das Horas Reais" in frame.value.columns for frame in r01.dataframe)
    app.multiselect(key="suite_categories").select("Não informado").run()
    assert "suite_results" not in app.session_state and not app.get("download_button")
    app.button(key="suite_run").click().run()
    assert not app.exception and r01_tab(app).metric[0].value == "1"


def test_verification_is_offered_only_with_the_workload_analysis():
    app = open_analysis("R02")
    app.button(key="suite_run").click().run()
    assert not app.exception and "suite_verification" not in app.session_state


def test_snapshot_refresh_and_origin_failure_remove_every_previous_result(monkeypatch):
    app = open_analysis("R02")
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
    app = open_analysis("todas")
    app.multiselect(key="suite_categories").select("Categoria só histórica").run()
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error and not r01_tab(app).metric
    assert any("não acrescentam vínculos" in i.value for i in app.info)


def test_analysis_guidance_and_filter_summary_are_available_before_calculation():
    app = open_analysis("R06")
    assert any("Como evoluíram as matrículas e os alunos?" in text.value for text in app.markdown)
    assert "alunos_source" in app.session_state
    course_selector = app.multiselect(key="alunos_courses")
    course_selector.select(course_selector.options[0]).run()
    assert not app.exception and "alunos_results" not in app.session_state
    selected_filters = next(
        text.value for text in app.markdown if text.value.startswith("| Filtro | Valor |")
    )
    assert f"| Cursos | {app.multiselect(key='alunos_courses').value[0]} |" in selected_filters
    assert any("Recorte pronto" in message.value for message in app.info)


def test_reset_filters_keeps_loaded_snapshot_and_removes_results_and_downloads():
    app = open_analysis("todas")
    fingerprint = app.session_state["suite_source"].fingerprint
    app.selectbox(key="suite_first").select("2024.2").run()
    app.multiselect(key="suite_categories").select("Não informado").run()
    app.button(key="suite_run").click().run()
    assert not app.exception and app.get("download_button")
    app.button(key="suite_reset_filters").click().run()
    assert not app.exception and not app.error
    assert app.session_state["suite_source"].fingerprint == fingerprint
    assert app.selectbox(key="suite_first").value == app.selectbox(key="suite_first").options[0]
    assert not app.multiselect(key="suite_categories").value
    assert "suite_results" not in app.session_state and not app.get("download_button")
