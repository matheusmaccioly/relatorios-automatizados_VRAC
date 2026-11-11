"""Contratos offline da identidade local, da navegação e dos gráficos."""

import re
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest
import streamlit as st
from conftest import result_downloads
from matplotlib import pyplot as plt
from streamlit.testing.v1 import AppTest

from vrac.academic_ui import analysis_names
from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_fixture import load_fixture
from vrac.branding import load_branding, streamlit_theme
from vrac.charts import distribution_bars, render_png
from vrac.demo_data import DemoDataError
from vrac.navigation import AREAS, FACULTY, STUDENTS
from vrac.ui import FACULTY_PICKER, VIEW_HOME, VIEW_KEY, VIEWS
from vrac.ui_kit import session_cached
from vrac.web_charts import (
    BAR_THICKNESS,
    _reference_order,
    _text_on,
    interactive_bars,
    interactive_chart,
)

ROOT = Path(__file__).resolve().parents[1]


def test_generated_theme_and_local_fonts_match_the_branding_source() -> None:
    branding = load_branding()
    with (ROOT / ".streamlit" / "config.toml").open("rb") as stream:
        configuration = tomllib.load(stream)
    assert configuration["theme"] == streamlit_theme(branding.tokens)
    assert configuration["browser"]["gatherUsageStats"] is False
    assert configuration["server"]["enableStaticServing"] is True
    for font in branding.tokens["fonts"]:
        original = branding.root / font["file"]
        public = ROOT / "static" / "branding" / original.name
        assert public.read_bytes() == original.read_bytes()
    assert all(
        face["url"].startswith("app/static/branding/")
        for face in configuration["theme"]["fontFaces"]
    )
    assert (ROOT / "static" / "branding" / branding.logo.name).read_bytes() == (
        branding.logo.read_bytes()
    )
    assert branding.logo_url == f"app/static/branding/{branding.logo.name}"


def test_styles_use_only_the_authorized_palette_without_external_resources() -> None:
    branding = load_branding()
    styles = branding.styles
    used_colors = set(re.findall(r"#[0-9a-fA-F]{6}\b", styles))
    assert used_colors <= set(branding.tokens["colors"].values())
    assert "$" not in styles
    assert "url(" not in styles and "@import" not in styles


def test_reset_overview_removes_results_and_restores_dependent_filters() -> None:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.selectbox(key="overview_center").select("Centro sintético 2").run()
    assert app.selectbox(key="overview_department").value == "SINT-B"
    cadre = app.multiselect(key="overview_cadres").options[0]
    app.multiselect(key="overview_cadres").select(cadre).run()
    app.button(key="overview_run").click().run()
    assert not app.exception and "overview_result" in app.session_state
    assert app.get("download_button")
    app.button(key="overview_reset").click().run()
    assert not app.exception and not app.error
    assert app.selectbox(key="overview_center").value == "Todos os centros"
    assert app.selectbox(key="overview_department").value == "SINT-A"
    assert app.multiselect(key="overview_cadres").value == []
    for name in (
        "overview_result",
        "overview_history",
        "overview_generated",
        "overview_execution_id",
    ):
        assert name not in app.session_state
    assert not app.metric and not result_downloads(app)


def test_changed_overview_filters_explain_why_previous_results_were_cleared() -> None:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.button(key="overview_run").click().run()
    assert "overview_result" in app.session_state
    app.selectbox(key="overview_department").select("SINT-B").run()
    assert not app.exception and "overview_result" not in app.session_state
    assert not result_downloads(app)
    assert any("Os filtros mudaram" in message.value for message in app.info)


def _open_card(code: str) -> AppTest:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.button(key=f"home_open_{code}").click().run()
    assert not app.exception and not app.error
    return app


def _widget_keys(app: AppTest) -> set[str]:
    return {widget.key for widget in (*app.selectbox, *app.multiselect) if widget.key}


def test_chart_series_are_authorized_colors_in_a_fixed_order() -> None:
    branding = load_branding()
    assert set(branding.series) <= set(branding.tokens["colors"].values())
    assert len(set(branding.series)) == len(branding.series)
    assert branding.series[0] == branding.tokens["colors"]["blue"]


def test_tabs_group_the_analyses_by_area_with_coming_soon_last() -> None:
    assert VIEWS == (
        VIEW_HOME,
        "Docentes",
        "Alunos",
        "Financeira (em breve)",
        "Projetos patrocinados (em breve)",
    )
    codes = {item.code for area in AREAS for item in area.analyses}
    assert codes == {"panorama", "R02", "R03", "R04", "R05", "todas", "R06"}
    assert [area.available for area in AREAS] == [True, True, False, False]


def test_home_area_buttons_open_each_analysis_with_the_base_ready() -> None:
    app = _open_card("R04")
    assert app.session_state[VIEW_KEY] == FACULTY.tab
    assert app.session_state[FACULTY_PICKER] == "R04"
    assert "suite_source" in app.session_state and "alunos_source" not in app.session_state
    app.button(key="suite_run").click().run()
    assert not app.exception and app.metric
    app = _open_card("R06")
    assert app.session_state[VIEW_KEY] == STUDENTS.tab
    assert "alunos_source" in app.session_state and "suite_source" not in app.session_state


def test_home_shortcut_opens_the_faculty_view_without_reading_the_workbench_base() -> None:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.button(key="home_open_panorama").click().run()
    assert not app.exception and app.session_state[VIEW_KEY] == FACULTY.tab
    assert "suite_source" not in app.session_state


def test_starting_the_app_reads_no_analysis_base() -> None:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception and app.session_state[VIEW_KEY] == VIEW_HOME
    for name in ("suite_source", "alunos_source", "overview_result"):
        assert name not in app.session_state


@pytest.mark.parametrize(
    ("code", "result", "department_key"),
    [
        ("panorama", "overview_result", "overview_department"),
        ("R03", "suite_results", "suite_department"),
        ("R06", "alunos_results", "alunos_department"),
    ],
)
def test_quick_start_opens_the_area_and_calculates_for_the_department(
    code, result, department_key
) -> None:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.selectbox(key="home_analysis").select(code).run()
    app.selectbox(key="home_department").select("SINT-B").run()
    app.button(key="home_start").click().run()
    assert not app.exception and not app.error
    assert result in app.session_state
    assert app.selectbox(key=department_key).value == "SINT-B"


def test_card_failure_reports_the_error_without_loading_substitute_data(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise DemoDataError("Fonte sintética indisponível.")

    monkeypatch.setattr("vrac.academic_ui.load_academic_source", fail)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.button(key="home_open_R06").click().run()
    assert not app.exception and app.error
    assert "alunos_source" not in app.session_state and "alunos_results" not in app.session_state


def test_scope_change_reload_failure_removes_the_previous_snapshot(monkeypatch) -> None:
    app = _open_card("R06")
    app.button(key="alunos_run").click().run()
    assert "alunos_results" in app.session_state

    def fail(*args, **kwargs):
        raise DemoDataError("Fonte sintética indisponível.")

    monkeypatch.setattr("vrac.academic_ui.load_academic_source", fail)
    app.selectbox(key="alunos_center").select("Centro sintético 2").run()
    assert not app.exception and app.error
    assert "alunos_source" not in app.session_state and "alunos_results" not in app.session_state
    assert not result_downloads(app) or all(
        not (button.key or "").startswith("alunos_") for button in app.get("download_button")
    )


@pytest.mark.parametrize(
    ("code", "shown", "hidden"),
    [
        (
            "R02",
            {"suite_statuses", "suite_group_a_cadres", "suite_group_b_categories"},
            {
                "suite_first",
                "suite_workload_period",
                "suite_cadres",
                "suite_categories",
                "suite_courses",
            },
        ),
        (
            "R03",
            {"suite_first", "suite_last", "suite_cadres", "suite_categories"},
            {"suite_workload_period", "suite_group_a_cadres", "suite_courses"},
        ),
        (
            "R04",
            {"suite_workload_period", "suite_cadres", "suite_categories", "suite_statuses"},
            {"suite_first", "suite_last", "suite_group_a_cadres", "suite_courses"},
        ),
        (
            "R06",
            {"alunos_first", "alunos_last", "alunos_courses", "alunos_shifts"},
            {"alunos_workload_period", "alunos_cadres", "alunos_group_a_cadres", "suite_first"},
        ),
    ],
)
def test_each_analysis_shows_only_the_filters_it_uses(code, shown, hidden) -> None:
    keys = _widget_keys(_open_card(code))
    assert shown <= keys
    assert not hidden & keys


@pytest.mark.parametrize("kind", [AnalysisKind.WORKLOAD, AnalysisKind.STUDENTS])
def test_hidden_filters_keep_the_result_of_the_initial_form(kind) -> None:
    """Esconder filtros sem efeito não pode alterar o que a análise calcula."""
    prefix = "alunos" if kind == AnalysisKind.STUDENTS else "suite"
    app = _open_card(kind.value)
    app.button(key=f"{prefix}_run").click().run()
    source = app.session_state[f"{prefix}_source"]
    first, last = source.periods[0], source.periods[-1]
    expected = calculate(kind, source, AnalysisFilters(first, last, last))
    (result,) = app.session_state[f"{prefix}_results"]
    assert result.tables == expected.tables
    assert result.metrics == expected.metrics


def test_analysis_names_keep_the_selector_options() -> None:
    assert list(analysis_names().values()) == ["R01", "R02", "R03", "R04", "R05", "R06"]


def test_single_category_shows_the_number_instead_of_a_one_bar_chart() -> None:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.button(key="overview_run").click().run()
    assert app.session_state["overview_result"].by_department == (("SINT-A", 4),)
    assert not app.exception and len(app.get("vega_lite_chart")) == 5
    assert any(button.key == "overview_png_departamento" for button in app.get("download_button"))


def test_exports_are_only_drawn_when_requested(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("Arquivo desenhado sem pedido.")

    monkeypatch.setattr("vrac.academic_ui.render_png", fail)
    monkeypatch.setattr("vrac.faculty_presentation.render_png", fail)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.button(key="overview_run").click().run()
    assert not app.exception and app.get("download_button")


def test_render_png_closes_the_figure_even_when_saving_fails(monkeypatch) -> None:
    branding = load_branding()
    plt.close("all")

    def figure():
        return distribution_bars((("A", 1),), title="T", unit="u", branding=branding)

    assert render_png(figure).startswith(b"\x89PNG")
    assert not plt.get_fignums()

    def fail(*args, **kwargs):
        raise OSError("falha")

    monkeypatch.setattr("vrac.charts.figure_png", fail)
    with pytest.raises(OSError, match="falha"):
        render_png(figure)
    assert not plt.get_fignums()


def test_session_cache_reuses_only_the_same_execution() -> None:
    st.session_state.clear()
    calls = []

    def build() -> int:
        calls.append(1)
        return len(calls)

    first = {"Execução": "a"}
    assert session_cached("grafico", first, build) == 1
    assert session_cached("grafico", first, build) == 1
    assert session_cached("grafico", {"Execução": "b"}, build) == 2
    assert session_cached("outro", first, build) == 3
    assert session_cached("grafico", None, build) == 4
    assert session_cached("grafico", None, build) == 5
    st.session_state.clear()


def test_numeric_references_follow_value_order_with_missing_last() -> None:
    records = [{"Referência": value} for value in ("0", "20", "45", "6", "ausente")]
    assert _reference_order(records) == ["0", "6", "20", "45", "ausente"]
    assert _reference_order([{"Referência": "Grupo"}, {"Referência": "Outro"}]) is None


def test_labels_inside_marks_use_black_or_white_by_fill() -> None:
    colors = load_branding().tokens["colors"]
    assert _text_on(colors["blue"]) == "#FFFFFF"
    assert _text_on(colors["yellow"]) == "#000000"


def test_bars_are_thin_and_keep_the_value_at_the_tip() -> None:
    spec = interactive_bars(
        (("A", 3), ("B", 1)), label="Quadro", unit="vínculos", branding=load_branding()
    ).to_dict()
    bars, labels = spec["layer"]
    assert bars["mark"]["size"] == BAR_THICKNESS <= 24
    assert bars["mark"]["cornerRadiusEnd"] == 4
    assert labels["encoding"]["text"]["field"] == "Valor exibido"


def test_line_charts_show_every_series_at_the_hovered_reference() -> None:
    source = load_fixture("SINT-A")
    filters = AnalysisFilters("2024.1", "2026.2", "2026.2")
    result = calculate(AnalysisKind.STUDENTS, source, filters)
    specification = next(chart for chart in result.charts if chart.table == "students")
    serialized = interactive_chart(result, specification, load_branding()).to_dict()
    catcher = serialized["layer"][-1]
    assert catcher["mark"]["color"] == "transparent"
    titles = [item["title"] for item in catcher["encoding"]["tooltip"] if "title" in item]
    assert set(specification.series) <= set(titles)
    rows = catcher["data"]["values"]
    assert len(rows) == len({row["Referência"] for row in rows})
    assert all(f"serie_{i}" in rows[0] for i in range(len(specification.series)))


def test_monthly_line_labels_only_highlights_and_keeps_every_month_in_the_data() -> None:
    source = load_fixture("SINT-A")
    filters = AnalysisFilters("2024.1", "2026.2", "2026.2")
    result = calculate(AnalysisKind.HISTORY, source, filters)
    line = next(chart for chart in result.charts if chart.table == "monthly_history")
    table = next(item for item in result.tables if item.key == "monthly_history")
    serialized = interactive_chart(replace(result), line, load_branding()).to_dict()
    assert len(serialized["layer"][0]["data"]["values"]) == len(table.rows)
    assert len(serialized["layer"][1]["data"]["values"]) <= 4
