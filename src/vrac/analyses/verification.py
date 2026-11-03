"""Aprofundamento fechado e experimental, restrito à demonstração local."""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from vrac.analyses.academic import AnalysisFilters
from vrac.authorization import require_data_access
from vrac.settings import DemoSource, Settings

IDENTITY = "desenvolvedor-local-sintetico"
RULE_ID = "E01"
RULE_VERSION = "1"
MAX_DEPARTMENTS = 5
MAX_CHECKS = 1


@dataclass(frozen=True, slots=True)
class Rule:
    identifier: str
    version: str
    required_data: str
    trigger: str
    query: str
    explanation: str
    evidence: str
    limitation: str
    max_cost: str
    experimental: bool


CATALOG = (
    Rule(
        RULE_ID,
        RULE_VERSION,
        "Alocações e snapshot R04",
        "R04 selecionada e E01 habilitada",
        "academic_allocations.sql",
        "Classificação ausente no semestre e departamentos",
        "Contagem de registros de alocação",
        "Não identifica TCC nem avalia produtividade",
        "Uma execução; até 5 departamentos, 5000 alocações, 61 leituras e 5 s por comando",
        True,
    ),
)


class Status(StrEnum):
    SUGGESTED = "Sugerida"
    APPROVED = "Aprovada"
    DECLINED = "Recusada"
    EXECUTED = "Executada"
    FAILED = "Falhou"
    NOT_APPLICABLE = "Não aplicável"


@dataclass(frozen=True, slots=True)
class Context:
    identity: str
    analysis: str
    filters: AnalysisFilters
    department: str
    departments: tuple[str, ...]
    source_arguments: tuple[tuple[str, object], ...]
    reference: str
    rule_version: str = RULE_VERSION


@dataclass(frozen=True, slots=True)
class Outcome:
    status: Status
    reason: str
    evidence: str = ""
    limitation: str = ""


@dataclass(slots=True)
class VerificationSession:
    context: Context | None = None
    outcomes: dict[str, Outcome] = field(default_factory=dict)

    def select(self, context: Context) -> None:
        if self.context != context:
            self.context = context
            self.outcomes.clear()

    def decide(self, approved: bool) -> None:
        if self.context is None:
            raise ValueError("Selecione uma análise antes de autorizar.")
        # Uma decisão concluída não é renovada implicitamente por reruns.
        if RULE_ID not in self.outcomes:
            self.outcomes[RULE_ID] = Outcome(
                Status.APPROVED if approved else Status.DECLINED,
                "Autorização simulada local." if approved else "Consulta recusada.",
            )

    def run(
        self,
        settings: Settings,
        *,
        automatic: bool,
        enabled: frozenset[str],
        applicable: bool,
        query: Callable[[Context], int],
        budget: int = MAX_CHECKS,
    ) -> Outcome:
        require_data_access(settings)
        context = self.context
        if context is None or context.identity != IDENTITY:
            raise PermissionError("Identidade sintética local necessária.")
        previous = self.outcomes.get(RULE_ID)
        if previous and previous.status in {
            Status.DECLINED,
            Status.EXECUTED,
            Status.FAILED,
            Status.NOT_APPLICABLE,
        }:
            return previous
        if (
            not applicable
            or settings.demo_source != DemoSource.POSTGRES
            or context.rule_version != RULE_VERSION
            or not context.reference
            or not context.departments
            or len(context.departments) > MAX_DEPARTMENTS
        ):
            result = Outcome(Status.NOT_APPLICABLE, "Origem, análise ou limite incompatível.")
        elif RULE_ID not in enabled or budget < 1 or budget > MAX_CHECKS:
            result = Outcome(Status.SUGGESTED, "Verificação não habilitada ou limite esgotado.")
        elif not automatic and (previous is None or previous.status != Status.APPROVED):
            result = Outcome(Status.SUGGESTED, "Aguardando autorização para consulta adicional.")
        else:
            try:
                count = query(context)
                if type(count) is not int or count < 0:
                    raise ValueError("Resposta inválida.")
                result = Outcome(
                    Status.EXECUTED,
                    "Classificação ausente em alocações do semestre e departamentos selecionados.",
                    f"{count} registros de alocação sem classificação.",
                    "Experimental: não identifica TCC nem avalia docentes; inclui todas as "
                    "alocações do recorte de departamento e semestre, sem filtro por quadro "
                    "ou categoria.",
                )
            except Exception:
                result = Outcome(
                    Status.FAILED,
                    "Consulta ou referência indisponível; atualize os dados para tentar novamente.",
                )
        # Sugerida não consome a decisão futura.
        if result.status != Status.SUGGESTED:
            self.outcomes[RULE_ID] = result
        return result
