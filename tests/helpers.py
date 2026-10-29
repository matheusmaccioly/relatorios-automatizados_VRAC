"""Auxiliares compartilhados da suíte sintética; não aprovam regra institucional."""

from vrac.analyses.contracts import (
    AnalysisId,
    AnalysisRequest,
    EntityKey,
    EntityKind,
    TemporalBasis,
)
from vrac.analyses.rules import FacultyRule
from vrac.settings import DataMode, Environment, Settings
from vrac.synthetic import demo_period

SETTINGS = Settings(environment=Environment.DEVELOPMENT, data_mode=DataMode.SYNTHETIC)


def request_for(
    rule: FacultyRule, *, period: str = "2026.1", department: str = "SINT-A"
) -> AnalysisRequest:
    """Solicitação coerente com a regra: unidade e base temporal vêm dela."""
    academic = demo_period(period)
    return AnalysisRequest(
        analysis_id=AnalysisId.FACULTY,
        period=academic,
        filters=(EntityKey(EntityKind.EMPLOYMENT_DEPARTMENT, department),),
        temporal_basis=rule.temporal_basis,
        snapshot_on=(academic.starts_on if rule.temporal_basis == TemporalBasis.SNAPSHOT else None),
        faculty_counting_basis=rule.counting_basis,
        semantic_variant_id=rule.semantic_variant_id,
    )
