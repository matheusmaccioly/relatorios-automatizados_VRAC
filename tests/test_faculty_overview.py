"""R01: fidelidade às regras documentadas do painel, sem banco, rede ou Streamlit."""

import csv
import io
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from vrac.analyses import faculty_overview_fixture as fixture
from vrac.analyses.export import detail_csv, safe_cell, summary_csv
from vrac.analyses.faculty_overview import (
    CADRE_FILTER_GAP,
    NOT_INFORMED,
    FacultySource,
    OverviewFilters,
    OverviewStatus,
    RealHoursRow,
    compute_overview,
    current_real_hours,
    semaphore_status,
)

ALL = OverviewFilters()
NOW = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "hours,cadre,expected",
    [
        (None, "PRINCIPAL", "Sem CH (em branco)"),
        (0, "PRINCIPAL", "Sem alocação (CH = 0)"),
        (10, "PROF PRINCIPAL", "Sem regra definida"),
        (10, None, "Sem regra definida"),
        (6, "PRINCIPAL", "Abaixo do necessário"),
        (7, "principal", "Dentro do esperado"),  # comparação sem diferenciar maiúsculas
        (44, "PRINCIPAL", "Dentro do esperado"),
        (45, "PRINCIPAL", "Acima do necessário"),
        (15, "COMPLEMENTAR TEMPO INTEGRAL", "Abaixo do necessário"),
        (16, "COMPLEMENTAR TEMPO INTEGRAL", "Dentro do esperado"),
        (20, "COMPLEMENTAR TEMPO INTEGRAL", "Dentro do esperado"),
        (21, "COMPLEMENTAR TEMPO INTEGRAL", "Acima do necessário"),
        (31, "COMPLEMENTAR TEMPO INTEGRAL", "Muito acima (verificar coord./múltiplas turmas)"),
        (11, "COMPLEMENTAR TEMPO PARCIAL", "Abaixo do necessário"),
        (12, "COMPLEMENTAR TEMPO PARCIAL", "Dentro do esperado"),
        (15, "COMPLEMENTAR TEMPO PARCIAL", "Dentro do esperado"),
        (16, "COMPLEMENTAR TEMPO PARCIAL", "Acima do necessário"),
        (31, "COMPLEMENTAR TEMPO PARCIAL", "Muito acima (verificar coord./múltiplas turmas)"),
    ],
)
def test_semaphore_reproduces_dashboard_rule_and_boundaries(
    hours: float | None, cadre: str | None, expected: str
) -> None:
    assert semaphore_status(hours, cadre) == expected


def test_real_hours_use_latest_semester_per_registration_without_summing_semesters() -> None:
    rows = (
        RealHoursRow(1, 20252, 30, "PRINCIPAL"),
        RealHoursRow(1, 20261, 12, "PRINCIPAL"),
        RealHoursRow(2, 20261, None, "PRINCIPAL"),
        RealHoursRow(3, 20261, 10, "PRINCIPAL"),
        RealHoursRow(3, 20261, 2, "PRINCIPAL"),  # duas linhas no semestre: soma, como o painel
        RealHoursRow(4, 20261, 0, "PRINCIPAL"),
        RealHoursRow(4, 20261, 8, "PRINCIPAL"),  # status distintos: resultado indisponível
    )
    result = current_real_hours(rows)
    assert result[1] == (12, 20261, "Dentro do esperado")
    assert result[2] == (None, 20261, "Sem CH (em branco)")
    assert result[3][0] == 12
    assert result[4] == (8, 20261, None)


def test_overview_counts_registrations_and_preserves_missing_classification() -> None:
    overview = compute_overview(fixture.load_fixture("SINT-A"), ALL)
    assert overview.status == OverviewStatus.VALID
    assert overview.total == 5  # matrículas, embora haja 4 pessoas
    assert overview.by_cadre[-1] == (NOT_INFORMED, 1)
    assert dict(overview.by_category)["PROF PRINCIPAL"] == 2
    assert CADRE_FILTER_GAP in overview.warnings
    assert any("1 pessoa(s)" in text and "não pessoas" in text for text in overview.warnings)
    assert any("sem quadro ou categoria" in text for text in overview.warnings)
    assert any("Sem regra definida" in text for text in overview.warnings)
    assert any("sem registro na fonte de Horas Reais" in text for text in overview.warnings)
    assert "5 matrículas funcionais distintas" in overview.narrative


def test_detail_keeps_zero_null_and_absent_hours_distinct() -> None:
    detail = {
        row.registration: row
        for row in compute_overview(fixture.load_fixture("SINT-A"), ALL).detail
    }
    assert (detail["880000001"].real_hours, detail["880000001"].real_hours_semester) == (
        12,
        "2026.1",
    )
    assert detail["880000002"].real_hours == 0
    assert detail["880000002"].indicator == "Sem alocação (CH = 0)"
    assert detail["880000003"].indicator == "Acima do necessário"
    assert detail["880000004"].real_hours is None
    assert detail["880000004"].indicator == "Sem CH (em branco)"
    assert detail["880000005"].real_hours is None and detail["880000005"].indicator is None


def test_duplicate_register_rows_follow_each_visual_aggregation() -> None:
    source = fixture.load_fixture("SINT-B")
    duplicated = replace(source, register=source.register * 2)
    overview = compute_overview(duplicated, ALL)
    assert overview.total == 1  # cartão e quadro: contagem distinta
    assert overview.by_cadre == (("PROF SUPLEMENTAR", 1),)
    assert overview.by_category == (("PROF SUPLEMENTAR", 2),)  # categoria: contagem de linhas


def test_filters_change_population_and_empty_results_are_not_zero() -> None:
    source = fixture.load_fixture("SINT-A")
    principal = compute_overview(source, OverviewFilters(cadres=frozenset({"PROF PRINCIPAL"})))
    assert principal.total == 1
    missing = compute_overview(source, OverviewFilters(categories=frozenset({NOT_INFORMED})))
    assert missing.total == 1
    nobody = compute_overview(source, OverviewFilters(statuses=frozenset()))
    assert nobody.status == OverviewStatus.EMPTY_FILTERS and nobody.total is None
    empty = compute_overview(fixture.load_fixture("SINT-VAZIO"), ALL)
    assert empty.status == OverviewStatus.EMPTY_SOURCE and empty.total is None
    assert "não significa zero" in empty.narrative


def test_unknown_filter_values_are_refused() -> None:
    with pytest.raises(ValueError, match="quadro"):
        compute_overview(
            fixture.load_fixture("SINT-A"), OverviewFilters(cadres=frozenset({"' OR 1=1"}))
        )
    with pytest.raises(ValueError):
        fixture.load_fixture("SINT-INEXISTENTE")


def test_rows_without_registration_are_reported_not_counted() -> None:
    source = fixture.load_fixture("SINT-B")
    blank = replace(source.register[0], registration=None, registration_int=None)
    overview = compute_overview(
        FacultySource("SINT-B", (*source.register, blank), source.real_hours, "x", "v"), ALL
    )
    assert overview.total == 1
    assert any("sem matrícula" in text for text in overview.warnings)


def _csv(data: bytes) -> list[list[str]]:
    assert data.startswith(b"\xef\xbb\xbf")
    return list(csv.reader(io.StringIO(data.decode("utf-8-sig")), delimiter=";"))


def test_exports_identify_demo_filters_warnings_and_blocked_qp() -> None:
    overview = compute_overview(fixture.load_fixture("SINT-A"), ALL)
    summary = _csv(summary_csv(overview, NOW))
    flat = [";".join(row) for row in summary]
    assert any("DEMONSTRAÇÃO" in line for line in flat)
    assert ["Resultado", "Total", "5"] in summary
    assert ["Filtro", "Quadro", "todos"] in summary
    assert any(row[0] == "Aviso" for row in summary)
    assert any(
        row[:2] == ["Geral e QP", "QP, demais e participação"] and "bloqueado" in row[2]
        for row in summary
    )
    detail = _csv(detail_csv(overview, NOW))
    header = detail.index(next(row for row in detail if row and row[0] == "Departamento"))
    rows = detail[header + 1 :]
    assert len(rows) == 5
    assert "ausente" in {cell for row in rows for cell in row}


def test_empty_export_has_no_total() -> None:
    overview = compute_overview(fixture.load_fixture("SINT-VAZIO"), ALL)
    summary = _csv(summary_csv(overview, NOW))
    assert not any(row[:2] == ["Resultado", "Total"] for row in summary)


@pytest.mark.parametrize("text", ["=1+1", "+cmd", "-2+3", "@SUM(A1)", "\tx"])
def test_export_neutralizes_spreadsheet_formulas(text: str) -> None:
    assert safe_cell(text).startswith("'")
    assert safe_cell(-2) == "-2" and safe_cell(1.5) == "1,5" and safe_cell(None) == "ausente"
