"""Distinções documentais com fixtures sintéticas; sem arquivo interno ou banco."""

from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from test_analysis_contracts import faculty_result

from vrac.analyses.catalog import ApprovalStatus, CatalogError, blocked_result, load_catalog
from vrac.analyses.contracts import (
    AnalysisId,
    ContractError,
    EnrollmentBasis,
    EntityKey,
    EntityKind,
    FacultyCountingBasis,
    MetricDatum,
    MetricUnit,
    TemporalBasis,
)
from vrac.analyses.references import (
    ComparisonStatus,
    ReferenceCase,
    compare_reference_case,
    compare_reference_values,
)

CATALOG = Path(__file__).resolve().parents[1] / "config" / "analyses.yaml"


def test_documentation_rebases_candidates_without_approving_or_selecting_them() -> None:
    catalog = load_catalog()
    assert len(catalog.documentary_evidence) == 1
    assert catalog.documentary_evidence[0].detailed_document_available
    assert [len(a.semantic_variants) for a in catalog.analyses] == [4, 4, 1]
    for definition in catalog.analyses:
        assert definition.selected_semantic_variant is None
        assert definition.physical_source_reference is None
        assert definition.validation_status == ApprovalStatus.PENDING
    faculty = catalog.get(AnalysisId.FACULTY)
    assert {v.unit for v in faculty.semantic_variants} == {
        MetricUnit.TEACHERS,
        MetricUnit.FUNCTIONAL_REGISTRATIONS,
    }
    enrollment = catalog.get(AnalysisId.ENROLLMENTS)
    assert {v.temporal_basis for v in enrollment.semantic_variants} == {
        TemporalBasis.CURRENT_REGISTER,
        TemporalBasis.PERIOD_HISTORY,
        TemporalBasis.LATEST_PER_ENTITY,
        TemporalBasis.FINAL_TRAJECTORY,
    }
    assert {v.unit for v in enrollment.semantic_variants} == {MetricUnit.ACADEMIC_REGISTRATIONS}
    assert catalog.get(AnalysisId.WORKLOAD).semantic_variants[0].unit is None
    result = blocked_result(faculty_result().request, catalog)
    assert result.data == ()
    assert not any("documento detalhado e o mapeamento" in warning for warning in result.warnings)


@pytest.mark.parametrize(
    "corruption",
    [
        "wrong_model",
        "financial_model",
        "unknown_evidence",
        "summary_only",
        "unknown_source",
        "wrong_measure_namespace",
        "duplicate_variant",
        "unknown_unit",
        "null_count_unit",
        "false_hour_unit",
        "undefined_time",
        "premature_selection",
        "unknown_selection",
    ],
)
def test_invalid_semantic_mapping_fails_closed(corruption: str, tmp_path: Path) -> None:
    doc = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    entry = doc["analyses"][0]
    variant = entry["semantic_variants"][0]
    if corruption == "wrong_model":
        variant["model"] = "B"
        variant["measure_references"] = ["B-M-033"]
    elif corruption == "financial_model":
        variant["model"] = "C"
    elif corruption == "unknown_evidence":
        variant["evidence_reference"] = "missing"
    elif corruption == "summary_only":
        doc["documentary_evidence"][0]["detailed_document_available"] = False
    elif corruption == "unknown_source":
        variant["logical_source"] = "missing"
    elif corruption == "wrong_measure_namespace":
        variant["measure_references"] = ["B-M-033"]
    elif corruption == "duplicate_variant":
        entry["semantic_variants"].append(dict(variant))
    elif corruption == "unknown_unit":
        variant["unit"] = "unknown"
    elif corruption == "null_count_unit":
        variant["unit"] = None
    elif corruption == "false_hour_unit":
        doc["analyses"][2]["semantic_variants"][0]["unit"] = False
    elif corruption == "undefined_time":
        variant["temporal_basis"] = "pendente"
    else:
        entry["selected_semantic_variant"] = (
            variant["id"] if corruption == "premature_selection" else "missing"
        )
    path = tmp_path / "catalog.yaml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


def test_person_functional_and_academic_identifiers_have_distinct_namespaces() -> None:
    assert (
        len(
            {
                EntityKey(kind, "SYN-001")
                for kind in (
                    EntityKind.TEACHER,
                    EntityKind.FUNCTIONAL_REGISTRATION,
                    EntityKind.ACADEMIC_REGISTRATION,
                )
            }
        )
        == 3
    )


def test_two_functional_registrations_are_not_reported_as_two_people() -> None:
    # A fixture declara uma pessoa com duas matrículas; não calcula um indicador real.
    people = replace(faculty_result(), data=(MetricDatum("total", MetricUnit.TEACHERS, 1),))
    functional = replace(
        people,
        request=replace(
            people.request, faculty_counting_basis=FacultyCountingBasis.FUNCTIONAL_REGISTRATIONS
        ),
        data=(MetricDatum("total", MetricUnit.FUNCTIONAL_REGISTRATIONS, 2),),
        units=(MetricUnit.FUNCTIONAL_REGISTRATIONS,),
    )
    assert (
        compare_reference_values(people.data[0], functional.data[0]).status
        == ComparisonStatus.BLOCKED
    )
    with pytest.raises(ContractError):
        replace(functional, request=people.request)


def test_academic_registration_count_cannot_be_labeled_unique_students() -> None:
    result = faculty_result()
    academic = replace(
        result,
        request=replace(
            result.request,
            analysis_id=AnalysisId.ENROLLMENTS,
            enrollment_basis=EnrollmentBasis.ACADEMIC_REGISTRATIONS,
        ),
        data=(MetricDatum("total", MetricUnit.ACADEMIC_REGISTRATIONS, 2),),
        units=(MetricUnit.ACADEMIC_REGISTRATIONS,),
    )
    with pytest.raises(ContractError):
        replace(
            academic,
            request=replace(academic.request, enrollment_basis=EnrollmentBasis.UNIQUE_STUDENTS),
        )


@pytest.mark.parametrize("change", ["temporal_basis", "semantic_variant_id"])
def test_equal_values_do_not_reconcile_different_temporal_or_population_rules(change: str) -> None:
    result = faculty_result()
    reference = ReferenceCase(
        "synthetic:baseline",
        result.request,
        result.rule_version,
        result.origins,
        result.data,
        ApprovalStatus.PENDING,
        True,
    )
    changed_request = replace(
        result.request,
        **{
            change: TemporalBasis.LATEST_PER_ENTITY
            if change == "temporal_basis"
            else "synthetic:other_population"
        },
    )
    outcome = compare_reference_case(reference, replace(result, request=changed_request))
    assert outcome.status == ComparisonStatus.BLOCKED


@pytest.mark.parametrize(
    "unit", [MetricUnit.FUNCTIONAL_REGISTRATIONS, MetricUnit.ACADEMIC_REGISTRATIONS]
)
def test_new_registration_units_preserve_exact_integer_count_contract(unit: MetricUnit) -> None:
    with pytest.raises(ContractError):
        MetricDatum("total", unit, 1.5)
    expected = MetricDatum("total", unit, 2)
    assert (
        compare_reference_values(expected, replace(expected, value=3)).status
        == ComparisonStatus.MISMATCH
    )
