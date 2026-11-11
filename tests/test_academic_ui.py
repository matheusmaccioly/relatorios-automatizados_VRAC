"""Fluxos dos seis roteiros, totalmente offline e com cenários em memória."""

from pathlib import Path

import pytest
from conftest import result_downloads
from streamlit.testing.v1 import AppTest

from vrac.demo_data import DemoDataError

APP = Path(__file__).resolve().parents[1] / "app.py"


def open_analysis(code: str) -> AppTest:
    """Abre a análise pelo atalho da página inicial; a aba aberta já lê a base."""
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key=f"home_open_{code}").click().run()
    return app


def r01_tab(app: AppTest):
    return next(tab for tab in app.tabs if tab.label == "Análise Geral dos professores")


def test_all_six_routes_generate_tables_charts_downloads_and_clear_on_filter_change() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception and "suite_results" not in app.session_state
    app.button(key="home_open_todas").click().run()
    assert not app.exception and not app.error
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert [r.kind for r in app.session_state["suite_results"]] == [
        "R02",
        "R03",
        "R04",
        "R05",
        "R06",
    ]
    assert any(t.label == "Análise Geral dos professores" for t in app.tabs)
    assert len(app.metric) > 10
    assert len(app.get("download_button")) > 20
    assert any("Situação: " in c.value for c in app.caption)
    app.selectbox(key="suite_last").select("2026.1").run()
    assert "suite_results" not in app.session_state
    assert not app.metric
    assert not result_downloads(app)


def test_workload_period_invalidates_results_and_downloads() -> None:
    app = open_analysis("R04")
    app.button(key="suite_run").click().run()
    assert "suite_results" in app.session_state and app.get("download_button")
    app.selectbox(key="suite_workload_period").select("2026.1").run()
    assert "suite_results" not in app.session_state and not result_downloads(app)


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
    assert not result_downloads(app)


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
    assert not result_downloads(app)


def test_r01_can_be_selected_and_shows_all_breakdowns_and_details():
    from vrac.analyses.verification import RULE_ID, Status

    app = open_analysis("todas")
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert app.session_state["suite_verification"].outcomes[RULE_ID].status != Status.FAILED
    r01 = r01_tab(app)
    assert len(r01.get("vega_lite_chart")) == 3
    # Quadro vazio fica fora pelo filtro de página do painel.
    assert len(r01.metric) == 1 and r01.metric[0].value == "4"
    assert any("Estado das Horas Reais" in frame.value.columns for frame in r01.dataframe)
    app.multiselect(key="suite_categories").select("PROF QCP").run()
    assert "suite_results" not in app.session_state and not result_downloads(app)
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
    assert not app.metric and not result_downloads(app)
    assert "suite_results" not in app.session_state
    app.button(key="suite_run").click().run()
    monkeypatch.setenv("VRAC_DEMO_SOURCE", "postgres")

    def fail(*args, **kwargs):
        raise DemoDataError("Origem selecionada indisponível; sem fallback.")

    monkeypatch.setattr("vrac.ui.load_demo_options", fail)
    app.run()
    assert not app.exception and app.error
    assert "suite_results" not in app.session_state and "suite_source" not in app.session_state
    assert not result_downloads(app)


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
    # O aviso fica no ícone de informação da R01, não numa faixa na tela.
    assert any("não acrescentam vínculos" in h.value for h in app.get("html"))


def test_analysis_guidance_and_filter_summary_are_available_before_calculation():
    app = open_analysis("R06")
    assert any("Como evoluíram os alunos matriculados" in text.value for text in app.markdown)
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
    assert "suite_results" not in app.session_state and not result_downloads(app)


def test_default_filters_follow_dashboard_status_and_qp_group():
    from dataclasses import replace

    from vrac.academic_ui import default_filters
    from vrac.analyses.academic_fixture import load_fixture

    source = load_fixture("SINT-A")
    register = tuple(replace(r, status="ATIVO") for r in source.faculty.register)
    source = replace(source, faculty=replace(source.faculty, register=register))
    filters = default_filters(source)
    assert filters.statuses == ("ATIVO",)
    assert (filters.group_a_name, filters.group_a_cadres) == ("QP", ("PROF PRINCIPAL",))
    assert (filters.group_b_name, filters.group_b_cadres) == ("Geral", ())


def test_comparison_screen_offers_two_groups_with_qp_and_general_by_default():
    app = open_analysis("R02")
    assert app.text_input(key="suite_group_a_name").value == "QP"
    assert app.text_input(key="suite_group_b_name").value == "Geral"
    assert app.multiselect(key="suite_group_a_cadres").value == ["PROF PRINCIPAL"]
    assert app.multiselect(key="suite_group_b_cadres").value == []
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    (result,) = app.session_state["suite_results"]
    assert [m.label for m in result.metrics] == ["QP", "Geral", "QP em % de Geral"]
    app.text_input(key="suite_group_b_name").input("Horistas").run()
    app.multiselect(key="suite_group_b_cadres").select("PROF HORISTA").run()
    assert "suite_results" not in app.session_state
    app.button(key="suite_run").click().run()
    (result,) = app.session_state["suite_results"]
    assert [m.label for m in result.metrics] == ["QP", "Horistas", "Em ambos os grupos"]
