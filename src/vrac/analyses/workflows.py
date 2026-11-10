"""Contratos dos roteiros propostos: lista fechada, sem cálculo ou acesso a fontes.

As dependências V01–V24 são registros pendentes, nunca aprovações implícitas.
O planejamento de uma métrica não constitui autorização ou implementação dela.
"""

from dataclasses import dataclass
from enum import StrEnum

from vrac.analyses.catalog import AnalysisCatalog, ApprovalStatus, pending_decisions
from vrac.analyses.contracts import (
    AnalysisId,
    AnalysisRequest,
    AnalysisResult,
    Availability,
    ContractError,
    EntityKind,
    MetricUnit,
    ResultStatus,
    TemporalBasis,
    require_text,
)
from vrac.settings import DataMode


class WorkflowId(StrEnum):
    OVERVIEW = "R01"
    QP = "R02"
    HISTORY = "R03"
    WORKLOAD = "R04"
    FUNCTIONS = "R05"
    STUDENTS = "R06"


@dataclass(frozen=True, slots=True)
class WorkflowDecision:
    identifier: str
    question: str
    owner_role: str
    status: ApprovalStatus = ApprovalStatus.PENDING


# Apenas perguntas lógicas: sem objetos físicos, expressões ou códigos dos painéis.
WORKFLOW_DECISIONS = tuple(
    WorkflowDecision(f"V{index:02}", question, owner)
    for index, (question, owner) in enumerate(
        (
            ("Qual identidade, unidade e deduplicação docente?", "Talita + fonte + DBA"),
            ("Qual população geral e elegibilidade de vínculos?", "Talita + fonte"),
            ("Qual definição vigente de QP e tratamento de múltiplos quadros?", "Talita + fonte"),
            ("Foto ou presença no período?", "Talita + fonte"),
            ("Qual calendário e tratamento de competências especiais?", "Talita + fonte + DBA"),
            ("Quais situações e lotes elegíveis no histórico?", "Talita + fonte"),
            ("Como tratar unidade histórica e mudança de classificação?", "Talita + fonte"),
            ("Qual fonte, chave, granularidade e unidade de Horas Reais?", "Talita + fonte + DBA"),
            ("Qual referência e unidade tornam as cargas comparáveis?", "Talita + fontes"),
            (
                "Quais limites e fronteiras do resultado de carga?",
                "Talita + responsável pela regra",
            ),
            ("Qual domínio e vigência de dupla função?", "Talita + fonte"),
            ("Quais papéis administrativos e prova de simultaneidade?", "Talita + fonte"),
            ("Como distinguir lotação, distribuição e registros de função?", "Fonte + DBA"),
            ("Qual identidade e unidade acadêmica?", "Talita + fonte + DBA"),
            ("Quais situações e efeito do cadastro atual sobre o histórico?", "Talita + fonte"),
            ("Qual evento e regra de conclusão?", "Talita + fonte"),
            ("Qual evento de ingresso e tratamento de dupla diplomação?", "Talita + fonte"),
            ("Qual elegibilidade de bolsa e correspondência temporal?", "Talita + fontes"),
            ("Quais cursos, habilitações, turnos e equivalências vigentes?", "Talita + fonte"),
            ("O filtro de processo seletivo propaga às quatro curvas?", "Talita + fonte"),
            ("Qual intervalo efetivo para conciliação acadêmica?", "Talita + Matheus"),
            ("Quais fontes físicas, chaves, cobertura e permissões?", "DBA + Matheus"),
            ("Quais escopos de login, detalhe, cache e exportação?", "DSI + responsável + Matheus"),
            (
                "Quais materiais e aceite visual institucionais?",
                "Matheus + responsável pela identidade",
            ),
        ),
        start=1,
    )
)


@dataclass(frozen=True, slots=True)
class ProposedMetric:
    identifier: str
    decisions: tuple[str, ...]
    logical_sources: tuple[str, ...]
    restriction: str


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    identifier: WorkflowId
    analysis_id: AnalysisId
    title: str
    phase: str
    scope_kinds: tuple[EntityKind, ...]
    optional_filters: tuple[EntityKind, ...]
    temporal_bases: tuple[TemporalBasis, ...]
    metrics: tuple[ProposedMetric, ...]


E = EntityKind
T = TemporalBasis
FACULTY_FILTERS = (E.CADRE, E.FUNCTIONAL_CATEGORY, E.STATUS, E.EMPLOYMENT_CATEGORY)
PHOTO_BASES = (T.SNAPSHOT, T.CURRENT_REGISTER)


def _metric(identifier: str, decisions: str, sources: str, restriction: str) -> ProposedMetric:
    return ProposedMetric(identifier, tuple(decisions.split()), tuple(sources.split()), restriction)


WORKFLOWS = (
    WorkflowDefinition(
        WorkflowId.OVERVIEW,
        AnalysisId.FACULTY,
        "Situação geral do departamento",
        "3",
        (E.EMPLOYMENT_DEPARTMENT,),
        FACULTY_FILTERS,
        PHOTO_BASES,
        (
            _metric(
                "geral",
                "V01 V02 V04",
                "cadastro_docente",
                "Pessoa e matrícula funcional são unidades distintas; não contar linhas.",
            ),
            _metric(
                "por_quadro",
                "V01 V02 V03 V04",
                "cadastro_docente",
                "Categorias podem se sobrepor; ausência de classificação não é zero.",
            ),
            _metric(
                "por_categoria",
                "V01 V02 V04",
                "cadastro_docente",
                "Preservar classificação ausente e multiplicidade de vínculos.",
            ),
        ),
    ),
    WorkflowDefinition(
        WorkflowId.QP,
        AnalysisId.FACULTY,
        "Corpo docente geral e QP",
        "3",
        (E.EMPLOYMENT_DEPARTMENT,),
        (E.FUNCTIONAL_CATEGORY, E.STATUS, E.EMPLOYMENT_CATEGORY),
        PHOTO_BASES,
        (
            _metric(
                "geral",
                "V01 V02 V04",
                "cadastro_docente",
                "O filtro de QP não pode reduzir o denominador geral.",
            ),
            _metric(
                "qp_confirmado",
                "V01 V02 V03 V04",
                "cadastro_docente",
                "QP é subconjunto do geral, com a mesma chave, filtros e referência.",
            ),
            _metric(
                "classificacao_pendente",
                "V01 V02 V03 V04",
                "cadastro_docente",
                "Não classificar ausência como não QP.",
            ),
            _metric(
                "demais",
                "V01 V02 V03 V04",
                "cadastro_docente",
                "Diferença de conjuntos somente com classificação completa.",
            ),
            _metric(
                "participacao_qp",
                "V01 V02 V03 V04",
                "cadastro_docente",
                "Exige cobertura completa e denominador observado maior que zero.",
            ),
        ),
    ),
    WorkflowDefinition(
        WorkflowId.HISTORY,
        AnalysisId.FACULTY,
        "Histórico semestral do departamento",
        "3",
        (E.HISTORICAL_DEPARTMENT,),
        FACULTY_FILTERS,
        (T.ANY_MONTH,),
        (
            _metric(
                "geral_semestral",
                "V01 V02 V04 V05 V06 V07",
                "historico_docente",
                "União de pessoas elegíveis; não somar contagens mensais.",
            ),
            _metric(
                "por_quadro_semestral",
                "V01 V02 V03 V04 V05 V06 V07",
                "historico_docente",
                "Preservar sobreposição e departamento histórico.",
            ),
        ),
    ),
    WorkflowDefinition(
        WorkflowId.WORKLOAD,
        AnalysisId.WORKLOAD,
        "Carga horária dos professores",
        "4b",
        (E.EMPLOYMENT_DEPARTMENT,),
        FACULTY_FILTERS,
        (T.SELECTED_CONTEXT,),
        (
            _metric(
                "horas_reais",
                "V01 V08 V09",
                "horas_reais_oficiais",
                "Fonte dedicada, unidade e chave confirmadas; não somar disciplinas.",
            ),
            _metric(
                "carga_contratada",
                "V01 V09",
                "carga_contratada",
                "Unidade e vigência próprias; não inferir pelo título.",
            ),
            _metric(
                "comparacao_cargas",
                "V01 V08 V09",
                "horas_reais_oficiais carga_contratada",
                "Somente unidades e referências compatíveis, sem conversão presumida.",
            ),
            _metric(
                "indicador_carga",
                "V01 V08 V09 V10",
                "horas_reais_oficiais",
                "Limites dependem de aprovação; não avaliar produtividade.",
            ),
        ),
    ),
    WorkflowDefinition(
        WorkflowId.FUNCTIONS,
        AnalysisId.FACULTY,
        "Dupla função e funções administrativas",
        "encaixe_pendente",
        (E.EMPLOYMENT_DEPARTMENT,),
        FACULTY_FILTERS,
        PHOTO_BASES,
        (
            _metric(
                "dupla_funcao",
                "V01 V02 V04 V11",
                "cadastro_docente",
                "Resultado cadastral não comprova cargo administrativo.",
            ),
            _metric(
                "gratificacao_registrada",
                "V01 V13",
                "registro_funcao",
                "Existência de registro sem valores financeiros; não comprova cargo.",
            ),
            _metric(
                "funcao_administrativa_confirmada",
                "V01 V11 V12 V13",
                "registro_funcao",
                "Requer papel, vigência e prova de simultaneidade; sem valores financeiros.",
            ),
        ),
    ),
    WorkflowDefinition(
        WorkflowId.STUDENTS,
        AnalysisId.ENROLLMENTS,
        "Evolução de alunos",
        "4a",
        (E.COURSE, E.PROGRAM, E.COURSE_DEPARTMENT),
        (E.STATUS, E.SHIFT, E.QUALIFICATION),
        (T.PERIOD_HISTORY,),
        (
            _metric(
                "matriculados",
                "V14 V15 V19 V21",
                "historico_academico",
                "Unidade acadêmica explícita; não somar estoques de períodos.",
            ),
            _metric(
                "bolsistas_matriculados",
                "V05 V14 V15 V18 V19 V21",
                "historico_academico elegibilidade_bolsa",
                "Subconjunto compatível; bolsas repetidas não multiplicam matrículas.",
            ),
            _metric(
                "formados",
                "V14 V16 V19 V21",
                "conclusao_academica",
                "Regra de conclusão própria; não inferir evasão.",
            ),
            _metric(
                "ingressantes",
                "V14 V17 V19 V21",
                "ingresso_academico",
                "Regra de ingresso própria; não somar ao estoque.",
            ),
        ),
    ),
)


def get_workflow(identifier: WorkflowId) -> WorkflowDefinition:
    if not isinstance(identifier, WorkflowId):
        raise ContractError("Roteiro fora da lista fechada.")
    return next(item for item in WORKFLOWS if item.identifier == identifier)


@dataclass(frozen=True, slots=True)
class WorkflowRequest:
    workflow_id: WorkflowId
    points: tuple[AnalysisRequest, ...]
    metric_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        definition = get_workflow(self.workflow_id)
        if (
            not isinstance(self.points, tuple)
            or not self.points
            or not all(isinstance(p, AnalysisRequest) for p in self.points)
            or not isinstance(self.metric_ids, tuple)
            or not self.metric_ids
            or not all(isinstance(m, str) for m in self.metric_ids)
            or len(set(self.metric_ids)) != len(self.metric_ids)
            or not set(self.metric_ids) <= {m.identifier for m in definition.metrics}
        ):
            raise ContractError("Pontos ou métricas do roteiro inválidos.")
        first = self.points[0]
        for point in self.points:
            if (
                point.analysis_id != definition.analysis_id
                or point.temporal_basis not in definition.temporal_bases
                or not any(f.kind in definition.scope_kinds for f in point.filters)
                or any(
                    f.kind not in (*definition.scope_kinds, *definition.optional_filters)
                    for f in point.filters
                )
                or point.mode != first.mode
                or set(point.filters) != set(first.filters)
                or point.temporal_basis != first.temporal_basis
                or point.faculty_counting_basis != first.faculty_counting_basis
                or point.enrollment_basis != first.enrollment_basis
                or point.semantic_variant_id != first.semantic_variant_id
            ):
                raise ContractError("Recorte, unidade ou referência incompatíveis com o roteiro.")
        if len({p.period.identifier for p in self.points}) != len(self.points):
            raise ContractError("Referência de período repetida na série.")
        ordered = sorted(self.points, key=lambda p: p.period.starts_on)
        if any(
            a.period.ends_on >= b.period.starts_on
            for a, b in zip(ordered, ordered[1:], strict=False)
        ):
            raise ContractError("Os pontos da série não podem sobrepor períodos.")
        if self.workflow_id in {WorkflowId.OVERVIEW, WorkflowId.QP, WorkflowId.FUNCTIONS}:
            if len(self.points) != 1:
                raise ContractError("O roteiro de foto exige uma única referência.")


@dataclass(frozen=True, slots=True)
class MetricPlan:
    metric_id: str
    pending_decisions: tuple[str, ...]
    logical_sources: tuple[str, ...]
    restriction: str
    execution_blockers: tuple[str, ...]


def plan_workflow(request: WorkflowRequest) -> tuple[MetricPlan, ...]:
    """Expõe dependências por métrica; não recebe aprovações nem executa análise."""
    if not isinstance(request, WorkflowRequest):
        raise ContractError("Solicitação de roteiro inválida.")
    definition = get_workflow(request.workflow_id)
    return tuple(
        MetricPlan(
            m.identifier,
            m.decisions,
            m.logical_sources,
            m.restriction,
            ("adaptador_nao_implementado", "V22", "V23")
            if request.points[0].mode == DataMode.REAL
            else ("adaptador_nao_implementado",),
        )
        for m in definition.metrics
        if m.identifier in request.metric_ids
    )


@dataclass(frozen=True, slots=True)
class MetricResult:
    metric_id: str
    result: AnalysisResult

    def __post_init__(self) -> None:
        if not isinstance(self.result, AnalysisResult) or not isinstance(self.metric_id, str):
            raise ContractError("Resultado de métrica inválido.")
        if any(d.metric != self.metric_id for d in self.result.data):
            raise ContractError("Resultado contém outra métrica.")


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    """Um resultado por métrica e período permite bloqueios independentes.

    Preserva os metadados e os estados de célula do contrato existente. Não autoriza
    números reais, detalhes pessoais ou agregação genérica de estoques temporais.
    """

    request: WorkflowRequest
    results: tuple[MetricResult, ...]
    app_version: str
    template_version: str

    def __post_init__(self) -> None:
        require_text(self.app_version)
        require_text(self.template_version)
        if not isinstance(self.request, WorkflowRequest) or not isinstance(self.results, tuple):
            raise ContractError("Resultado de roteiro inválido.")
        expected = {
            (p.period.identifier, m) for p in self.request.points for m in self.request.metric_ids
        }
        seen = set()
        for item in self.results:
            if not isinstance(item, MetricResult):
                raise ContractError("Resultado de métrica inválido.")
            result = item.result
            if result.request not in self.request.points:
                raise ContractError("Resultado pertence a outro recorte.")
            key = (result.request.period.identifier, item.metric_id)
            if key not in expected or key in seen:
                raise ContractError("Métrica ausente da solicitação ou repetida.")
            seen.add(key)
        if seen != expected:
            raise ContractError("Cada métrica solicitada exige estado explícito por período.")
        for item in self.results:
            for datum in item.result.data:
                if datum.unit == MetricUnit.PERCENT:
                    if item.metric_id != "participacao_qp":
                        raise ContractError("Percentual incompatível com a métrica do roteiro.")
                    if datum.availability == Availability.OBSERVED:
                        values = {
                            i.metric_id: i.result
                            for i in self.results
                            if i.result.request == item.result.request
                        }
                        for key in ("geral", "qp_confirmado", "classificacao_pendente"):
                            value = values.get(key)
                            if (
                                value is None
                                or value.status != ResultStatus.VALID
                                or len(value.data) != 1
                            ):
                                raise ContractError("Participação exige base e cobertura válidas.")
                        general = values["geral"].data[0]
                        qp = values["qp_confirmado"].data[0]
                        unknown = values["classificacao_pendente"].data[0]
                        if (
                            general.unit != qp.unit
                            or general.unit != unknown.unit
                            or general.value <= 0
                            or unknown.value != 0
                            or qp.value > general.value
                            or not 0 <= datum.value <= 100
                        ):
                            raise ContractError(
                                "Participação exige base positiva e classificação completa."
                            )

    @property
    def status(self) -> ResultStatus:
        statuses = {item.result.status for item in self.results}
        if statuses == {ResultStatus.BLOCKED}:
            return ResultStatus.BLOCKED
        if statuses == {ResultStatus.VALID}:
            return ResultStatus.VALID
        return ResultStatus.PARTIAL

    def to_dict(self) -> dict[str, object]:
        return {
            "workflow_id": self.request.workflow_id.value,
            "app_version": self.app_version,
            "template_version": self.template_version,
            "status": self.status.value,
            "synthetic": self.request.points[0].mode == DataMode.SYNTHETIC,
            "results": [
                {"metric_id": item.metric_id, "result": item.result.to_dict()}
                for item in self.results
            ],
        }


def phase3_blockers(catalog: AnalysisCatalog, *, mode: DataMode = DataMode.REAL) -> tuple[str, ...]:
    """Pendências documentais institucionais; D-028 permite o incremento sintético.

    Não confere disponibilidade do PostgreSQL nem substitui autorização de acesso.
    O padrão real preserva os bloqueios do contrato anterior.
    """
    if not isinstance(mode, DataMode):
        raise ContractError("Modo de dados inválido.")
    if mode == DataMode.SYNTHETIC:
        return ()
    definition = catalog.get(AnalysisId.FACULTY)
    blockers = list(pending_decisions(definition))
    if definition.validation_status != ApprovalStatus.APPROVED:
        blockers.append("aceite_funcional_docente")
    if definition.physical_source_reference is None:
        blockers.append("mapeamento_fisico_docente")
    if definition.selected_semantic_variant is None:
        blockers.append("selecao_variante_docente")
    return tuple(blockers)
