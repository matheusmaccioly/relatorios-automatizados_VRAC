"""Filtros Centro > Departamento e invalidação das análises, sem banco ou navegador."""

import csv
import io
from dataclasses import replace
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from vrac.analyses.academic_data import ALL_DEPARTMENTS
from vrac.analyses.export import detail_csv
from vrac.demo_data import DemoOptions, load_academic_source, load_faculty_source
from vrac.department_hierarchy import UNKNOWN_CENTER, hierarchy_for_departments
from vrac.settings import Settings

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.mark.parametrize("prefix", ["overview", "alunos"])
def test_center_limits_departments_and_resets_selection_outside_its_scope(prefix) -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.selectbox(key=f"{prefix}_department").select("SINT-B").run()
    assert not app.exception
    app.selectbox(key=f"{prefix}_center").select("Centro sintético 1").run()
    assert not app.exception and not app.error
    departments = app.selectbox(key=f"{prefix}_department")
    assert departments.options == ["SINT-A", "SINT-VAZIO", ALL_DEPARTMENTS]
    assert departments.value == "SINT-A"
    app.selectbox(key=f"{prefix}_center").select("Centro sintético 2").run()
    assert app.selectbox(key=f"{prefix}_department").options == ["SINT-B", ALL_DEPARTMENTS]
    assert app.selectbox(key=f"{prefix}_department").value == "SINT-B"


def test_overview_all_departments_is_limited_to_center_in_screen_and_csv() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.selectbox(key="overview_center").select("Centro sintético 1").run()
    app.selectbox(key="overview_department").select(ALL_DEPARTMENTS).run()
    app.button(key="overview_run").click().run()
    assert not app.exception and not app.error
    overview = app.session_state["overview_result"]
    assert overview.department == "Centro sintético 1 · Todos os departamentos"
    assert overview.total == 5
    assert {row.department for row in overview.detail} == {"SINT-A"}
    assert {name for name, _ in overview.by_department} == {"SINT-A"}
    assert len(app.get("vega_lite_chart")) == 5
    assert app.get("download_button")
    content = detail_csv(overview, app.session_state["overview_generated"]).decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(content), delimiter=";"))
    assert ["Identificação", "Departamento", overview.department] in rows
    detail_start = next(
        i for i, row in enumerate(rows) if row[:2] == ["Departamento", "Matrícula fictícia"]
    )
    assert {row[0] for row in rows[detail_start + 1 :]} == {"SINT-A"}
    assert any("Centro sintético 1" in item.value for item in app.caption)
    app.selectbox(key="overview_center").select("Centro sintético 2").run()
    assert not app.exception and not app.error
    assert "overview_result" not in app.session_state
    assert "overview_history" not in app.session_state
    assert not app.metric and not app.get("download_button")


def test_workbench_center_change_replaces_snapshot_and_removes_results() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="home_open_todas").click().run()
    app.selectbox(key="suite_center").select("Centro sintético 1").run()
    app.selectbox(key="suite_department").select(ALL_DEPARTMENTS).run()
    app.button(key="suite_load").click().run()
    source = app.session_state["suite_source"]
    assert source.department == "Centro sintético 1 · Todos os departamentos"
    assert {row.department for row in source.faculty.register} == {"SINT-A"}
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert app.metric[0].value == "5" and app.get("download_button")
    filters = next(t.value for t in app.table if "Filtro" in t.value.columns)
    assert filters.set_index("Filtro").loc["Centro", "Valor"] == "Centro sintético 1"
    assert (
        filters.set_index("Filtro").loc["Departamentos efetivos", "Valor"] == "SINT-A, SINT-VAZIO"
    )
    app.selectbox(key="suite_center").select("Centro sintético 2").run()
    assert not app.exception and not app.error
    for key in ("suite_results", "suite_overview", "suite_generated"):
        assert key not in app.session_state
    replaced = app.session_state["suite_source"]
    assert replaced.department.startswith("Centro sintético 2")
    assert replaced.fingerprint != source.fingerprint
    assert not app.metric and not app.get("download_button")


def test_postgres_without_center_mapping_keeps_explicit_unknown_group(monkeypatch) -> None:
    monkeypatch.setenv("VRAC_DEMO_SOURCE", "postgres")
    hierarchy = hierarchy_for_departments(
        ("SINT-A", "SINT-B", "SINT-VAZIO"), source="PostgreSQL sintético"
    )
    monkeypatch.setattr(
        "vrac.ui.load_demo_options",
        lambda _: DemoOptions(("SINT-A", "SINT-B"), ("2026.1",), "2026.1", hierarchy.source),
    )
    for module in ("vrac.ui", "vrac.academic_ui"):
        monkeypatch.setattr(f"{module}.load_department_hierarchy", lambda _: hierarchy)

    calls = []

    def faculty(settings, **arguments):
        calls.append(arguments)
        return replace(load_faculty_source(Settings(), **arguments), source=hierarchy.source)

    def academic(settings, **arguments):
        calls.append(arguments)
        source = load_academic_source(Settings(), **arguments)
        return replace(source, faculty=replace(source.faculty, source=hierarchy.source))

    monkeypatch.setattr("vrac.ui.load_faculty_source", faculty)
    monkeypatch.setattr("vrac.ui.load_academic_source", academic)
    monkeypatch.setattr("vrac.academic_ui.load_academic_source", academic)
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="home_open_todas").click().run()
    assert not app.exception and not app.error
    assert app.selectbox(key="suite_center").options == ["Todos os centros", UNKNOWN_CENTER]
    app.selectbox(key="suite_center").select(UNKNOWN_CENTER).run()
    app.selectbox(key="suite_department").select(ALL_DEPARTMENTS).run()
    app.button(key="suite_load").click().run()
    assert not app.exception and not app.error
    assert app.session_state["suite_source"].department == (
        "Centro não informado · Todos os departamentos"
    )
    assert calls[-1] == {
        "department": "Centro não informado · Todos os departamentos",
        "departments": ("SINT-A", "SINT-B", "SINT-VAZIO"),
    }
    assert any("mapeamento de centros está pendente" in item.value for item in app.caption)
