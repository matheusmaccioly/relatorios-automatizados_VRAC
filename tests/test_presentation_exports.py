"""Apresentação e exportação: nenhum valor ausente vira zero e o recorte acompanha."""

from dataclasses import replace
from datetime import date

import pytest
from helpers import SETTINGS, request_for

from vrac.analyses.catalog import load_catalog
from vrac.analyses.contracts import Availability, EntityKind, ResultStatus
from vrac.analyses.faculty import faculty_result
from vrac.analyses.repository import select_repository
from vrac.analyses.rules import get_candidate_rule
from vrac.branding import load_branding
from vrac.exports import (
    CSV_DELIMITER,
    CSV_ENCODING,
    ExportBlocked,
    export_filename,
    result_csv,
    result_json,
)
from vrac.presentation import (
    ViewState,
    build_view,
    composition_chart,
    filters_table,
    metadata_table,
    result_table,
    view_state,
)
from vrac.synthetic import load_demo_data


def build_result(*, period: str = "2026.1", grouping=EntityKind.EMPLOYMENT_CATEGORY):
    rule = get_candidate_rule("pessoas_qualquer_mes")
    request = request_for(rule, period=period)
    result = faculty_result(
        request,
        rule,
        load_catalog(),
        select_repository(request, load_demo_data(SETTINGS)),
        grouping=grouping,
    )
    return result, rule


def test_absent_value_shows_its_situation_instead_of_zero() -> None:
    result, _ = build_result(period="2026.2", grouping=None)
    table = result_table(result)
    assert len(table) == 1
    assert table.iloc[0]["Valor"] is None
    assert table.iloc[0]["Situação do dado"] == "Sem registros"


def test_view_state_separates_empty_from_partial_and_blocked() -> None:
    empty, _ = build_result(period="2026.2", grouping=None)
    assert view_state(empty) == ViewState.EMPTY
    assert "não significa zero" in build_view(empty).headline

    partial, _ = build_result()
    assert partial.status == ResultStatus.PARTIAL
    assert view_state(partial) == ViewState.PARTIAL

    blocked = replace(empty, status=ResultStatus.BLOCKED, data=())
    assert view_state(blocked) == ViewState.BLOCKED


def test_filters_table_records_the_effective_scope_and_the_rule() -> None:
    result, rule = build_result()
    rows = dict(zip(*filters_table(result.request, rule).to_dict("list").values(), strict=True))
    assert rows["departamento vinculo"] == "SINT-A"
    assert rows["período"] == "2026.1"
    assert rows["período completo"] == "sim"
    assert rows["modo"] == "sintético"
    assert rows["data da foto"] == "não se aplica"
    assert rows["regra aplicada"] == rule.label


def test_metadata_keeps_extraction_and_source_update_as_separate_dates() -> None:
    result, _ = build_result()
    rows = dict(zip(*metadata_table(result).to_dict("list").values(), strict=True))
    origin = next(value for key, value in rows.items() if key.startswith("origem"))
    assert "extração 20" in origin
    assert "atualização da origem desconhecida" in origin
    assert rows["versão da consulta"] == "não há consulta revisada nesta fase"


def test_chart_plots_only_observed_categories() -> None:
    result, _ = build_result()
    figure = composition_chart(result, load_branding().tokens)
    assert figure is not None
    axes = figure.axes[0]
    assert [patch.get_height() for patch in axes.patches] == [1.0, 2.0]
    # O total e a métrica sem classificação não entram no gráfico de categorias.
    assert len(axes.patches) == 2


def test_chart_is_absent_when_there_is_nothing_observed_to_plot() -> None:
    result, _ = build_result(period="2026.2", grouping=None)
    assert composition_chart(result, load_branding().tokens) is None


def test_csv_repeats_scope_versions_and_warnings_on_every_row() -> None:
    result, rule = build_result()
    content = result_csv(result, rule).decode(CSV_ENCODING)
    header, *rows = [line for line in content.splitlines() if line]
    assert CSV_DELIMITER in header
    assert "Avisos" in header
    assert "Filtro · período" in header
    assert len(rows) == len(result.data)
    for row in rows:
        assert "2026.1" in row
        assert result.catalog_version in row
        assert "não aprovada" in row


def test_csv_neutralizes_text_that_excel_would_read_as_a_formula() -> None:
    result, rule = build_result()
    injected = replace(
        result,
        warnings=('=HYPERLINK("http://exemplo")', *result.warnings),
    )
    content = result_csv(injected, rule).decode(CSV_ENCODING)
    assert "'=HYPERLINK" in content
    assert ";=HYPERLINK" not in content


def test_json_carries_the_rule_and_the_synthetic_marker() -> None:
    import json

    result, rule = build_result()
    payload = json.loads(result_json(result, rule).decode("utf-8"))
    assert payload["synthetic"] is True
    assert payload["rule"]["approval_status"] == "pending"
    assert payload["rule"]["rule_id"] == rule.rule_id
    assert payload["availability_legend"][Availability.NO_ROWS.value] == "no_rows"
    assert payload["effective_filters"][0]["identifier"] == "SINT-A"


def test_blocked_and_real_results_do_not_export() -> None:
    result, rule = build_result()
    blocked = replace(result, status=ResultStatus.BLOCKED, data=())
    with pytest.raises(ExportBlocked):
        result_csv(blocked, rule)
    with pytest.raises(ExportBlocked):
        result_json(blocked, rule)


def test_export_filename_marks_the_mode_and_hides_physical_names() -> None:
    result, _ = build_result()
    name = export_filename(result, "csv")
    assert name.startswith("composicao_docente_2026-1_sintetico_")
    assert name.endswith(".csv")


def test_period_dates_are_explicit_and_not_a_civil_calendar() -> None:
    result, _ = build_result()
    assert result.request.period.starts_on == date(2026, 3, 1)
    assert result.request.period.ends_on == date(2026, 7, 31)
