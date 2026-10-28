"""Contratos lógicos e proveniência: nenhum cálculo institucional ou banco."""

import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from vrac.analyses.contracts import (
    AcademicPeriod,
    AnalysisId,
    AnalysisRequest,
    AnalysisResult,
    Availability,
    ContractError,
    EnrollmentBasis,
    EntityKey,
    EntityKind,
    MetricDatum,
    MetricKind,
    MetricUnit,
    ResultStatus,
    SourceReference,
    TemporalBasis,
)
from vrac.analyses.synthetic_cases import synthetic_contract_cases
from vrac.settings import DataMode


def faculty_request() -> AnalysisRequest:
    return AnalysisRequest(
        AnalysisId.FACULTY,
        AcademicPeriod("SYN-SEM", date(2026, 1, 10), date(2026, 6, 20), True),
        (EntityKey(EntityKind.EMPLOYMENT_DEPARTMENT, "SYN-DEP"),),
        temporal_basis=TemporalBasis.ANY_MONTH,
    )


def faculty_result() -> AnalysisResult:
    return AnalysisResult(
        faculty_request(),
        "12345678-1234-1234-1234-123456789abc",
        datetime(2026, 7, 3, tzinfo=UTC),
        ResultStatus.VALID,
        (MetricDatum("total", MetricUnit.TEACHERS, 2),),
        (MetricUnit.TEACHERS,),
        (
            SourceReference(
                "synthetic.faculty",
                "fixture-v1",
                datetime(2026, 7, 2, tzinfo=UTC),
                datetime(2026, 7, 1, tzinfo=UTC),
            ),
        ),
        "fixture-catalog-v1",
        "fixture-rule-v1",
        None,
        (),
    )


def test_entity_roles_are_not_interchangeable_even_when_identifiers_match() -> None:
    keys = {
        EntityKey(kind, "SYN-001")
        for kind in (
            EntityKind.EMPLOYMENT_DEPARTMENT,
            EntityKind.TEACHING_DEPARTMENT,
            EntityKind.COURSE,
            EntityKind.PROGRAM,
        )
    }
    assert len(keys) == 4


@pytest.mark.parametrize("snapshot", [None, date(2025, 12, 1)])
def test_snapshot_requires_an_explicit_date_inside_the_period(snapshot: date | None) -> None:
    with pytest.raises(ContractError):
        replace(faculty_request(), temporal_basis=TemporalBasis.SNAPSHOT, snapshot_on=snapshot)


def test_any_month_and_snapshot_remain_distinct_requests() -> None:
    request = faculty_request()
    snapshot = replace(request, temporal_basis=TemporalBasis.SNAPSHOT, snapshot_on=date(2026, 3, 1))
    assert snapshot != request
    with pytest.raises(ContractError):
        replace(request, filters=request.filters * 2)


@pytest.mark.parametrize(
    "availability",
    [Availability.NULL, Availability.NO_ROWS, Availability.UNDEFINED, Availability.ERROR],
)
def test_missing_null_error_and_undefined_never_become_zero(availability: Availability) -> None:
    datum = MetricDatum("total", MetricUnit.TEACHERS, None, availability)
    assert datum.value is None
    with pytest.raises(ContractError):
        replace(datum, value=0)


@pytest.mark.parametrize("value", [True, -1, 1.0, None])
def test_count_totals_require_nonnegative_integers(value: object) -> None:
    with pytest.raises(ContractError):
        MetricDatum("total", MetricUnit.TEACHERS, value)


def test_zero_and_negative_absolute_change_preserve_numeric_meaning() -> None:
    assert MetricDatum("total", MetricUnit.REGISTRATIONS, 0).value == 0
    delta = MetricDatum("delta", MetricUnit.REGISTRATIONS, -3, kind=MetricKind.ABSOLUTE_CHANGE)
    assert delta.value == -3


def test_counts_of_records_students_and_teachers_are_not_interchangeable() -> None:
    result = faculty_result()
    with pytest.raises(ContractError):
        replace(
            result, data=(MetricDatum("total", MetricUnit.RECORDS, 2),), units=(MetricUnit.RECORDS,)
        )
    enrollments = replace(
        result.request,
        analysis_id=AnalysisId.ENROLLMENTS,
        filters=(EntityKey(EntityKind.COURSE, "SYN-COURSE"),),
        enrollment_basis=EnrollmentBasis.REGISTRATIONS,
    )
    with pytest.raises(ContractError):
        replace(
            result,
            request=enrollments,
            data=(MetricDatum("total", MetricUnit.STUDENTS, 2),),
            units=(MetricUnit.STUDENTS,),
        )
    assert (
        replace(
            result,
            request=enrollments,
            data=(MetricDatum("total", MetricUnit.REGISTRATIONS, 3),),
            units=(MetricUnit.REGISTRATIONS,),
        )
        .data[0]
        .value
        == 3
    )


def test_duplicate_results_or_ambiguous_source_dates_are_refused() -> None:
    result = faculty_result()
    with pytest.raises(ContractError):
        replace(result, data=result.data * 2)
    with pytest.raises(ContractError):
        replace(result, origins=result.origins * 2)


@pytest.mark.parametrize("value", [3.14, Decimal("NaN"), Decimal("Infinity")])
def test_hours_require_explicit_finite_decimal(value: object) -> None:
    with pytest.raises(ContractError):
        MetricDatum("horas_reais", MetricUnit.WEEKLY_HOURS, value)


def test_partial_period_missing_data_and_undefined_grain_cannot_look_valid() -> None:
    result = faculty_result()
    with pytest.raises(ContractError):
        replace(
            result,
            request=replace(result.request, period=replace(result.request.period, complete=False)),
        )
    with pytest.raises(ContractError):
        replace(result, request=replace(result.request, temporal_basis=TemporalBasis.UNDEFINED))
    with pytest.raises(ContractError):
        replace(
            result, data=(MetricDatum("total", MetricUnit.TEACHERS, None, Availability.NO_ROWS),)
        )
    partial = replace(
        result, status=ResultStatus.PARTIAL, warnings=("Cobertura sintética incompleta.",)
    )
    assert partial.status == ResultStatus.PARTIAL
    with pytest.raises(ContractError):
        replace(partial, warnings=())


def test_real_results_cannot_bypass_the_phase_two_adapter_block() -> None:
    result = faculty_result()
    with pytest.raises(ContractError):
        replace(result, request=replace(result.request, mode=DataMode.REAL))
    blocked = replace(
        result,
        request=replace(result.request, mode=DataMode.REAL),
        status=ResultStatus.BLOCKED,
        data=(),
        warnings=("Fonte não validada.",),
    )
    assert not blocked.data
    with pytest.raises(ContractError):
        replace(blocked, data=result.data)


def test_partial_result_can_preserve_missing_data_without_zero_or_false_validity() -> None:
    result = faculty_result()
    partial = replace(
        result,
        status=ResultStatus.PARTIAL,
        request=replace(result.request, period=replace(result.request.period, complete=False)),
        data=(MetricDatum("total", MetricUnit.TEACHERS, None, Availability.NULL),),
        warnings=("Período incompleto e informação nula na fixture.",),
    )
    assert partial.data[0].value is None
    assert partial.status == ResultStatus.PARTIAL


def test_empty_data_cannot_be_labeled_a_valid_calculated_result() -> None:
    with pytest.raises(ContractError):
        replace(faculty_result(), data=())


def test_report_preserves_effective_filters_origin_dates_and_synthetic_label() -> None:
    result = faculty_result()
    second = SourceReference(
        "synthetic.second",
        "fixture-v2",
        datetime(2026, 7, 3, tzinfo=UTC),
        datetime(2026, 6, 20, tzinfo=UTC),
    )
    result = replace(result, origins=(*result.origins, second))
    payload = result.to_dict()
    assert payload["effective_filters"][0]["kind"] == "departamento_vinculo"
    assert payload["synthetic"] is True
    assert payload["origins"][0]["extracted_at"] != payload["origins"][0]["updated_at"]
    assert payload["origins"][0]["updated_at"] != payload["origins"][1]["updated_at"]
    serialized = json.dumps(payload)
    assert not any(word in serialized for word in ("password", "connection_string", "credentials"))
    with pytest.raises(ContractError):
        replace(second, extracted_at=datetime(2026, 7, 1))


def test_synthetic_cases_are_deterministic_explicit_and_not_functionally_approved() -> None:
    cases = synthetic_contract_cases()
    assert cases == synthetic_contract_cases()
    assert {case.identifier for case in cases} == {
        "duplicate_records",
        "null_value",
        "observed_zero",
        "no_rows",
        "partial_period",
        "zero_denominator",
        "distinct_source_dates",
    }
    assert all(case.synthetic and case.reference.synthetic for case in cases)
    assert all(case.reference.validation_status.value == "pending" for case in cases)
    duplicate = next(case for case in cases if case.identifier == "duplicate_records")
    assert len(duplicate.observations) == 3
    assert duplicate.reference.expected[0].value == 2
    zero_base = next(case for case in cases if case.identifier == "zero_denominator")
    assert zero_base.observations[0].value == 0
    assert zero_base.reference.expected[0].availability == Availability.UNDEFINED
    assert zero_base.reference.expected[0].value is None
