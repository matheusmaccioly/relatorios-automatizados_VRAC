"""Roteiros com identidades e datas sintéticas; nenhuma regra institucional aprovada."""

import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from vrac.analyses.catalog import ApprovalStatus, CatalogError, blocked_result, load_catalog
from vrac.analyses.contracts import (
    AcademicPeriod,
    AnalysisId,
    AnalysisRequest,
    AnalysisResult,
    ContractError,
    EnrollmentBasis,
    EntityKey,
    EntityKind,
    MetricDatum,
    MetricUnit,
    ResultStatus,
    SourceReference,
    TemporalBasis,
)
from vrac.analyses.workflows import (
    WORKFLOW_DECISIONS,
    WORKFLOWS,
    MetricResult,
    WorkflowId,
    WorkflowRequest,
    WorkflowResult,
    get_workflow,
    phase3_blockers,
    plan_workflow,
)
from vrac.settings import DataMode


def request(identifier: WorkflowId = WorkflowId.STUDENTS) -> WorkflowRequest:
    definition = get_workflow(identifier)
    basis = definition.temporal_bases[0]
    point = AnalysisRequest(
        definition.analysis_id,
        AcademicPeriod("SYN-S1", date(2025, 1, 1), date(2025, 7, 15), True),
        (EntityKey(definition.scope_kinds[0], "SYN-UNIT"),),
        temporal_basis=basis,
        snapshot_on=date(2025, 7, 15) if basis == TemporalBasis.SNAPSHOT else None,
        enrollment_basis=EnrollmentBasis.ACADEMIC_REGISTRATIONS,
    )
    return WorkflowRequest(identifier, (point,), tuple(m.identifier for m in definition.metrics))


def result(point: AnalysisRequest, metric: str, value: int = 3) -> AnalysisResult:
    unit = (
        MetricUnit.ACADEMIC_REGISTRATIONS
        if point.analysis_id == AnalysisId.ENROLLMENTS
        else MetricUnit.TEACHERS
    )
    timestamp = datetime(2025, 8, 1, tzinfo=UTC)
    return AnalysisResult(
        point,
        "12345678-1234-1234-1234-123456789abc",
        timestamp,
        ResultStatus.VALID,
        (MetricDatum(metric, unit, value),),
        (unit,),
        (SourceReference("synthetic.workflow", "fixture-v1", timestamp, timestamp),),
        "fixture-catalog",
        "fixture-rule",
        None,
        (),
    )


def test_six_workflows_are_linked_to_the_three_existing_families() -> None:
    catalog = load_catalog()
    for definition in WORKFLOWS:
        assert definition.identifier.value in catalog.get(definition.analysis_id).workflow_ids
    assert len(WORKFLOWS) == 6
    assert {d.identifier for d in WORKFLOW_DECISIONS} == {f"V{i:02}" for i in range(1, 25)}
    assert all(d.status == ApprovalStatus.PENDING for d in WORKFLOW_DECISIONS)
    assert all(
        set(m.decisions) <= {d.identifier for d in WORKFLOW_DECISIONS}
        for w in WORKFLOWS
        for m in w.metrics
    )
    assert phase3_blockers(catalog)
    assert get_workflow(WorkflowId.FUNCTIONS).phase == "encaixe_pendente"


def test_institutional_pending_records_do_not_block_synthetic_prompt3() -> None:
    catalog = load_catalog()
    assert phase3_blockers(catalog, mode=DataMode.SYNTHETIC) == ()
    assert "mapeamento_fisico_docente" in phase3_blockers(catalog, mode=DataMode.REAL)
    assert phase3_blockers(catalog) == phase3_blockers(catalog, mode=DataMode.REAL)
    with pytest.raises(ContractError):
        phase3_blockers(catalog, mode="synthetic")


@pytest.mark.parametrize("identifier", list(WorkflowId))
@pytest.mark.parametrize("mode", list(DataMode))
def test_proposed_metrics_never_silently_become_executable(identifier, mode) -> None:
    req = request(identifier)
    req = replace(req, points=(replace(req.points[0], mode=mode),))
    plans = plan_workflow(req)
    assert len(plans) == len(req.metric_ids)
    assert all(
        p.pending_decisions and "adaptador_nao_implementado" in p.execution_blockers for p in plans
    )
    if mode == DataMode.REAL:
        assert all({"V22", "V23"} <= set(p.execution_blockers) for p in plans)
    values = tuple(
        MetricResult(m, blocked_result(req.points[0], load_catalog())) for m in req.metric_ids
    )
    output = WorkflowResult(req, values, "fixture-app", "fixture-template")
    assert output.status == ResultStatus.BLOCKED
    assert all(not r.result.data for r in output.results)


def test_missing_scholarship_source_blocks_only_that_curve() -> None:
    req = request()
    point = req.points[0]
    values = tuple(
        MetricResult(
            m,
            blocked_result(point, load_catalog())
            if m == "bolsistas_matriculados"
            else result(point, m),
        )
        for m in req.metric_ids
    )
    output = WorkflowResult(req, values, "fixture-app", "fixture-template")
    assert output.status == ResultStatus.PARTIAL
    assert sum(r.result.status == ResultStatus.VALID for r in values) == 3
    payload = json.loads(json.dumps(output.to_dict()))
    assert payload["synthetic"] and payload["status"] == "parcial"
    plans = {p.metric_id: p for p in plan_workflow(req)}
    assert "V18" in plans["bolsistas_matriculados"].pending_decisions
    assert all(
        "V18" not in plans[m].pending_decisions
        for m in ("matriculados", "formados", "ingressantes")
    )


def test_qp_filter_cannot_reduce_the_general_denominator() -> None:
    req = request(WorkflowId.QP)
    with pytest.raises(ContractError):
        replace(
            req,
            points=(
                replace(
                    req.points[0],
                    filters=(*req.points[0].filters, EntityKey(EntityKind.CADRE, "SYN-QP")),
                ),
            ),
        )


@pytest.mark.parametrize(
    "kind",
    [
        EntityKind.EMPLOYMENT_DEPARTMENT,
        EntityKind.TEACHING_DEPARTMENT,
        EntityKind.DISTRIBUTION_DEPARTMENT,
    ],
)
def test_history_requires_historical_department(kind) -> None:
    req = request(WorkflowId.HISTORY)
    with pytest.raises(ContractError):
        replace(req, points=(replace(req.points[0], filters=(EntityKey(kind, "SYN"),)),))


def test_series_keeps_explicit_points_and_does_not_accept_overlaps_or_changed_units() -> None:
    req = request()
    first = req.points[0]
    second = replace(
        first, period=AcademicPeriod("SYN-S2", date(2025, 7, 16), date(2025, 12, 31), False)
    )
    series = replace(req, points=(first, second))
    assert not series.points[1].period.complete
    for bad in (
        first,
        replace(second, period=replace(second.period, starts_on=date(2025, 7, 15))),
        replace(second, enrollment_basis=EnrollmentBasis.UNIQUE_STUDENTS),
        replace(second, mode=DataMode.REAL),
        replace(second, filters=(EntityKey(EntityKind.COURSE, "SYN-OTHER"),)),
    ):
        with pytest.raises(ContractError):
            replace(req, points=(first, bad))


@pytest.mark.parametrize(
    "change",
    [
        {"metric_ids": ("arbitrary_sql",)},
        {"metric_ids": ("matriculados", "matriculados")},
        {"metric_ids": ()},
        {"points": ()},
        {"workflow_id": "R06"},
    ],
)
def test_closed_workflow_rejects_invalid_requests(change) -> None:
    with pytest.raises(ContractError):
        replace(request(), **change)


def test_result_requires_state_for_each_metric_and_period() -> None:
    req = request()
    values = tuple(MetricResult(m, result(req.points[0], m)) for m in req.metric_ids)
    assert WorkflowResult(req, values, "fixture", "fixture").status == ResultStatus.VALID
    for bad in (values[:-1], values + values[:1]):
        with pytest.raises(ContractError):
            WorkflowResult(req, bad, "fixture", "fixture")
    with pytest.raises(ContractError):
        MetricResult("ingressantes", result(req.points[0], "matriculados"))


@pytest.mark.parametrize("general,unknown", [(0, 0), (5, 1)])
def test_conclusive_qp_percentage_refuses_zero_or_incomplete_classification(
    general, unknown
) -> None:
    req = request(WorkflowId.QP)
    point = req.points[0]
    req = replace(
        req, metric_ids=("geral", "qp_confirmado", "classificacao_pendente", "participacao_qp")
    )
    values = tuple(
        MetricResult(m, result(point, m, n))
        for m, n in (("geral", general), ("qp_confirmado", 0), ("classificacao_pendente", unknown))
    )
    percentage = replace(
        result(point, "participacao_qp"),
        data=(MetricDatum("participacao_qp", MetricUnit.PERCENT, Decimal(0)),),
        units=(MetricUnit.PERCENT,),
    )
    with pytest.raises(ContractError):
        WorkflowResult(
            req, (*values, MetricResult("participacao_qp", percentage)), "fixture", "fixture"
        )


def test_catalog_rejects_workflow_from_another_family(tmp_path) -> None:
    from pathlib import Path

    import yaml

    path = Path(__file__).resolve().parents[1] / "config" / "analyses.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["analyses"][0]["workflow_ids"] = ["R06"]
    changed = tmp_path / "bad.yaml"
    changed.write_text(yaml.safe_dump(document), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(changed)
