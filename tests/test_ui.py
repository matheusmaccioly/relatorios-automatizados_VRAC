"""Verificações locais da tela sem navegador, banco ou conexão de rede."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from vrac.demo_data import DemoDataError, DemoOptions
from vrac.synthetic import SyntheticDataset

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(autouse=True)
def memory_faculty_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """A aba R01 usa a fixture em memória; nenhum teste de tela abre o PostgreSQL."""
    from vrac.analyses import faculty_overview_fixture as fixture
    from vrac.department_hierarchy import hierarchy_for_departments

    hierarchy = hierarchy_for_departments(
        fixture.DEPARTMENTS, source="Memória", synthetic_centers=True
    )
    monkeypatch.setattr("vrac.ui.load_department_hierarchy", lambda _: hierarchy)
    monkeypatch.setattr("vrac.academic_ui.load_department_hierarchy", lambda _: hierarchy)
    monkeypatch.setattr(
        "vrac.ui.load_faculty_source", lambda _, *, department: fixture.load_fixture(department)
    )


def test_demo_is_identified_and_loads_only_on_explicit_action() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert "DEMONSTRAÇÃO" in app.warning[0].value
    assert not app.dataframe
    app.button(key="demo_show").click().run()
    assert not app.exception
    assert len(app.dataframe) == 2
    assert app.table[0].value.iloc[0]["Modo"] == "Sintético"
    assert app.table[0].value.iloc[0]["Departamento"] == "SINT-A"


def test_missing_value_is_labeled_and_distinct_from_zero() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.button(key="demo_show").click().run()
    hours = app.dataframe[0].value["Horas Reais fictícias (h/semana)"].tolist()
    assert sorted(hours) == ["0", "4", "4", "ausente"]
    students = app.dataframe[1].value["Matrículas fictícias"].tolist()
    assert "0" in students
    assert "None" not in students and "nan" not in students


def test_changing_either_filter_removes_previous_data() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    for widget, value in [("demo_department", "SINT-B"), ("demo_period", "2025.2")]:
        app.button(key="demo_show").click().run()
        assert app.dataframe
        app.selectbox(key=widget).select(value).run()
        assert not app.exception
        assert not app.dataframe
        assert not app.table
        assert "demo_data" not in app.session_state


def test_empty_period_is_explained_without_a_zero_result() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.selectbox(key="demo_period").select("2026.2").run()
    app.button(key="demo_show").click().run()
    assert not app.exception
    assert not app.dataframe
    assert app.table[0].value.iloc[0]["Período"] == "2026.2"
    assert any("Ausência de registros não significa zero" in item.value for item in app.info)
    assert not app.metric


def test_real_mode_never_loads_demo_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VRAC_DATA_MODE", "real")

    def forbidden_loader(*args: object, **kwargs: object) -> None:
        pytest.fail("Dados fictícios não podem ser carregados em modo real.")

    monkeypatch.setattr("vrac.ui.load_selected_demo", forbidden_loader)
    monkeypatch.setattr("vrac.ui.load_demo_options", forbidden_loader)
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


def test_postgres_empty_selection_and_one_empty_table_are_handled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    from vrac.settings import Settings
    from vrac.synthetic import load_demo_data

    monkeypatch.setenv("VRAC_DEMO_SOURCE", "postgres")
    monkeypatch.setattr(
        "vrac.ui.load_demo_options",
        lambda _: DemoOptions(
            ("SINT-A", "SINT-VAZIO"), ("2026.1",), "2026.1", "PostgreSQL sintético"
        ),
    )
    selected = replace(load_demo_data(Settings()), allocations=(), source="PostgreSQL sintético")
    monkeypatch.setattr("vrac.ui.load_selected_demo", lambda *a, **k: selected)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.button(key="demo_show").click().run()
    assert not app.exception and len(app.dataframe) == 1
    assert app.table[0].value.iloc[0]["Origem"] == "PostgreSQL sintético"
    assert "Horas Reais fictícias" in app.dataframe[0].value.columns
    assert any("Sem registros sintéticos para esta tabela" in item.value for item in app.info)
    empty = SyntheticDataset((), (), source="PostgreSQL sintético")
    monkeypatch.setattr("vrac.ui.load_selected_demo", lambda *a, **k: empty)
    app.selectbox(key="demo_department").select("SINT-VAZIO").run()
    app.button(key="demo_show").click().run()
    assert not app.exception and not app.dataframe and not app.metric
    assert any("Ausência de registros não significa zero" in item.value for item in app.info)


def test_postgres_failure_clears_previous_results_without_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.button(key="demo_show").click().run()
    assert app.dataframe

    def fail(*args: object, **kwargs: object) -> None:
        raise DemoDataError("PostgreSQL sintético indisponível.")

    monkeypatch.setenv("VRAC_DEMO_SOURCE", "postgres")
    monkeypatch.setattr("vrac.ui.load_demo_options", fail)
    app.run()
    assert not app.exception and not app.dataframe
    assert "demo_data" not in app.session_state
    assert "PostgreSQL sintético indisponível" in app.error[0].value


def test_failed_reload_removes_previously_displayed_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.button(key="demo_show").click().run()
    assert app.dataframe

    def fail(*args: object, **kwargs: object) -> None:
        raise DemoDataError("Consulta sintética indisponível.")

    monkeypatch.setattr("vrac.ui.load_selected_demo", fail)
    app.button(key="demo_show").click().run()
    assert not app.exception and not app.dataframe
    assert "demo_data" not in app.session_state
    assert "Consulta sintética indisponível" in app.error[0].value


def test_faculty_overview_calculates_only_on_explicit_action() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception and not app.metric
    app.button(key="overview_run").click().run()
    assert not app.exception
    assert app.metric[0].label == "Quantidade de professores"
    assert app.metric[0].value == "5"
    # Mesma tabela Filtro · Valor das demais telas.
    table = next(t.value for t in app.table if list(t.value.columns) == ["Filtro", "Valor"])
    filters = dict(zip(table["Filtro"], table["Valor"], strict=True))
    assert filters["Unidade"] == "matrículas funcionais distintas"
    assert filters["Quadro"] == "todos" and filters["Origem"] == "Memória"
    assert len(app.get("vega_lite_chart")) == 5
    assert any("Informações gerais dos professores" == t.label for t in app.tabs)
    assert any("Estado das Horas Reais" in f.value.columns for f in app.dataframe)
    assert "overview_history" in app.session_state


def test_faculty_overview_filters_and_department_change_clear_results() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="overview_run").click().run()
    assert app.metric
    app.multiselect(key="overview_cadres").select("PROF PRINCIPAL").run()
    assert not app.metric and "overview_result" not in app.session_state
    app.button(key="overview_run").click().run()
    assert app.metric[0].value == "1"
    app.selectbox(key="overview_department").select("SINT-B").run()
    assert not app.metric
    assert not app.multiselect(key="overview_cadres").value
    app.button(key="overview_run").click().run()
    assert not app.exception and app.metric[0].value == "1"


def test_faculty_overview_empty_department_is_not_zero() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.selectbox(key="overview_department").select("SINT-VAZIO").run()
    app.button(key="overview_run").click().run()
    assert not app.exception and not app.metric
    assert any("não significa zero" in item.value for item in app.info)


def test_faculty_overview_source_failure_shows_error_without_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise DemoDataError("Base sintética indisponível.")

    monkeypatch.setattr("vrac.ui.load_faculty_source", fail)
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception and not app.metric
    assert any("Base sintética indisponível" in item.value for item in app.error)
    assert not any(b.key == "overview_run" for b in app.button)
