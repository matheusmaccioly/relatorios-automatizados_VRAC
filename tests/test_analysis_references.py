"""Critérios de comparação e equivalência usando apenas fixtures identificadas."""

from dataclasses import replace
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import pytest
from test_analysis_contracts import faculty_result

from vrac.analyses.catalog import ApprovalStatus
from vrac.analyses.contracts import (
    AcademicPeriod,
    ContractError,
    EntityKey,
    EntityKind,
    MetricDatum,
    MetricUnit,
)
from vrac.analyses.courses import CourseEquivalence, resolve_course_series
from vrac.analyses.references import (
    ComparisonStatus,
    HoursRoundingRule,
    ReferenceCase,
    compare_reference_case,
    compare_reference_values,
)
from vrac.settings import DataMode


def test_integer_counts_have_no_adjustable_tolerance() -> None:
    expected = MetricDatum("total", MetricUnit.TEACHERS, 10)
    assert (
        compare_reference_values(expected, replace(expected, value=10)).status
        == ComparisonStatus.MATCH
    )
    assert (
        compare_reference_values(expected, replace(expected, value=11)).status
        == ComparisonStatus.MISMATCH
    )


def rounding_rule() -> HoursRoundingRule:
    return HoursRoundingRule(
        2, ROUND_HALF_UP, date(2026, 1, 1), "Papel fictício", "synthetic:rounding-only", True
    )


def test_hours_require_explicit_rounding_and_matching_units_and_mode() -> None:
    expected = MetricDatum("horas_reais", MetricUnit.WEEKLY_HOURS, Decimal("1.234"))
    actual = replace(expected, value=Decimal("1.231"))
    assert compare_reference_values(expected, actual).status == ComparisonStatus.BLOCKED
    assert (
        compare_reference_values(expected, actual, hours_rounding=rounding_rule()).status
        == ComparisonStatus.MATCH
    )
    assert (
        compare_reference_values(
            expected, replace(actual, value=Decimal("1.245")), hours_rounding=rounding_rule()
        ).status
        == ComparisonStatus.MISMATCH
    )
    assert (
        compare_reference_values(
            expected, actual, mode=DataMode.REAL, hours_rounding=rounding_rule()
        ).status
        == ComparisonStatus.BLOCKED
    )
    assert (
        compare_reference_values(
            expected,
            replace(actual, unit=MetricUnit.SEMESTER_HOURS),
            hours_rounding=rounding_rule(),
        ).status
        == ComparisonStatus.BLOCKED
    )
    with pytest.raises(ContractError):
        replace(rounding_rule(), evidence_reference="")


def test_reference_comparison_requires_same_scope_rule_and_source_reference() -> None:
    result = faculty_result()
    reference = ReferenceCase(
        "synthetic-reference",
        result.request,
        result.rule_version,
        result.origins,
        result.data,
        ApprovalStatus.PENDING,
        True,
    )
    assert compare_reference_case(reference, result).status == ComparisonStatus.MATCH
    assert (
        compare_reference_case(reference, replace(result, rule_version="different-rule")).status
        == ComparisonStatus.BLOCKED
    )
    different_scope = replace(
        result.request, filters=(EntityKey(EntityKind.EMPLOYMENT_DEPARTMENT, "SYN-OTHER"),)
    )
    assert (
        compare_reference_case(reference, replace(result, request=different_scope)).status
        == ComparisonStatus.BLOCKED
    )
    origin = result.origins[0]
    assert (
        compare_reference_case(
            reference,
            replace(
                result, origins=(replace(origin, updated_at=origin.updated_at + timedelta(days=1)),)
            ),
        ).status
        == ComparisonStatus.BLOCKED
    )
    assert (
        compare_reference_case(
            reference,
            replace(
                result,
                origins=(replace(origin, extracted_at=origin.extracted_at + timedelta(days=1)),),
            ),
        ).status
        == ComparisonStatus.MATCH
    )


def test_synthetic_reference_never_becomes_human_functional_approval() -> None:
    result = faculty_result()
    with pytest.raises(ContractError):
        ReferenceCase(
            "synthetic-reference",
            result.request,
            result.rule_version,
            result.origins,
            result.data,
            ApprovalStatus.APPROVED,
            True,
            "Papel fictício",
            date(2026, 1, 1),
            "synthetic:fake",
        )


def test_unknown_origin_update_and_rejected_reference_do_not_auto_reconcile() -> None:
    result = faculty_result()
    reference = ReferenceCase(
        "synthetic-reference",
        result.request,
        result.rule_version,
        result.origins,
        result.data,
        ApprovalStatus.PENDING,
        True,
    )
    assert (
        compare_reference_case(
            replace(reference, validation_status=ApprovalStatus.REJECTED), result
        ).status
        == ComparisonStatus.BLOCKED
    )
    unknown = replace(result.origins[0], updated_at=None)
    assert (
        compare_reference_case(
            replace(reference, origins=(unknown,)), replace(result, origins=(unknown,))
        ).status
        == ComparisonStatus.BLOCKED
    )


def equivalence() -> CourseEquivalence:
    return CourseEquivalence(
        EntityKey(EntityKind.COURSE, "SYN-OLD"),
        EntityKey(EntityKind.COURSE, "SYN-NEW"),
        date(2026, 1, 1),
        date(2026, 12, 31),
        "synthetic:course-reference",
        "fixture-v1",
        ApprovalStatus.APPROVED,
        True,
        "Papel fictício",
        date(2026, 1, 1),
        "synthetic:approval-fixture",
    )


def test_courses_without_approved_equivalence_keep_separate_series() -> None:
    item = equivalence()
    period = AcademicPeriod("SYN-SEM", date(2026, 2, 1), date(2026, 6, 30), True)
    first = resolve_course_series(item.source_course, period)
    second = resolve_course_series(item.target_course, period)
    assert first.series_course != second.series_course
    pending = replace(item, approval_status=ApprovalStatus.PENDING)
    assert resolve_course_series(item.source_course, period, (pending,)).combined is False
    assert (
        resolve_course_series(item.source_course, period, (item,), mode=DataMode.REAL).combined
        is False
    )
    with pytest.raises(ContractError):
        resolve_course_series(EntityKey(EntityKind.PROGRAM, "SYN-OLD"), period)


def test_equivalence_requires_full_validity_and_rejects_conflicting_overlap_or_chains() -> None:
    item = equivalence()
    period = AcademicPeriod("SYN-SEM", date(2026, 2, 1), date(2026, 6, 30), True)
    assert (
        resolve_course_series(item.source_course, period, (item,)).series_course
        == item.target_course
    )
    partial = replace(item, valid_from=date(2026, 4, 1))
    assert not resolve_course_series(item.source_course, period, (partial,)).combined
    assert not resolve_course_series(item.source_course, period, (item, partial)).combined
    chain = replace(
        item,
        source_course=item.target_course,
        target_course=EntityKey(EntityKind.COURSE, "SYN-THIRD"),
    )
    assert not resolve_course_series(item.source_course, period, (item, chain)).combined
    with pytest.raises(ContractError):
        replace(item, evidence_reference=None)
