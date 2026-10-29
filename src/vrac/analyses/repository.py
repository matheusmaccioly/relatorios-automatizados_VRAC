"""Porta de acesso a observações docentes; nenhum nome físico institucional aqui.

A observação é a linha lógica que o cálculo consome: pessoa, matrícula funcional,
departamento do vínculo e competência, mais os atributos de distribuição. Converter
uma fonte física nessa forma é responsabilidade de um adaptador aprovado, que ainda
não existe. O adaptador real permanece bloqueado e não abre conexão.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol

from vrac.analyses.contracts import (
    AnalysisRequest,
    ContractError,
    EntityKey,
    EntityKind,
    SourceReference,
    require_date,
)
from vrac.settings import DataMode
from vrac.synthetic import DATASET_VERSION, SyntheticDataset

#: Rótulo que acompanha toda observação sintética, inclusive em exportações.
SYNTHETIC_SOURCE = "demonstracao_sintetica"


class RealAdapterBlocked(PermissionError):
    """Modo real sem fonte física aprovada; não revelar infraestrutura."""


@dataclass(frozen=True, slots=True)
class FacultyObservation:
    """Uma competência de um vínculo. Nulo e ausente permanecem distintos de zero."""

    person: EntityKey
    registration: EntityKey
    employment_department: EntityKey
    reference_month: date
    cadre: str | None = None
    functional_category: str | None = None
    employment_category: str | None = None
    status: str | None = None

    def __post_init__(self) -> None:
        pairs = (
            (self.person, EntityKind.TEACHER),
            (self.registration, EntityKind.FUNCTIONAL_REGISTRATION),
            (self.employment_department, EntityKind.EMPLOYMENT_DEPARTMENT),
        )
        for value, kind in pairs:
            if not isinstance(value, EntityKey) or value.kind != kind:
                raise ContractError("Chave lógica da observação docente inválida.")
        require_date(self.reference_month)
        if self.reference_month.day != 1:
            raise ContractError("A competência deve ser o primeiro dia do mês de referência.")
        for attribute in (
            self.cadre,
            self.functional_category,
            self.employment_category,
            self.status,
        ):
            if attribute is not None and (not isinstance(attribute, str) or not attribute.strip()):
                raise ContractError("Atributo de distribuição vazio não equivale a nulo.")

    def attribute(self, kind: EntityKind) -> str | None:
        """Ler um atributo de distribuição sem inferir categoria ausente."""
        values = {
            EntityKind.CADRE: self.cadre,
            EntityKind.FUNCTIONAL_CATEGORY: self.functional_category,
            EntityKind.EMPLOYMENT_CATEGORY: self.employment_category,
            EntityKind.STATUS: self.status,
        }
        if kind not in values:
            raise ContractError("Dimensão de distribuição não disponível na observação.")
        return values[kind]


@dataclass(frozen=True, slots=True)
class FacultyObservationSet:
    """Observações com proveniência e limites de cobertura preservados."""

    observations: tuple[FacultyObservation, ...]
    origins: tuple[SourceReference, ...]
    coverage_warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.observations, tuple) or not all(
            isinstance(item, FacultyObservation) for item in self.observations
        ):
            raise ContractError("Conjunto de observações docentes inválido.")
        if (
            not isinstance(self.origins, tuple)
            or not self.origins
            or not all(isinstance(item, SourceReference) for item in self.origins)
        ):
            raise ContractError("Observações exigem origem lógica e referência temporal.")
        if not isinstance(self.coverage_warnings, tuple):
            raise ContractError("Avisos de cobertura inválidos.")


class FacultyRepository(Protocol):
    """Contrato mínimo do acesso a dados; o cálculo não conhece a fonte."""

    def fetch(self, request: AnalysisRequest) -> FacultyObservationSet: ...


@dataclass(frozen=True, slots=True)
class SyntheticFacultyRepository:
    """Traduz a fixture determinística para observações lógicas.

    A fixture declara período por rótulo e competência por texto `AAAA-MM`. A conversão
    é local à demonstração e não define calendário institucional.
    """

    dataset: SyntheticDataset

    def fetch(self, request: AnalysisRequest) -> FacultyObservationSet:
        if request.mode != DataMode.SYNTHETIC:
            raise RealAdapterBlocked(
                "O repositório sintético não atende modo real. Nenhum dado foi carregado."
            )
        departments = {
            key.identifier
            for key in request.filters
            if key.kind == EntityKind.EMPLOYMENT_DEPARTMENT
        }
        observations = tuple(
            FacultyObservation(
                person=EntityKey(EntityKind.TEACHER, row.teacher_id),
                registration=EntityKey(EntityKind.FUNCTIONAL_REGISTRATION, row.contract_id),
                employment_department=EntityKey(EntityKind.EMPLOYMENT_DEPARTMENT, row.department),
                reference_month=_competence(row.reference_month),
                employment_category=row.employment_type,
            )
            for row in sorted(
                self.dataset.faculty,
                key=lambda item: (item.reference_month, item.teacher_id, item.contract_id),
            )
            if row.period == request.period.identifier
            and (not departments or row.department in departments)
        )
        return FacultyObservationSet(
            observations=observations,
            origins=(
                SourceReference(
                    logical_source=SYNTHETIC_SOURCE,
                    version=self.dataset.version,
                    extracted_at=datetime.now(UTC),
                    updated_at=None,
                ),
            ),
            coverage_warnings=(
                "Dados fictícios: a fixture não representa cobertura, quadro ou situação reais.",
                "A fixture não informa quadro, categoria funcional nem situação do vínculo.",
            ),
        )


@dataclass(frozen=True, slots=True)
class BlockedFacultyRepository:
    """Lugar do adaptador institucional: recusa antes de qualquer conexão."""

    reason: str = (
        "Adaptador real de composição docente bloqueado: fonte física, escopo e "
        "aprovação humana não registrados."
    )

    def fetch(self, request: AnalysisRequest) -> FacultyObservationSet:
        raise RealAdapterBlocked(self.reason)


def _competence(reference_month: str) -> date:
    """Converter `AAAA-MM` da fixture; qualquer outro formato é erro, não suposição."""
    try:
        year, month = reference_month.split("-")
        return date(int(year), int(month), 1)
    except (ValueError, AttributeError):
        raise ContractError("Competência fictícia em formato inesperado.") from None


def select_repository(request: AnalysisRequest, dataset: SyntheticDataset) -> FacultyRepository:
    """Modo real nunca recebe a fixture; falha não ativa dados sintéticos."""
    if request.mode == DataMode.SYNTHETIC:
        if dataset.version != DATASET_VERSION or not dataset.synthetic:
            raise ContractError("Conjunto sintético não identificado.")
        return SyntheticFacultyRepository(dataset)
    return BlockedFacultyRepository()
