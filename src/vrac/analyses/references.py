"""Referências e comparação de valores fornecidos; não calcula resultados."""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, InvalidOperation
from enum import StrEnum

from vrac.analyses.catalog import ApprovalStatus
from vrac.analyses.contracts import (
    COUNT_UNITS,
    HOUR_UNITS,
    AnalysisRequest,
    AnalysisResult,
    Availability,
    ContractError,
    MetricDatum,
    ResultStatus,
    SourceReference,
    require_date,
    require_text,
)
from vrac.settings import DataMode


class ComparisonStatus(StrEnum):
    MATCH = "coincide"
    MISMATCH = "diverge"
    BLOCKED = "bloqueado"


@dataclass(frozen=True, slots=True)
class HoursRoundingRule:
    decimal_places: int
    rounding: str
    reviewed_on: date
    reviewer_role: str
    evidence_reference: str
    synthetic: bool

    def __post_init__(self) -> None:
        if (
            type(self.decimal_places) is not int
            or not 0 <= self.decimal_places <= 6
            or self.rounding not in {ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_DOWN}
            or type(self.synthetic) is not bool
        ):
            raise ContractError("Regra de arredondamento inválida.")
        require_date(self.reviewed_on)
        require_text(self.reviewer_role)
        require_text(self.evidence_reference)


@dataclass(frozen=True, slots=True)
class ComparisonOutcome:
    status: ComparisonStatus
    reason: str


def compare_reference_values(
    expected: MetricDatum,
    actual: MetricDatum,
    *,
    mode: DataMode = DataMode.SYNTHETIC,
    hours_rounding: HoursRoundingRule | None = None,
) -> ComparisonOutcome:
    """O chamador deve confirmar mesmo recorte/regra/data; não há tolerância ajustável."""
    if (
        not isinstance(mode, DataMode)
        or not isinstance(expected, MetricDatum)
        or not isinstance(actual, MetricDatum)
    ):
        raise ContractError("Modo da comparação inválido.")
    if (expected.metric, expected.unit, expected.dimensions, expected.kind) != (
        actual.metric,
        actual.unit,
        actual.dimensions,
        actual.kind,
    ):
        return ComparisonOutcome(
            ComparisonStatus.BLOCKED, "Métrica, unidade ou dimensões diferentes."
        )
    if (
        expected.availability != Availability.OBSERVED
        or actual.availability != Availability.OBSERVED
    ):
        return ComparisonOutcome(ComparisonStatus.BLOCKED, "Ausência, nulo e falha não são zero.")
    if expected.unit in COUNT_UNITS:
        matches = expected.value == actual.value
    elif expected.unit in HOUR_UNITS:
        if hours_rounding is None or hours_rounding.synthetic != (mode == DataMode.SYNTHETIC):
            return ComparisonOutcome(
                ComparisonStatus.BLOCKED, "Critério de horas não acordado para este modo."
            )
        try:
            quantum = Decimal(1).scaleb(-hours_rounding.decimal_places)
            matches = expected.value.quantize(
                quantum, rounding=hours_rounding.rounding
            ) == actual.value.quantize(quantum, rounding=hours_rounding.rounding)
        except InvalidOperation:
            return ComparisonOutcome(
                ComparisonStatus.BLOCKED, "Precisão incompatível com o critério acordado."
            )
    else:
        return ComparisonOutcome(
            ComparisonStatus.BLOCKED, "Critério percentual ainda exige aprovação."
        )
    return ComparisonOutcome(
        ComparisonStatus.MATCH if matches else ComparisonStatus.MISMATCH,
        "Comparação exata de inteiros ou após arredondamento explicitamente registrado.",
    )


@dataclass(frozen=True, slots=True)
class ReferenceCase:
    identifier: str
    request: AnalysisRequest
    rule_version: str
    origins: tuple[SourceReference, ...]
    expected: tuple[MetricDatum, ...]
    validation_status: ApprovalStatus
    synthetic: bool
    reviewer_role: str | None = None
    reviewed_on: date | None = None
    evidence_reference: str | None = None

    def __post_init__(self) -> None:
        require_text(self.identifier)
        require_text(self.rule_version)
        if (
            not isinstance(self.request, AnalysisRequest)
            or not isinstance(self.validation_status, ApprovalStatus)
            or type(self.synthetic) is not bool
            or not isinstance(self.origins, tuple)
            or not all(isinstance(item, SourceReference) for item in self.origins)
            or not isinstance(self.expected, tuple)
            or not all(isinstance(item, MetricDatum) for item in self.expected)
            or self.synthetic != (self.request.mode == DataMode.SYNTHETIC)
        ):
            raise ContractError("Caso de referência inválido.")
        if self.validation_status == ApprovalStatus.APPROVED:
            if self.synthetic or not self.expected or not self.origins:
                raise ContractError("Fixture sintética não constitui aprovação funcional humana.")
            require_text(self.reviewer_role)
            require_date(self.reviewed_on)
            require_text(self.evidence_reference)
            if any(origin.extracted_at is None for origin in self.origins):
                raise ContractError("Referência aprovada exige referência temporal da origem.")


def compare_reference_case(
    reference: ReferenceCase,
    result: AnalysisResult,
    *,
    hours_rounding: HoursRoundingRule | None = None,
) -> ComparisonOutcome:
    """Conciliação de exemplos recebidos, sem calcular nem aprovar uma análise."""
    if (
        reference.request != result.request
        or reference.rule_version != result.rule_version
        or result.status != ResultStatus.VALID
        or not reference.expected
        or not reference.origins
        or reference.validation_status == ApprovalStatus.REJECTED
    ):
        return ComparisonOutcome(
            ComparisonStatus.BLOCKED, "Recorte, regra ou situação incompatíveis."
        )
    if any(source.updated_at is None for source in (*reference.origins, *result.origins)):
        return ComparisonOutcome(
            ComparisonStatus.BLOCKED,
            "Atualização da origem desconhecida; comparação requer revisão.",
        )
    if not reference.synthetic and reference.validation_status != ApprovalStatus.APPROVED:
        return ComparisonOutcome(
            ComparisonStatus.BLOCKED, "Referência real ainda não aprovada por Talita."
        )

    def origin_key(source: SourceReference):
        return source.logical_source, source.version, source.updated_at

    if {origin_key(s) for s in reference.origins} != {origin_key(s) for s in result.origins}:
        return ComparisonOutcome(ComparisonStatus.BLOCKED, "Versão ou atualização da origem mudou.")

    def metric_key(item: MetricDatum):
        return item.metric, item.unit, item.dimensions, item.kind

    expected = {metric_key(item): item for item in reference.expected}
    actual = {metric_key(item): item for item in result.data}
    if (
        len(expected) != len(reference.expected)
        or len(actual) != len(result.data)
        or expected.keys() != actual.keys()
    ):
        return ComparisonOutcome(
            ComparisonStatus.BLOCKED, "Conjunto de métricas diferente ou duplicado."
        )
    outcomes = [
        compare_reference_values(
            item, actual[key], mode=result.request.mode, hours_rounding=hours_rounding
        )
        for key, item in expected.items()
    ]
    if any(item.status == ComparisonStatus.BLOCKED for item in outcomes):
        return ComparisonOutcome(
            ComparisonStatus.BLOCKED, "Comparação depende de dados ou critério acordado."
        )
    if any(item.status == ComparisonStatus.MISMATCH for item in outcomes):
        return ComparisonOutcome(
            ComparisonStatus.MISMATCH,
            "Valores divergentes; não alterar a tolerância para conciliá-los.",
        )
    return ComparisonOutcome(
        ComparisonStatus.MATCH,
        "Valores conferidos no mesmo recorte e referência; não constitui aprovação humana.",
    )
