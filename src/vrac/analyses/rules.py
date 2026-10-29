"""Regras docentes candidatas, versionadas e explícitas; nenhuma é aprovada aqui.

A definição institucional de composição docente continua pendente (Q-003). Este
módulo não escolhe uma regra: registra as combinações documentadas de população e
referência temporal como candidatas, cada uma amarrada às decisões do catálogo que
ainda faltam. A aprovação só existe com data e evidência humana registradas, nos
mesmos termos exigidos por `DefinitionDecision`.
"""

from dataclasses import dataclass
from datetime import date

from vrac.analyses.catalog import AnalysisCatalog, ApprovalStatus, pending_decisions
from vrac.analyses.contracts import (
    AnalysisId,
    ContractError,
    EntityKind,
    FacultyCountingBasis,
    MetricUnit,
    TemporalBasis,
    require_text,
)

#: Bases temporais que o cálculo sabe aplicar. Fora desta lista, nada é presumido.
SUPPORTED_TEMPORAL_BASES = (
    TemporalBasis.SNAPSHOT,
    TemporalBasis.ANY_MONTH,
    TemporalBasis.LATEST_PER_ENTITY,
    TemporalBasis.LATEST_IN_SELECTION,
)

#: Dimensões de distribuição aceitas; cada uma vem da observação, não de inferência.
SUPPORTED_GROUPINGS = (
    EntityKind.CADRE,
    EntityKind.FUNCTIONAL_CATEGORY,
    EntityKind.EMPLOYMENT_CATEGORY,
    EntityKind.STATUS,
)

_UNIT_BY_BASIS = {
    FacultyCountingBasis.PEOPLE: MetricUnit.TEACHERS,
    FacultyCountingBasis.FUNCTIONAL_REGISTRATIONS: MetricUnit.FUNCTIONAL_REGISTRATIONS,
}


@dataclass(frozen=True, slots=True)
class RuleApproval:
    """Aprovação de regra: mesma exigência de data e evidência do catálogo."""

    status: ApprovalStatus
    reviewed_on: date | None
    evidence_reference: str | None
    owner_role: str

    def __post_init__(self) -> None:
        if not isinstance(self.status, ApprovalStatus):
            raise ContractError("Situação de aprovação da regra inválida.")
        require_text(self.owner_role)
        if self.reviewed_on is not None and type(self.reviewed_on) is not date:
            raise ContractError("Data de revisão da regra inválida.")
        if self.status == ApprovalStatus.APPROVED:
            if self.reviewed_on is None:
                raise ContractError("Aprovação exige data e evidência humana registrada.")
            require_text(self.evidence_reference)
        elif self.evidence_reference is not None:
            require_text(self.evidence_reference)

    @property
    def approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED


@dataclass(frozen=True, slots=True)
class FacultyRule:
    """Uma combinação candidata de população e referência temporal.

    `counting_basis` e `temporal_basis` são parâmetros, não hipóteses escolhidas pelo
    código. `requires_decisions` lista o que o catálogo ainda não aprovou; enquanto
    houver pendência, o resultado não pode ser apresentado como válido.
    """

    rule_id: str
    rule_version: str
    label: str
    counting_basis: FacultyCountingBasis
    temporal_basis: TemporalBasis
    semantic_variant_id: str | None
    requires_decisions: tuple[str, ...]
    limitations: tuple[str, ...]
    approval: RuleApproval

    def __post_init__(self) -> None:
        for value in (self.rule_id, self.rule_version, self.label):
            require_text(value)
        if not isinstance(self.counting_basis, FacultyCountingBasis):
            raise ContractError("Base de contagem docente inválida.")
        if self.temporal_basis not in SUPPORTED_TEMPORAL_BASES:
            raise ContractError("Base temporal sem cálculo implementado nesta fase.")
        if not isinstance(self.approval, RuleApproval):
            raise ContractError("Regra docente exige registro de aprovação explícito.")
        if self.semantic_variant_id is not None:
            require_text(self.semantic_variant_id)
        for collection in (self.requires_decisions, self.limitations):
            if not isinstance(collection, tuple) or not collection:
                raise ContractError("Regra candidata exige pendências e limites registrados.")
            for item in collection:
                require_text(item)

    @property
    def unit(self) -> MetricUnit:
        """Unidade derivada da população; pessoas e vínculos não se confundem."""
        return _UNIT_BY_BASIS[self.counting_basis]


def _candidate(
    rule_id: str,
    label: str,
    counting_basis: FacultyCountingBasis,
    temporal_basis: TemporalBasis,
    semantic_variant_id: str | None,
    limitations: tuple[str, ...],
) -> FacultyRule:
    return FacultyRule(
        rule_id=rule_id,
        rule_version="faculty-candidate-v1",
        label=label,
        counting_basis=counting_basis,
        temporal_basis=temporal_basis,
        semantic_variant_id=semantic_variant_id,
        requires_decisions=("faculty_source", "faculty_grain", "faculty_formula"),
        limitations=limitations,
        approval=RuleApproval(
            status=ApprovalStatus.PENDING,
            reviewed_on=None,
            evidence_reference=None,
            owner_role="Talita e responsável pela fonte docente",
        ),
    )


#: As quatro candidatas que a conversa com Talita precisa resolver (Q-003).
#: Nenhuma está aprovada; a ordem não expressa preferência institucional.
CANDIDATE_FACULTY_RULES = (
    _candidate(
        "pessoas_foto",
        "Pessoas distintas, foto em uma data",
        FacultyCountingBasis.PEOPLE,
        TemporalBasis.SNAPSHOT,
        "faculty_people_context",
        (
            "A chave de pessoa precisa ser identificador opaco aprovado; não deduplicar por nome.",
            "A data da foto não é presumida pelo código; precisa ser escolhida no recorte.",
        ),
    ),
    _candidate(
        "pessoas_qualquer_mes",
        "Pessoas distintas presentes em qualquer mês do período",
        FacultyCountingBasis.PEOPLE,
        TemporalBasis.ANY_MONTH,
        "faculty_people_context",
        (
            "Presença em qualquer mês não equivale à soma de contagens mensais.",
            "O calendário do período, inclusive o mês de julho, continua sem aprovação.",
        ),
    ),
    _candidate(
        "matriculas_ultima_por_vinculo",
        "Matrículas funcionais na última referência de cada vínculo",
        FacultyCountingBasis.FUNCTIONAL_REGISTRATIONS,
        TemporalBasis.LATEST_PER_ENTITY,
        "faculty_registrations_latest_each",
        (
            "Matrícula funcional não equivale a pessoa distinta.",
            "Desempate entre registros da mesma referência depende de regra aprovada.",
        ),
    ),
    _candidate(
        "matriculas_ultimo_mes_global",
        "Matrículas funcionais no último mês do recorte",
        FacultyCountingBasis.FUNCTIONAL_REGISTRATIONS,
        TemporalBasis.LATEST_IN_SELECTION,
        "faculty_registrations_latest_global",
        (
            "O último mês presente no recorte não comprova a competência corrente.",
            "Vínculos encerrados antes desse mês desaparecem da contagem.",
        ),
    ),
)


def get_candidate_rule(rule_id: str) -> FacultyRule:
    """Lista fechada: a tela não compõe regras livremente."""
    for rule in CANDIDATE_FACULTY_RULES:
        if rule.rule_id == rule_id:
            return rule
    raise ContractError("Regra docente fora da lista fechada de candidatas.")


def rule_blockers(rule: FacultyRule, catalog: AnalysisCatalog) -> tuple[str, ...]:
    """Pendências que impedem apresentar a regra como aprovada.

    Combina o que a própria regra declara faltar com o que o catálogo ainda registra
    como pendente. Não altera status, não aprova e não libera modo real.
    """
    if not isinstance(rule, FacultyRule):
        raise ContractError("Regra docente inválida.")
    definition = catalog.get(AnalysisId.FACULTY)
    pending = set(pending_decisions(definition))
    blockers = [item for item in rule.requires_decisions if item in pending]
    if not rule.approval.approved:
        blockers.append("aprovacao_regra_docente")
    if definition.validation_status != ApprovalStatus.APPROVED:
        blockers.append("aceite_funcional_docente")
    if definition.physical_source_reference is None:
        blockers.append("mapeamento_fisico_docente")
    if (
        rule.semantic_variant_id is not None
        and definition.selected_semantic_variant != rule.semantic_variant_id
    ):
        blockers.append("selecao_variante_docente")
    return tuple(dict.fromkeys(blockers))
