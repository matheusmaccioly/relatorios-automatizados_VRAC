"""Catálogo fechado: campos, propostas e bloqueios sem fonte aprovada."""

from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from vrac.analyses.catalog import (
    ApprovalStatus,
    CatalogError,
    DecisionArea,
    SyntheticStatus,
    blocked_result,
    load_catalog,
    pending_decisions,
)
from vrac.analyses.contracts import AnalysisId, ResultStatus
from vrac.analyses.synthetic_cases import synthetic_contract_cases
from vrac.settings import DataMode

CATALOG = Path(__file__).resolve().parents[1] / "config" / "analyses.yaml"


def test_catalog_has_only_the_three_priorities_and_explicit_pending_approvals() -> None:
    catalog = load_catalog()
    assert [item.id for item in catalog.analyses] == list(AnalysisId)
    for definition in catalog.analyses:
        assert definition.validation_status == ApprovalStatus.PENDING
        assert definition.synthetic_status == SyntheticStatus.IMPLEMENTED_OFFLINE_VERIFIED
        assert definition.synthetic_mapping_reference.startswith(
            "docs/operations/SYNTHETIC_SOURCE_MAP.md#"
        )
        assert definition.physical_source_reference is None
        assert {item.area for item in definition.decisions} == set(DecisionArea)
        assert len(pending_decisions(definition)) == 5
        assert (
            definition.comparison_policy and definition.logical_keys and definition.logical_sources
        )
        assert all(
            item.reviewed_on is None and item.evidence_reference is None
            for item in definition.decisions
        )


@pytest.mark.parametrize("mode", list(DataMode))
def test_blocked_result_never_queries_or_falls_back_to_synthetic_numbers(mode: DataMode) -> None:
    catalog = load_catalog()
    for case in synthetic_contract_cases():
        result = blocked_result(replace(case.reference.request, mode=mode), catalog)
        assert result.status == ResultStatus.BLOCKED and result.data == ()
        assert result.query_version is None
        assert result.warnings
        assert all(
            origin.extracted_at is None and origin.updated_at is None for origin in result.origins
        )
        assert result.request == replace(case.reference.request, mode=mode)


@pytest.mark.parametrize(
    "corruption",
    [
        "unknown_analysis",
        "missing_decision",
        "approval_without_evidence",
        "unknown_field",
        "wrong_priority",
        "duplicate_analysis",
        "false_synthetic_verification",
    ],
)
def test_invalid_catalog_cannot_silently_expand_scope_or_approve_rules(
    corruption: str, tmp_path: Path
) -> None:
    document = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    first = document["analyses"][0]
    if corruption == "unknown_analysis":
        first["id"] = "financeiro"
    elif corruption == "missing_decision":
        first["decisions"].pop()
    elif corruption == "approval_without_evidence":
        first["validation_status"] = "approved"
    elif corruption == "unknown_field":
        first["connection_string"] = "private-marker"
    elif corruption == "wrong_priority":
        document["analyses"][0]["priority"], document["analyses"][1]["priority"] = 2, 1
    elif corruption == "false_synthetic_verification":
        first["synthetic_status"] = "institutionally_approved"
    else:
        document["analyses"][1] = dict(first)
    path = tmp_path / "catalog.yaml"
    path.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    with pytest.raises(CatalogError) as error:
        load_catalog(path)
    assert "private-marker" not in str(error.value)


@pytest.mark.parametrize(
    "payload",
    [
        "catalog_version: one\ncatalog_version: private-marker\nanalyses: []",
        "!!python/object/apply:builtins.str [private-marker]",
        "catalog_version: [private-marker]\nanalyses: []",
    ],
)
def test_yaml_duplicates_tags_and_bad_types_are_refused_without_echo(
    payload: str, tmp_path: Path
) -> None:
    path = tmp_path / "catalog.yaml"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(CatalogError) as error:
        load_catalog(path)
    assert "private-marker" not in str(error.value)


def test_unknown_analysis_identifier_is_not_accepted_as_a_free_query() -> None:
    with pytest.raises(CatalogError):
        load_catalog().get("arbitrary_sql")
