"""Cálculo de composição docente sobre a fixture determinística.

Estes testes exercitam o mecanismo, não aprovam regra institucional. O caso
"aprovado" é construído em memória, com evidência explicitamente sintética, só para
provar que o portão libera quando o registro humano existir.
"""

from dataclasses import replace
from datetime import date

import pytest
from helpers import SETTINGS, request_for

from vrac.analyses.catalog import AnalysisCatalog, ApprovalStatus, load_catalog
from vrac.analyses.contracts import (
    AnalysisId,
    Availability,
    ContractError,
    EntityKind,
    MetricUnit,
    ResultStatus,
    TemporalBasis,
)
from vrac.analyses.faculty import (
    GENERAL_METRIC,
    UNCLASSIFIED_METRIC,
    compute_faculty_composition,
    faculty_result,
)
from vrac.analyses.repository import SyntheticFacultyRepository, select_repository
from vrac.analyses.rules import RuleApproval, get_candidate_rule
from vrac.settings import DataMode
from vrac.synthetic import load_demo_data


def observations(rule, *, period: str = "2026.1", department: str = "SINT-A"):
    request = request_for(rule, period=period, department=department)
    observed = SyntheticFacultyRepository(load_demo_data(SETTINGS)).fetch(request)
    return observed.observations, request


def approved_catalog() -> AnalysisCatalog:
    """Catálogo aprovado em memória; evidência sintética, nunca institucional."""
    catalog = load_catalog()
    definition = catalog.get(AnalysisId.FACULTY)
    decisions = tuple(
        replace(
            item,
            status=ApprovalStatus.APPROVED,
            reviewed_on=date(2026, 10, 29),
            evidence_reference="evidencia-sintetica-de-teste",
        )
        for item in definition.decisions
    )
    approved = replace(
        definition,
        decisions=decisions,
        validation_status=ApprovalStatus.APPROVED,
        physical_source_reference="fonte-sintetica-de-teste",
        selected_semantic_variant="faculty_people_context",
    )
    return replace(
        catalog,
        analyses=tuple(
            approved if item.id == AnalysisId.FACULTY else item for item in catalog.analyses
        ),
    )


def approved_rule(rule_id: str = "pessoas_foto"):
    return replace(
        get_candidate_rule(rule_id),
        approval=RuleApproval(
            status=ApprovalStatus.APPROVED,
            reviewed_on=date(2026, 10, 29),
            evidence_reference="evidencia-sintetica-de-teste",
            owner_role="Talita",
        ),
    )


def test_people_and_functional_registrations_are_different_numbers() -> None:
    people = get_candidate_rule("pessoas_qualquer_mes")
    rows, request = observations(people)
    assert compute_faculty_composition(rows, request, people).general == 2

    registrations = replace(
        people,
        rule_id="matriculas_qualquer_mes_para_teste",
        counting_basis=get_candidate_rule("matriculas_ultima_por_vinculo").counting_basis,
    )
    rows, request = observations(registrations)
    assert compute_faculty_composition(rows, request, registrations).general == 3


def test_presence_in_any_month_is_not_the_sum_of_monthly_counts() -> None:
    rule = get_candidate_rule("pessoas_qualquer_mes")
    rows, request = observations(rule)
    computation = compute_faculty_composition(rows, request, rule)
    # Quatro competências na fixture, duas pessoas distintas.
    assert computation.considered_observations == 4
    assert computation.general == 2


def test_snapshot_depends_on_the_chosen_date() -> None:
    rule = get_candidate_rule("pessoas_foto")
    rows, request = observations(rule)
    march = replace(request, snapshot_on=date(2026, 3, 1))
    april = replace(request, snapshot_on=date(2026, 4, 1))
    assert compute_faculty_composition(rows, march, rule).general == 2
    assert compute_faculty_composition(rows, april, rule).general == 1


def test_latest_reference_per_registration_differs_from_latest_global() -> None:
    per_entity = get_candidate_rule("matriculas_ultima_por_vinculo")
    rows, request = observations(per_entity)
    assert compute_faculty_composition(rows, request, per_entity).general == 3

    global_latest = get_candidate_rule("matriculas_ultimo_mes_global")
    rows, request = observations(global_latest)
    assert compute_faculty_composition(rows, request, global_latest).general == 1


def test_overlapping_categories_do_not_sum_to_the_total() -> None:
    rule = get_candidate_rule("pessoas_qualquer_mes")
    rows, request = observations(rule)
    computation = compute_faculty_composition(
        rows, request, rule, grouping=EntityKind.EMPLOYMENT_CATEGORY
    )
    assert computation.general == 2
    assert {group.value: group.count for group in computation.groups} == {
        "Tipo A": 1,
        "Tipo B": 2,
    }
    assert sum(group.count for group in computation.groups) > computation.general
    assert computation.overlapping == 1


def test_missing_classification_is_counted_apart_and_never_inferred() -> None:
    rule = get_candidate_rule("pessoas_qualquer_mes")
    rows, request = observations(rule)
    computation = compute_faculty_composition(rows, request, rule, grouping=EntityKind.CADRE)
    assert computation.groups == ()
    assert computation.unclassified == 2
    assert computation.general == 2


def test_computation_refuses_a_request_that_disagrees_with_the_rule() -> None:
    rule = get_candidate_rule("pessoas_qualquer_mes")
    rows, request = observations(rule)
    other = get_candidate_rule("matriculas_ultima_por_vinculo")
    with pytest.raises(ContractError):
        compute_faculty_composition(rows, request, other)
    with pytest.raises(ContractError):
        compute_faculty_composition(rows, request, rule, grouping=EntityKind.COURSE)


def test_pending_rule_produces_a_partial_result_that_names_the_pendencies() -> None:
    catalog = load_catalog()
    rule = get_candidate_rule("pessoas_qualquer_mes")
    request = request_for(rule)
    result = faculty_result(
        request, rule, catalog, select_repository(request, load_demo_data(SETTINGS))
    )
    assert result.status == ResultStatus.PARTIAL
    assert any("não aprovada" in warning for warning in result.warnings)
    assert any("aceite_funcional_docente" in warning for warning in result.warnings)
    assert result.data[0].metric == GENERAL_METRIC
    assert result.data[0].value == 2
    assert result.units == (MetricUnit.TEACHERS,)


def test_valid_result_becomes_reachable_only_with_approval_registered() -> None:
    rule = approved_rule("pessoas_foto")
    request = replace(request_for(rule), snapshot_on=date(2026, 3, 1))
    result = faculty_result(
        request,
        rule,
        approved_catalog(),
        select_repository(request, load_demo_data(SETTINGS)),
    )
    assert result.status == ResultStatus.VALID
    assert result.data[0].value == 2
    assert all(item.availability == Availability.OBSERVED for item in result.data)


def test_incomplete_period_is_never_valid() -> None:
    rule = approved_rule("pessoas_qualquer_mes")
    request = request_for(rule, period="2026.2")
    result = faculty_result(
        request,
        rule,
        approved_catalog(),
        select_repository(request, load_demo_data(SETTINGS)),
    )
    assert request.period.complete is False
    assert result.status == ResultStatus.PARTIAL


def test_absence_of_rows_is_reported_without_a_zero() -> None:
    catalog = load_catalog()
    rule = get_candidate_rule("pessoas_qualquer_mes")
    request = request_for(rule, period="2026.2")
    result = faculty_result(
        request, rule, catalog, select_repository(request, load_demo_data(SETTINGS))
    )
    assert len(result.data) == 1
    assert result.data[0].availability == Availability.NO_ROWS
    assert result.data[0].value is None
    assert any("não significa zero" in warning for warning in result.warnings)


def test_real_mode_is_blocked_without_touching_the_repository() -> None:
    catalog = load_catalog()
    rule = get_candidate_rule("pessoas_qualquer_mes")
    request = replace(request_for(rule), mode=DataMode.REAL)

    class Forbidden:
        def fetch(self, request):  # pragma: no cover - não deve ser chamado
            raise AssertionError("Modo real não pode consultar o repositório.")

    result = faculty_result(request, rule, catalog, Forbidden())
    assert result.status == ResultStatus.BLOCKED
    assert result.data == ()
    assert any("Modo real bloqueado" in warning for warning in result.warnings)


def test_grouped_result_carries_the_unclassified_metric() -> None:
    catalog = load_catalog()
    rule = get_candidate_rule("pessoas_qualquer_mes")
    request = request_for(rule)
    result = faculty_result(
        request,
        rule,
        catalog,
        select_repository(request, load_demo_data(SETTINGS)),
        grouping=EntityKind.EMPLOYMENT_CATEGORY,
    )
    metrics = {item.metric: item for item in result.data}
    assert metrics[UNCLASSIFIED_METRIC].value == 0
    assert metrics[UNCLASSIFIED_METRIC].availability == Availability.OBSERVED
    assert any("mais de uma categoria" in warning for warning in result.warnings)


def test_snapshot_rule_requires_a_date_inside_the_period() -> None:
    rule = get_candidate_rule("pessoas_foto")
    with pytest.raises(ContractError):
        replace(request_for(rule), snapshot_on=date(2026, 1, 15))
    assert rule.temporal_basis == TemporalBasis.SNAPSHOT
