"""Catálogo público de definições; nunca carrega conexão ou executa fórmulas."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from importlib.resources import files
from pathlib import Path
from uuid import uuid4

import yaml

from vrac.analyses.contracts import (
    AnalysisId,
    AnalysisRequest,
    AnalysisResult,
    ContractError,
    MetricUnit,
    ResultStatus,
    SourceReference,
    TemporalBasis,
    require_text,
)


class CatalogError(ValueError):
    pass


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DecisionArea(StrEnum):
    SOURCE = "source"
    GRANULARITY = "granularity"
    CALCULATION = "calculation"
    COMPARISON = "comparison"
    FUNCTIONAL = "functional"


@dataclass(frozen=True, slots=True)
class DefinitionDecision:
    id: str
    area: DecisionArea
    question: str
    owner_role: str
    status: ApprovalStatus
    reviewed_on: date | None
    evidence_reference: str | None

    def __post_init__(self) -> None:
        for value in (self.id, self.question, self.owner_role):
            require_text(value)
        if not isinstance(self.area, DecisionArea) or not isinstance(self.status, ApprovalStatus):
            raise ContractError("Decisão do catálogo inválida.")
        if self.reviewed_on is not None and type(self.reviewed_on) is not date:
            raise ContractError("Data de revisão inválida.")
        if self.evidence_reference is not None:
            require_text(self.evidence_reference)
        if self.status == ApprovalStatus.APPROVED:
            if self.reviewed_on is None:
                raise ContractError("Aprovação exige data e evidência humana registrada.")
            require_text(self.evidence_reference)


@dataclass(frozen=True, slots=True)
class SemanticVariant:
    """Leitura documental, sem expressão executável nem escolha institucional implícita."""

    id: str
    evidence_reference: str
    model: str
    measure_references: tuple[str, ...]
    logical_source: str
    unit: MetricUnit | None
    temporal_basis: TemporalBasis
    description: str
    constraints: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.id, self.evidence_reference, self.logical_source, self.description):
            require_text(value)
        if self.model not in {"A", "B"}:
            raise CatalogError("Modelo fora do escopo acadêmico.")
        if self.unit is not None and not isinstance(self.unit, MetricUnit):
            raise CatalogError("Unidade documental inválida.")
        if (
            not isinstance(self.temporal_basis, TemporalBasis)
            or self.temporal_basis == TemporalBasis.UNDEFINED
        ):
            raise CatalogError("Base temporal documental inválida.")
        if not self.measure_references or not self.constraints:
            raise CatalogError("Variante sem evidência ou limites.")
        for ref in self.measure_references:
            if not ref.startswith(f"{self.model}-M-") or not ref[4:].isdigit():
                raise CatalogError("Referência de medida pertence a outro modelo.")
        for constraint in self.constraints:
            require_text(constraint)


@dataclass(frozen=True, slots=True)
class AnalysisDefinition:
    id: AnalysisId
    workflow_ids: tuple[str, ...]
    priority: int
    question: str
    population: str
    granularity: str
    units: tuple[MetricUnit, ...]
    logical_sources: tuple[str, ...]
    documentary_references: tuple[str, ...]
    semantic_variants: tuple[SemanticVariant, ...]
    selected_semantic_variant: str | None
    physical_source_reference: str | None
    logical_keys: tuple[str, ...]
    parameters: tuple[str, ...]
    filters: tuple[str, ...]
    formula: str
    exceptions: tuple[str, ...]
    period_definition: str
    owner_role: str
    rule_version: str
    comparison_policy: str
    validation_status: ApprovalStatus
    decisions: tuple[DefinitionDecision, ...]


@dataclass(frozen=True, slots=True)
class DocumentaryEvidence:
    id: str
    reference: str
    kind: str
    summary: str
    detailed_document_available: bool
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.id, self.reference, self.kind, self.summary):
            require_text(value)
        if self.kind not in {"semantic_model_inspection_log", "semantic_model_documentation"}:
            raise CatalogError("Tipo de evidência documental fora do escopo.")
        if type(self.detailed_document_available) is not bool or not self.limitations:
            raise CatalogError("Limites da evidência documental não informados.")
        for limitation in self.limitations:
            require_text(limitation)


@dataclass(frozen=True, slots=True)
class AnalysisCatalog:
    version: str
    analyses: tuple[AnalysisDefinition, ...]
    documentary_evidence: tuple[DocumentaryEvidence, ...]

    def get(self, analysis_id: AnalysisId) -> AnalysisDefinition:
        if not isinstance(analysis_id, AnalysisId):
            raise CatalogError("Análise fora da lista fechada.")
        return next(item for item in self.analyses if item.id == analysis_id)


class _UniqueSafeLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in result:
                raise CatalogError("Catálogo inválido; campos duplicados não são permitidos.")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def load_catalog(path: Path | None = None) -> AnalysisCatalog:
    try:
        if path is None:
            checkout = Path(__file__).resolve().parents[3] / "config" / "analyses.yaml"
            source = (
                checkout if checkout.is_file() else files(__package__).joinpath("analyses.yaml")
            )
        else:
            source = path
        text = source.read_text(encoding="utf-8")
        if len(text.encode("utf-8")) > 262144:
            raise CatalogError("Catálogo excede o tamanho permitido.")
        document = yaml.load(text, Loader=_UniqueSafeLoader)
        if not isinstance(document, dict) or set(document) != {
            "catalog_version",
            "documentary_evidence",
            "analyses",
        }:
            raise CatalogError("Estrutura de catálogo inválida.")
        require_text(document["catalog_version"])
        evidence = []
        if not isinstance(document["documentary_evidence"], list):
            raise CatalogError("Registro de evidências inválido.")
        for raw in document["documentary_evidence"]:
            values = dict(raw)
            if not isinstance(values["limitations"], list):
                raise CatalogError("Limitações documentais inválidas.")
            values["limitations"] = tuple(values["limitations"])
            evidence.append(DocumentaryEvidence(**values))
        evidence_ids = {record.id for record in evidence}
        if len(evidence_ids) != len(evidence):
            raise CatalogError("Evidências documentais duplicadas.")
        entries = []
        for raw in document["analyses"]:
            values = dict(raw)
            values["id"] = AnalysisId(values["id"])
            workflow_ids = values["workflow_ids"]
            expected_workflows = {
                AnalysisId.FACULTY: ["R01", "R02", "R03", "R05"],
                AnalysisId.ENROLLMENTS: ["R06"],
                AnalysisId.WORKLOAD: ["R04"],
            }[values["id"]]
            if workflow_ids != expected_workflows:
                raise CatalogError("Roteiros incompatíveis com a família de análise.")
            values["workflow_ids"] = tuple(workflow_ids)
            values["validation_status"] = ApprovalStatus(values["validation_status"])
            if type(values["priority"]) is not int or values["priority"] < 1:
                raise CatalogError("Prioridade inválida.")
            for key in (
                "question",
                "population",
                "granularity",
                "formula",
                "period_definition",
                "owner_role",
                "rule_version",
                "comparison_policy",
            ):
                require_text(values[key])
            for key in (
                "logical_sources",
                "documentary_references",
                "logical_keys",
                "parameters",
                "filters",
                "exceptions",
            ):
                if not isinstance(values[key], list) or not values[key]:
                    raise CatalogError("Definição incompleta.")
                for item in values[key]:
                    require_text(item)
                values[key] = tuple(values[key])
            if not set(values["documentary_references"]) <= evidence_ids:
                raise CatalogError("Referência documental não registrada.")
            values["units"] = tuple(MetricUnit(unit) for unit in values["units"])
            if not values["units"]:
                raise CatalogError("Unidade ausente.")
            variants = []
            for raw_variant in values["semantic_variants"]:
                variant = dict(raw_variant)
                for key in ("measure_references", "constraints"):
                    if not isinstance(variant[key], list):
                        raise CatalogError("Estrutura de variante inválida.")
                    variant[key] = tuple(variant[key])
                variant["unit"] = (
                    MetricUnit(variant["unit"]) if variant["unit"] is not None else None
                )
                variant["temporal_basis"] = TemporalBasis(variant["temporal_basis"])
                parsed = SemanticVariant(**variant)
                if (
                    parsed.evidence_reference not in values["documentary_references"]
                    or parsed.logical_source not in values["logical_sources"]
                    or (parsed.unit is not None and parsed.unit not in values["units"])
                    or parsed.model != ("B" if values["id"] == AnalysisId.ENROLLMENTS else "A")
                    or (parsed.unit is None and values["id"] != AnalysisId.WORKLOAD)
                    or not any(
                        e.id == parsed.evidence_reference and e.detailed_document_available
                        for e in evidence
                    )
                ):
                    raise CatalogError("Variante sem fonte ou evidência compatível.")
                variants.append(parsed)
            if not variants or len({v.id for v in variants}) != len(variants):
                raise CatalogError("Variantes ausentes ou repetidas.")
            values["semantic_variants"] = tuple(variants)
            selected = values["selected_semantic_variant"]
            if selected is not None and (
                selected not in {v.id for v in variants}
                or values["validation_status"] != ApprovalStatus.APPROVED
            ):
                raise CatalogError("Seleção de variante exige definição aprovada.")
            if values["physical_source_reference"] is not None:
                require_text(values["physical_source_reference"])
            decisions = []
            for decision in values["decisions"]:
                decision = dict(decision)
                decision["area"] = DecisionArea(decision["area"])
                decision["status"] = ApprovalStatus(decision["status"])
                decisions.append(DefinitionDecision(**decision))
            if {item.area for item in decisions} != set(DecisionArea) or len(
                {d.id for d in decisions}
            ) != len(decisions):
                raise CatalogError("Decisões obrigatórias ausentes ou repetidas.")
            values["decisions"] = tuple(decisions)
            if values["validation_status"] == ApprovalStatus.APPROVED and (
                values["physical_source_reference"] is None
                or selected is None
                or any(item.status != ApprovalStatus.APPROVED for item in decisions)
            ):
                raise CatalogError("Aprovação incompleta não libera uma análise.")
            entries.append(AnalysisDefinition(**values))
        if len(entries) != len(AnalysisId) or {entry.id for entry in entries} != set(AnalysisId):
            raise CatalogError("O catálogo deve conter apenas as três análises do escopo.")
        if len({entry.priority for entry in entries}) != len(entries):
            raise CatalogError("Prioridades repetidas.")
        entries.sort(key=lambda item: item.priority)
        if [entry.id for entry in entries] != list(AnalysisId):
            raise CatalogError("Priorizar composição docente, matrículas e carga, nesta ordem.")
        return AnalysisCatalog(document["catalog_version"], tuple(entries), tuple(evidence))
    except (OSError, yaml.YAMLError, ValueError, TypeError, KeyError, AttributeError):
        raise CatalogError(
            "Catálogo inválido ou indisponível; nenhuma análise foi executada."
        ) from None


def pending_decisions(definition: AnalysisDefinition) -> tuple[str, ...]:
    return tuple(item.id for item in definition.decisions if item.status != ApprovalStatus.APPROVED)


def blocked_result(request: AnalysisRequest, catalog: AnalysisCatalog) -> AnalysisResult:
    """Representar o bloqueio sem consulta, valores fictícios ou extração inventada."""
    definition = catalog.get(request.analysis_id)
    warnings = [
        "Adaptador de análise não implementado nesta fase; nenhuma consulta ou cálculo executado.",
        "Fonte, granularidade, cálculo, referência e aprovação funcional exigem registro humano.",
    ]
    warnings.extend(f"Decisão pendente: {item}." for item in pending_decisions(definition))
    if not any(
        evidence.id in definition.documentary_references and evidence.detailed_document_available
        for evidence in catalog.documentary_evidence
    ):
        warnings.append(
            "Há registro de inspeção semântica, mas o documento detalhado e o mapeamento "
            "dos objetos desta análise continuam pendentes."
        )
    return AnalysisResult(
        request=request,
        execution_id=str(uuid4()),
        created_at=datetime.now(UTC),
        status=ResultStatus.BLOCKED,
        data=(),
        units=definition.units,
        origins=tuple(
            SourceReference(name, "unmapped", None, None) for name in definition.logical_sources
        ),
        catalog_version=catalog.version,
        rule_version=definition.rule_version,
        query_version=None,
        warnings=tuple(warnings),
    )
