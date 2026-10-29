"""Regras candidatas e porta de dados; nenhuma fixture aprova regra institucional."""

from dataclasses import replace
from datetime import date

import pytest
from helpers import SETTINGS, request_for

from vrac.analyses.catalog import ApprovalStatus, load_catalog
from vrac.analyses.contracts import (
    ContractError,
    EntityKey,
    EntityKind,
    FacultyCountingBasis,
    MetricUnit,
    TemporalBasis,
)
from vrac.analyses.repository import (
    BlockedFacultyRepository,
    FacultyObservation,
    FacultyObservationSet,
    RealAdapterBlocked,
    SyntheticFacultyRepository,
    select_repository,
)
from vrac.analyses.rules import (
    CANDIDATE_FACULTY_RULES,
    RuleApproval,
    get_candidate_rule,
    rule_blockers,
)
from vrac.settings import DataMode
from vrac.synthetic import load_demo_data


def test_every_candidate_rule_is_pending_and_names_its_pendencies() -> None:
    assert len(CANDIDATE_FACULTY_RULES) == 4
    for rule in CANDIDATE_FACULTY_RULES:
        assert not rule.approval.approved
        assert rule.approval.reviewed_on is None
        assert rule.requires_decisions
        assert rule.limitations


def test_candidates_cover_both_populations_and_both_time_references() -> None:
    populations = {rule.counting_basis for rule in CANDIDATE_FACULTY_RULES}
    assert populations == set(FacultyCountingBasis)
    units = {rule.unit for rule in CANDIDATE_FACULTY_RULES}
    assert units == {MetricUnit.TEACHERS, MetricUnit.FUNCTIONAL_REGISTRATIONS}
    bases = {rule.temporal_basis for rule in CANDIDATE_FACULTY_RULES}
    assert TemporalBasis.SNAPSHOT in bases
    assert TemporalBasis.ANY_MONTH in bases


def test_approval_requires_date_and_evidence() -> None:
    with pytest.raises(ContractError):
        RuleApproval(
            status=ApprovalStatus.APPROVED,
            reviewed_on=None,
            evidence_reference="ata",
            owner_role="Talita",
        )
    with pytest.raises(ContractError):
        RuleApproval(
            status=ApprovalStatus.APPROVED,
            reviewed_on=date(2026, 10, 29),
            evidence_reference=None,
            owner_role="Talita",
        )


def test_unsupported_temporal_basis_is_refused() -> None:
    rule = get_candidate_rule("pessoas_foto")
    with pytest.raises(ContractError):
        replace(rule, temporal_basis=TemporalBasis.PERIOD_HISTORY)
    with pytest.raises(ContractError):
        replace(rule, temporal_basis=TemporalBasis.UNDEFINED)


def test_rule_outside_the_closed_list_is_refused() -> None:
    with pytest.raises(ContractError):
        get_candidate_rule("regra_inventada")


def test_blockers_report_catalog_and_rule_pendencies() -> None:
    catalog = load_catalog()
    blockers = rule_blockers(get_candidate_rule("pessoas_foto"), catalog)
    assert "aprovacao_regra_docente" in blockers
    assert "aceite_funcional_docente" in blockers
    assert "mapeamento_fisico_docente" in blockers
    assert "selecao_variante_docente" in blockers
    assert "faculty_source" in blockers


def test_approving_only_the_rule_does_not_clear_the_catalog_pendencies() -> None:
    catalog = load_catalog()
    approved = replace(
        get_candidate_rule("pessoas_foto"),
        approval=RuleApproval(
            status=ApprovalStatus.APPROVED,
            reviewed_on=date(2026, 10, 29),
            evidence_reference="evidencia-sintetica-de-teste",
            owner_role="Talita",
        ),
    )
    blockers = rule_blockers(approved, catalog)
    assert "aprovacao_regra_docente" not in blockers
    assert "aceite_funcional_docente" in blockers
    assert "mapeamento_fisico_docente" in blockers


def test_synthetic_repository_translates_only_the_requested_scope() -> None:
    rule = get_candidate_rule("pessoas_qualquer_mes")
    dataset = load_demo_data(SETTINGS)
    observed = SyntheticFacultyRepository(dataset).fetch(request_for(rule))
    assert observed.observations
    assert {item.employment_department.identifier for item in observed.observations} == {"SINT-A"}
    assert all(item.reference_month.day == 1 for item in observed.observations)
    assert observed.origins[0].extracted_at is not None
    # A fixture não informa quadro nem situação: devem permanecer nulos, não vazios.
    assert all(item.cadre is None and item.status is None for item in observed.observations)
    assert observed.coverage_warnings


def test_synthetic_repository_refuses_real_mode() -> None:
    rule = get_candidate_rule("pessoas_qualquer_mes")
    request = replace(request_for(rule), mode=DataMode.REAL)
    with pytest.raises(RealAdapterBlocked):
        SyntheticFacultyRepository(load_demo_data(SETTINGS)).fetch(request)


def test_real_mode_selects_the_blocked_adapter_and_never_the_fixture() -> None:
    rule = get_candidate_rule("pessoas_qualquer_mes")
    request = replace(request_for(rule), mode=DataMode.REAL)
    repository = select_repository(request, load_demo_data(SETTINGS))
    assert isinstance(repository, BlockedFacultyRepository)
    with pytest.raises(RealAdapterBlocked):
        repository.fetch(request)


def test_observation_rejects_blank_attributes_and_mid_month_competence() -> None:
    person = EntityKey(EntityKind.TEACHER, "SYN-DOC-001")
    registration = EntityKey(EntityKind.FUNCTIONAL_REGISTRATION, "V01")
    department = EntityKey(EntityKind.EMPLOYMENT_DEPARTMENT, "SINT-A")
    with pytest.raises(ContractError):
        FacultyObservation(person, registration, department, date(2026, 3, 15))
    with pytest.raises(ContractError):
        FacultyObservation(person, registration, department, date(2026, 3, 1), cadre="   ")
    with pytest.raises(ContractError):
        FacultyObservation(registration, registration, department, date(2026, 3, 1))


def test_observation_set_requires_an_origin() -> None:
    with pytest.raises(ContractError):
        FacultyObservationSet(observations=(), origins=())
