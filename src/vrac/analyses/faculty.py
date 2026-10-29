"""Cálculo de composição docente, separado da interface e de qualquer fonte física.

O cálculo recebe a regra como parâmetro explícito. Nenhuma combinação é presumida:
população e referência temporal vêm de `FacultyRule`, e o resultado só pode ser
apresentado como válido quando a regra carrega aprovação humana registrada e o
catálogo não tem pendência para a análise.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import uuid4

from vrac.analyses.catalog import AnalysisCatalog
from vrac.analyses.contracts import (
    AnalysisId,
    AnalysisRequest,
    AnalysisResult,
    Availability,
    ContractError,
    EntityKey,
    EntityKind,
    FacultyCountingBasis,
    MetricDatum,
    ResultStatus,
    SourceReference,
    TemporalBasis,
)
from vrac.analyses.repository import (
    FacultyObservation,
    FacultyObservationSet,
    FacultyRepository,
    RealAdapterBlocked,
)
from vrac.analyses.rules import SUPPORTED_GROUPINGS, FacultyRule, rule_blockers
from vrac.settings import DataMode

GENERAL_METRIC = "geral"
UNCLASSIFIED_METRIC = "classificacao_pendente"

_PENDING_RULE_WARNING = (
    "Regra candidata não aprovada: o número demonstra o fluxo e não tem validade institucional."
)
_OVERLAP_WARNING = (
    "A mesma identidade aparece em mais de uma categoria; as parcelas não somam o "
    "total e não devem ser apresentadas como partes exclusivas."
)
_UNCLASSIFIED_WARNING = (
    "Há identidades sem classificação nesta dimensão; ausência de categoria não "
    "autoriza inferência nem exclusão do total."
)


@dataclass(frozen=True, slots=True)
class GroupCount:
    """Contagem de uma categoria observada, sem rateio ou reclassificação."""

    value: str
    count: int


@dataclass(frozen=True, slots=True)
class FacultyComputation:
    """Resultado aritmético puro, antes de qualquer juízo de aprovação."""

    general: int
    groups: tuple[GroupCount, ...]
    unclassified: int
    overlapping: int
    considered_observations: int
    grouping: EntityKind | None


def _competence_of(moment: date) -> date:
    return date(moment.year, moment.month, 1)


def _apply_temporal_basis(
    observations: tuple[FacultyObservation, ...],
    request: AnalysisRequest,
    rule: FacultyRule,
) -> tuple[FacultyObservation, ...]:
    """Aplicar a referência temporal da regra, sem converter calendário por conta própria."""
    if rule.temporal_basis == TemporalBasis.ANY_MONTH:
        return observations
    if rule.temporal_basis == TemporalBasis.SNAPSHOT:
        target = _competence_of(request.snapshot_on)
        return tuple(item for item in observations if item.reference_month == target)
    if not observations:
        return ()
    if rule.temporal_basis == TemporalBasis.LATEST_IN_SELECTION:
        latest = max(item.reference_month for item in observations)
        return tuple(item for item in observations if item.reference_month == latest)
    # LATEST_PER_ENTITY: a última competência de cada matrícula funcional.
    latest_by_registration: dict[str, date] = {}
    for item in observations:
        key = item.registration.identifier
        current = latest_by_registration.get(key)
        if current is None or item.reference_month > current:
            latest_by_registration[key] = item.reference_month
    return tuple(
        item
        for item in observations
        if item.reference_month == latest_by_registration[item.registration.identifier]
    )


def _identity(observation: FacultyObservation, rule: FacultyRule) -> str:
    if rule.counting_basis == FacultyCountingBasis.PEOPLE:
        return observation.person.identifier
    return observation.registration.identifier


def compute_faculty_composition(
    observations: tuple[FacultyObservation, ...],
    request: AnalysisRequest,
    rule: FacultyRule,
    *,
    grouping: EntityKind | None = None,
) -> FacultyComputation:
    """Contar identidades distintas conforme a regra; nunca somar competências."""
    if grouping is not None and grouping not in SUPPORTED_GROUPINGS:
        raise ContractError("Dimensão de distribuição fora da lista fechada.")
    if request.analysis_id != AnalysisId.FACULTY:
        raise ContractError("Cálculo docente aplicado a outra análise.")
    if request.faculty_counting_basis != rule.counting_basis:
        raise ContractError("A unidade da solicitação difere da regra informada.")
    if request.temporal_basis != rule.temporal_basis:
        raise ContractError("A base temporal da solicitação difere da regra informada.")

    considered = _apply_temporal_basis(observations, request, rule)
    identities = {_identity(item, rule) for item in considered}

    buckets: dict[str, set[str]] = {}
    unclassified: set[str] = set()
    membership: dict[str, int] = dict.fromkeys(identities, 0)
    if grouping is not None:
        for item in considered:
            identity = _identity(item, rule)
            value = item.attribute(grouping)
            if value is None:
                unclassified.add(identity)
            else:
                buckets.setdefault(value, set()).add(identity)
        for identity in identities:
            places = sum(1 for members in buckets.values() if identity in members)
            membership[identity] = places + (1 if identity in unclassified else 0)

    return FacultyComputation(
        general=len(identities),
        groups=tuple(GroupCount(value, len(members)) for value, members in sorted(buckets.items())),
        unclassified=len(unclassified),
        overlapping=sum(1 for places in membership.values() if places > 1),
        considered_observations=len(considered),
        grouping=grouping,
    )


def _metrics(computation: FacultyComputation, rule: FacultyRule) -> tuple[MetricDatum, ...]:
    """Ausência de registros produz `sem_registros`, nunca zero."""
    if computation.considered_observations == 0:
        return (
            MetricDatum(
                metric=GENERAL_METRIC,
                unit=rule.unit,
                value=None,
                availability=Availability.NO_ROWS,
            ),
        )
    data = [MetricDatum(metric=GENERAL_METRIC, unit=rule.unit, value=computation.general)]
    if computation.grouping is not None:
        data.extend(
            MetricDatum(
                metric=f"por_{computation.grouping.value}",
                unit=rule.unit,
                value=group.count,
                dimensions=(EntityKey(computation.grouping, group.value),),
            )
            for group in computation.groups
        )
        data.append(
            MetricDatum(
                metric=UNCLASSIFIED_METRIC,
                unit=rule.unit,
                value=computation.unclassified,
            )
        )
    return tuple(data)


def faculty_result(
    request: AnalysisRequest,
    rule: FacultyRule,
    catalog: AnalysisCatalog,
    repository: FacultyRepository,
    *,
    grouping: EntityKind | None = None,
) -> AnalysisResult:
    """Executar o fluxo e decidir o estado; modo real permanece bloqueado.

    Em modo real o repositório não é consultado: o bloqueio é decidido antes, sem
    abrir conexão. Em modo sintético, uma regra sem aprovação produz resultado
    parcial com as pendências nomeadas, nunca um resultado válido.
    """
    blockers = rule_blockers(rule, catalog)
    if request.mode == DataMode.REAL:
        return _blocked(
            request,
            rule,
            catalog,
            (
                "Modo real bloqueado: fonte física, escopo autorizado e autenticação "
                "institucional não registrados.",
                *(f"Pendência: {item}." for item in blockers),
            ),
        )
    try:
        observed = repository.fetch(request)
    except RealAdapterBlocked as error:
        return _blocked(request, rule, catalog, (str(error),))

    computation = compute_faculty_composition(
        observed.observations, request, rule, grouping=grouping
    )
    data = _metrics(computation, rule)
    warnings = _warnings(computation, rule, observed, blockers)
    unresolved = any(item.availability != Availability.OBSERVED for item in data)
    status = (
        ResultStatus.VALID
        if not blockers and not unresolved and request.period.complete
        else ResultStatus.PARTIAL
    )
    return AnalysisResult(
        request=request,
        execution_id=str(uuid4()),
        created_at=datetime.now(UTC),
        status=status,
        data=data,
        units=(rule.unit,),
        origins=observed.origins,
        catalog_version=catalog.version,
        rule_version=rule.rule_version,
        query_version=None,
        warnings=warnings,
    )


def _warnings(
    computation: FacultyComputation,
    rule: FacultyRule,
    observed: FacultyObservationSet,
    blockers: tuple[str, ...],
) -> tuple[str, ...]:
    warnings: list[str] = []
    if blockers:
        warnings.append(_PENDING_RULE_WARNING)
        warnings.extend(f"Pendência: {item}." for item in blockers)
    warnings.extend(rule.limitations)
    warnings.extend(observed.coverage_warnings)
    if computation.considered_observations == 0:
        warnings.append(
            "Nenhum registro no recorte informado. Ausência de registros não significa zero."
        )
    if computation.unclassified:
        warnings.append(_UNCLASSIFIED_WARNING)
    if computation.overlapping:
        warnings.append(_OVERLAP_WARNING)
    return tuple(dict.fromkeys(warnings))


def _blocked(
    request: AnalysisRequest,
    rule: FacultyRule,
    catalog: AnalysisCatalog,
    reasons: tuple[str, ...],
) -> AnalysisResult:
    definition = catalog.get(AnalysisId.FACULTY)
    return AnalysisResult(
        request=request,
        execution_id=str(uuid4()),
        created_at=datetime.now(UTC),
        status=ResultStatus.BLOCKED,
        data=(),
        units=(rule.unit,),
        origins=tuple(
            SourceReference(name, "unmapped", None, None) for name in definition.logical_sources
        ),
        catalog_version=catalog.version,
        rule_version=rule.rule_version,
        query_version=None,
        warnings=tuple(dict.fromkeys(reasons)),
    )


__all__ = [
    "GENERAL_METRIC",
    "UNCLASSIFIED_METRIC",
    "FacultyComputation",
    "GroupCount",
    "compute_faculty_composition",
    "faculty_result",
]
