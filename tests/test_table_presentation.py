"""Tabelas visuais e gráficos novos mudam a leitura, nunca os valores nem os arquivos."""

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from vrac.academic_ui import _percent
from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate, chart_unit
from vrac.analyses.academic_data import ALL_DEPARTMENTS
from vrac.analyses.academic_export import table_csv
from vrac.analyses.academic_fixture import load_fixture
from vrac.analyses.export import detail_csv
from vrac.analyses.faculty_overview import OverviewFilters, compute_overview, semaphore_status
from vrac.analyses.faculty_overview_fixture import load_fixture as load_faculty
from vrac.branding import load_branding
from vrac.charts import academic_chart, render_png
from vrac.indicators import (
    ABSENT,
    INDICATORS,
    change_label,
    indicator_distribution,
    indicator_label,
    indicator_rank,
)
from vrac.ui import RECORDS_TITLE, VIEWS
from vrac.ui_kit import TONE_TOKENS, _indicator_styles
from vrac.web_charts import chart_records, interactive_chart

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 5, 12, tzinfo=UTC)
FILTERS = AnalysisFilters(
    "2024.1", "2026.2", "2026.2", group_a_cadres=("PROF PRINCIPAL", "PRINCIPAL")
)
SYMBOLS = {symbol for symbol, _ in INDICATORS.values()} - {"?", "–"}


def table(result, key):
    return next(item for item in result.tables if item.key == key)


def calculated(kind, department="SINT-A", filters=FILTERS):
    return calculate(kind, load_fixture(department), filters)


@pytest.mark.parametrize("hours", [None, 0, 1, 7, 12, 14, 16, 18, 21, 31, 44, 45])
@pytest.mark.parametrize(
    "cadre",
    ["PRINCIPAL", "COMPLEMENTAR TEMPO INTEGRAL", "COMPLEMENTAR TEMPO PARCIAL", "OUTRO", None],
)
def test_every_outcome_of_the_rule_has_a_symbol(hours, cadre) -> None:
    assert semaphore_status(hours, cadre) in INDICATORS


def test_symbols_are_unique_and_tones_use_only_declared_tokens() -> None:
    symbols = [symbol for symbol, _ in INDICATORS.values()]
    assert len(symbols) == len(set(symbols))
    colors = load_branding().tokens["colors"]
    assert {colors[token] for token in TONE_TOKENS.values()} <= set(colors.values())
    # O resultado não avalia produtividade: nenhum estado recebe a cor de erro.
    assert not any(colors["red"] in style for style in _indicator_styles().values())
    assert indicator_label("Dentro do esperado") not in _indicator_styles()


def test_labels_keep_the_original_text_and_leave_unknown_values_alone() -> None:
    assert indicator_label("Abaixo do necessário") == "▼ Abaixo do necessário"
    assert indicator_label("Acima do necessário") == "▲ Acima do necessário"
    assert indicator_label(ABSENT) == ABSENT
    assert indicator_label("Horas Reais informadas") == "Horas Reais informadas"


def test_distribution_counts_every_row_in_reading_order_and_keeps_missing_visible() -> None:
    values = ["Acima do necessário", None, "Abaixo do necessário", "Acima do necessário", None]
    assert indicator_distribution(values) == (
        ("Abaixo do necessário", 1),
        ("Acima do necessário", 2),
        (ABSENT, 2),
    )
    assert indicator_rank(ABSENT) > indicator_rank("Resultados distintos")


def test_change_direction_never_marks_a_missing_variation() -> None:
    assert change_label(12.5, "12,5") == "▲ 12,5"
    assert change_label(-3, "-3") == "▼ -3"
    assert change_label(0, "0") == "● 0"
    assert change_label(None, "ausente") == "ausente"


def test_percent_is_rounded_only_for_display() -> None:
    assert _percent(33.3333) == "33,3"
    assert _percent(0.0) == "0,0"
    assert _percent(None) == "ausente"
    assert _percent(float("nan")) == "ausente"


def test_exported_files_carry_the_rule_text_without_symbols() -> None:
    overview = compute_overview(load_faculty("SINT-A"), OverviewFilters())
    workload = calculated(AnalysisKind.WORKLOAD)
    files = [
        detail_csv(overview, NOW).decode("utf-8-sig"),
        table_csv(workload, table(workload, "workload"), NOW).decode("utf-8-sig"),
        table_csv(workload, table(workload, "indicators"), NOW).decode("utf-8-sig"),
    ]
    assert all("Sem alocação (CH = 0)" in text for text in files)
    assert not any(symbol in text for text in files for symbol in SYMBOLS)


def test_workload_indicator_chart_reads_the_calculated_table_in_reading_order() -> None:
    result = calculated(AnalysisKind.WORKLOAD)
    spec = next(chart for chart in result.charts if chart.table == "indicators")
    rows = table(result, "indicators").rows
    assert sum(count for _, count in rows) == len(table(result, "workload").rows)
    assert [name for name, _ in rows] == sorted((name for name, _ in rows), key=indicator_rank)
    serialized = interactive_chart(result, spec, load_branding()).to_dict()
    expression = serialized["layer"][0]["encoding"]["y"]["axis"]["labelExpr"]
    assert "▼ Abaixo do necessário" in expression and "datum.label" in expression
    assert chart_unit(result, spec) == "professores"
    assert render_png(lambda: academic_chart(result, spec, load_branding())).startswith(b"\x89PNG")


def test_participation_chart_uses_percent_and_needs_more_than_one_department() -> None:
    several = calculated(AnalysisKind.QP, ALL_DEPARTMENTS)
    spec = next(chart for chart in several.charts if "Participação (%)" in chart.series)
    assert chart_unit(several, spec) == "%"
    grouped = next(chart for chart in several.charts if chart.kind == "grouped_bar")
    assert chart_unit(several, grouped) == "professores (matrículas funcionais distintas)"
    one = calculated(AnalysisKind.QP)
    assert len(table(one, "departments").rows) == 1
    assert not any("Participação (%)" in chart.series for chart in one.charts)


def test_bar_with_missing_value_stays_on_the_axis_labelled_as_missing() -> None:
    # Departamento sem professores do grupo B: participação ausente, não zero.
    nested = replace(
        FILTERS, group_b_cadres=("PROF PRINCIPAL", "PRINCIPAL", "PROF HORISTA"), group_b_name="B"
    )
    result = calculated(AnalysisKind.QP, ALL_DEPARTMENTS, nested)
    spec = next(chart for chart in result.charts if "Participação (%)" in chart.series)
    records = chart_records(result, spec)
    missing = [record for record in records if record["Valor"] is None]
    assert missing and all(record["Valor exibido"] == "ausente" for record in missing)
    serialized = interactive_chart(result, spec, load_branding()).to_dict()
    assert all(layer["mark"]["invalid"] == "show" for layer in serialized["layer"])


def test_course_chart_repeats_the_detail_rows_of_the_last_period_without_summing() -> None:
    result = calculated(AnalysisKind.STUDENTS, ALL_DEPARTMENTS)
    latest = table(result, "student_courses_latest")
    detail = table(result, "student_courses")
    expected = {row[0]: row[2] for row in detail.rows if row[1] == "2026.2"}
    assert dict(latest.rows) == expected
    known = [value for _, value in latest.rows if value is not None]
    assert known == sorted(known, reverse=True)
    assert any(chart.table == latest.key for chart in result.charts)


def test_single_course_keeps_the_table_and_skips_the_one_bar_chart() -> None:
    every = calculated(AnalysisKind.STUDENTS, ALL_DEPARTMENTS)
    course = table(every, "student_courses_latest").rows[0][0]
    result = calculated(AnalysisKind.STUDENTS, ALL_DEPARTMENTS, replace(FILTERS, courses=(course,)))
    assert len(table(result, "student_courses_latest").rows) == 1
    assert not any(chart.table == "student_courses_latest" for chart in result.charts)


def test_unavailable_enrollment_stays_missing_in_the_course_table() -> None:
    source = load_fixture(ALL_DEPARTMENTS)
    source = replace(source, available=source.available - {"students"})
    latest = table(calculate(AnalysisKind.STUDENTS, source, FILTERS), "student_courses_latest")
    assert latest.rows and all(value is None for _, value in latest.rows)


def test_coming_soon_areas_are_tabs_without_data_or_analyses() -> None:
    soon = [view for view in VIEWS if "em breve" in view]
    assert soon == ["Financeira (em breve)", "Projetos patrocinados (em breve)"]
    assert 'content: "Análise financeira"' not in load_branding().styles
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    for label in soon:
        tab = next(item for item in app.tabs if item.label == label)
        assert not tab.selectbox and not tab.multiselect and not tab.metric
        assert [button.key for button in tab.button] == [f"{label.split()[0].casefold()}_home"]
    app.button(key="financeira_home").click().run()
    assert app.session_state["vrac-view"] == "Início"


def test_records_left_the_menu_and_stay_collapsed_at_the_end_of_the_page() -> None:
    assert RECORDS_TITLE not in VIEWS
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert not any(tab.label == RECORDS_TITLE for tab in app.tabs)
    block = next(item for item in app.expander if item.label == RECORDS_TITLE)
    assert not block.proto.expanded
    assert block.button(key="demo_show") is not None


def r04_app() -> AppTest:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.button(key="home_open_R04").click().run()
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    return app


def test_charted_tables_stay_collapsed_inside_their_chart_cards() -> None:
    app = r04_app()
    result = app.session_state["suite_results"][0]
    cards = [item for item in app.expander if item.label == "Ver tabela do gráfico"]
    assert len(cards) == len(result.charts)
    assert not any(item.proto.expanded for item in cards)
    labels = [item.label for item in app.expander]
    charted = {chart.table for chart in result.charts}
    for item in result.tables:
        assert (item.title in labels) == (item.key not in charted)
    assert "CH Real dos Professores em Disciplinas" in labels


def test_every_table_keeps_a_csv_with_its_previous_key_and_shows_the_symbols() -> None:
    app = r04_app()
    result = app.session_state["suite_results"][0]
    keys = {button.key for button in app.get("download_button")}
    assert {f"suite_R04_{item.key}_csv" for item in result.tables} <= keys
    element = next(
        item
        for item in app.dataframe
        if "Indicador de CH" in item.value and "Nome fictício" in item.value
    )
    shown = set(element.value["Indicador de CH"])
    assert shown <= {indicator_label(name) for name in INDICATORS}
    # A leitura começa pelo que interessa; a ordem do cálculo e do CSV não muda.
    assert list(element.proto.column_order)[:3] == [
        "Nome fictício",
        "Indicador de CH",
        "Horas Reais (Semestre Atual)",
    ]
    assert list(element.value.columns)[:2] == ["Matrícula fictícia", "Nome fictício"]


def test_table_feeding_two_charts_gets_distinct_download_keys() -> None:
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.button(key="home_open_R03").click().run()
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    keys = [button.key for button in app.get("download_button")]
    assert len(keys) == len(set(keys))
    assert "suite_R03_monthly_history_csv" in keys and "suite_R03_history_csv" in keys
