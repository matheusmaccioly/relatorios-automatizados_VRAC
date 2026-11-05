"""R06 na UI: filtros, proveniência e invalidação, sem PostgreSQL ou navegador real."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from vrac.analyses.academic_data import ALL_DEPARTMENTS
from vrac.demo_data import DemoDataError

APP = Path(__file__).resolve().parents[1] / "app.py"
R06 = "R06 · Evolução de matrículas e alunos"


def loaded_r06():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.selectbox(key="suite_analysis").select(R06).run()
    app.button(key="suite_load").click().run()
    return app


def assert_calculated(app):
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert len(app.session_state["suite_results"]) == 1
    assert len(app.metric) == 4 and app.get("download_button")
    assert app.session_state["suite_results"][0].source == "Memória"


def assert_invalidated(app):
    assert not app.exception
    assert "suite_results" not in app.session_state
    assert "suite_generated" not in app.session_state
    assert not app.metric and not app.get("download_button")


def test_r06_every_academic_filter_removes_previous_results_and_downloads():
    app = loaded_r06()
    assert_calculated(app)
    for key in (
        "suite_courses",
        "suite_qualifications",
        "suite_shifts",
        "suite_levels",
        "suite_entries",
    ):
        selector = app.multiselect(key=key)
        selector.select(selector.options[0]).run()
        assert_invalidated(app)
        assert "suite_source" in app.session_state
        assert_calculated(app)
    for key, value in (("suite_first", "2024.2"), ("suite_last", "2026.1")):
        app.selectbox(key=key).select(value).run()
        assert_invalidated(app)
        assert_calculated(app)
    filters = next(
        table.value for table in app.table if list(table.value.columns) == ["Filtro", "Valor"]
    )
    effective = dict(zip(filters["Filtro"], filters["Valor"], strict=True))
    result = app.session_state["suite_results"][0]
    assert effective["Cursos"] == ", ".join(result.filters.courses)
    assert effective["Referência inicial"] == result.filters.first_period
    assert effective["Referência final"] == result.filters.last_period


def test_r06_center_department_and_refresh_failure_remove_old_downloads(monkeypatch):
    app = loaded_r06()
    assert_calculated(app)
    app.selectbox(key="suite_center").select("Centro sintético 2").run()
    assert_invalidated(app)
    assert app.session_state["suite_source"].department.startswith("Centro sintético 2")
    app.selectbox(key="suite_department").select(ALL_DEPARTMENTS).run()
    app.button(key="suite_load").click().run()
    assert_calculated(app)
    source = app.session_state["suite_source"]
    assert {r.department for r in (*source.students, *source.student_history)} == {"SINT-B"}
    app.selectbox(key="suite_department").select("SINT-B").run()
    assert_invalidated(app)
    app.button(key="suite_load").click().run()
    assert_calculated(app)

    def fail(*args, **kwargs):
        raise DemoDataError("PostgreSQL sintético indisponível; nenhum exemplo foi carregado.")

    monkeypatch.setattr("vrac.academic_ui.load_academic_source", fail)
    app.button(key="suite_load").click().run()
    assert_invalidated(app)
    assert app.error and "suite_source" not in app.session_state


def test_r06_uses_interactive_charts_and_retains_png_downloads():
    app = loaded_r06()
    initial_images = len(app.get("imgs"))
    assert_calculated(app)
    result = app.session_state["suite_results"][0]
    assert len(app.get("vega_lite_chart")) == len(result.charts)
    assert len(app.get("imgs")) == initial_images
    assert sum(
        button.label == "Baixar gráfico (PNG)" for button in app.get("download_button")
    ) == len(result.charts)
