"""Solicitações e resultados lógicos, independentes de Streamlit e banco."""

from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from vrac.settings import DataMode


class ContractError(ValueError):
    """Violação de contrato sem repetir valores externos na mensagem."""


class AnalysisId(StrEnum):
    FACULTY = "composicao_docente"
    ENROLLMENTS = "evolucao_matriculas"
    WORKLOAD = "carga_horaria"


class EntityKind(StrEnum):
    EMPLOYMENT_DEPARTMENT = "departamento_vinculo"
    TEACHING_DEPARTMENT = "departamento_disciplina"
    COURSE_DEPARTMENT = "departamento_curso"
    COURSE = "curso"
    PROGRAM = "programa"
    TEACHER = "docente"
    STUDENT = "aluno"
    EMPLOYMENT = "vinculo"
    EMPLOYMENT_CATEGORY = "categoria_vinculo"
    FUNCTIONAL_REGISTRATION = "matricula_funcional"
    ACADEMIC_REGISTRATION = "matricula_academica"
    HISTORICAL_DEPARTMENT = "departamento_historico"
    DISTRIBUTION_DEPARTMENT = "departamento_distribuicao"
    CADRE = "quadro"
    FUNCTIONAL_CATEGORY = "categoria_funcional"
    STATUS = "situacao"
    SHIFT = "turno"
    QUALIFICATION = "habilitacao"
    ADMISSION_PROCESS = "processo_seletivo"


class TemporalBasis(StrEnum):
    UNDEFINED = "pendente"
    SNAPSHOT = "foto_em_data"
    ANY_MONTH = "presenca_em_qualquer_mes"
    LATEST_PER_ENTITY = "ultima_referencia_por_identificador_no_recorte"
    LATEST_IN_SELECTION = "ultima_referencia_global_no_recorte"
    SELECTED_CONTEXT = "contexto_selecionado"
    CURRENT_REGISTER = "cadastro_atual"
    PERIOD_HISTORY = "situacao_por_periodo"
    FINAL_TRAJECTORY = "populacao_final_trajetoria"


class FacultyCountingBasis(StrEnum):
    PEOPLE = "pessoas_docentes"
    FUNCTIONAL_REGISTRATIONS = "matriculas_funcionais"


class EnrollmentBasis(StrEnum):
    UNDEFINED = "pendente"
    REGISTRATIONS = "registros_matricula"
    UNIQUE_STUDENTS = "alunos_distintos"
    ACADEMIC_REGISTRATIONS = "matriculas_academicas_distintas"


class MetricUnit(StrEnum):
    TEACHERS = "docentes_distintos"
    FUNCTIONAL_REGISTRATIONS = "matriculas_funcionais_distintas"
    ACADEMIC_REGISTRATIONS = "matriculas_academicas_distintas"
    REGISTRATIONS = "matriculas"
    STUDENTS = "alunos_distintos"
    RECORDS = "registros"
    WEEKLY_HOURS = "horas_semanais"
    SEMESTER_HOURS = "horas_semestrais"
    PERCENT = "percentual"


COUNT_UNITS = frozenset(
    {
        MetricUnit.TEACHERS,
        MetricUnit.REGISTRATIONS,
        MetricUnit.STUDENTS,
        MetricUnit.RECORDS,
        MetricUnit.FUNCTIONAL_REGISTRATIONS,
        MetricUnit.ACADEMIC_REGISTRATIONS,
    }
)
HOUR_UNITS = frozenset({MetricUnit.WEEKLY_HOURS, MetricUnit.SEMESTER_HOURS})


class Availability(StrEnum):
    OBSERVED = "observado"
    NULL = "nulo_na_origem"
    NO_ROWS = "sem_registros"
    UNDEFINED = "nao_calculavel"
    ERROR = "falha_na_origem"


class ResultStatus(StrEnum):
    VALID = "valido"
    PARTIAL = "parcial"
    BLOCKED = "bloqueado"


class MetricKind(StrEnum):
    QUANTITY = "quantidade"
    ABSOLUTE_CHANGE = "variacao_absoluta"


def require_text(value: object) -> None:
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        raise ContractError("Identificador ou descrição lógica inválida.")


def require_date(value: object) -> None:
    if type(value) is not date:
        raise ContractError("Informe uma data de referência explícita.")


def require_timestamp(value: datetime | None) -> None:
    if value is not None and (
        not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None
    ):
        raise ContractError("Datas de execução e origem devem conter fuso horário.")


@dataclass(frozen=True, slots=True)
class EntityKey:
    kind: EntityKind
    identifier: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EntityKind):
            raise ContractError("Tipo de entidade lógica inválido.")
        require_text(self.identifier)


@dataclass(frozen=True, slots=True)
class AcademicPeriod:
    identifier: str
    starts_on: date
    ends_on: date
    complete: bool

    def __post_init__(self) -> None:
        require_text(self.identifier)
        require_date(self.starts_on)
        require_date(self.ends_on)
        if self.starts_on > self.ends_on or type(self.complete) is not bool:
            raise ContractError("Período lógico inválido.")


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    analysis_id: AnalysisId
    period: AcademicPeriod
    filters: tuple[EntityKey, ...]
    mode: DataMode = DataMode.SYNTHETIC
    temporal_basis: TemporalBasis = TemporalBasis.UNDEFINED
    snapshot_on: date | None = None
    enrollment_basis: EnrollmentBasis = EnrollmentBasis.UNDEFINED
    faculty_counting_basis: FacultyCountingBasis = FacultyCountingBasis.PEOPLE
    semantic_variant_id: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.analysis_id, AnalysisId)
            or not isinstance(self.period, AcademicPeriod)
            or not isinstance(self.mode, DataMode)
            or not isinstance(self.temporal_basis, TemporalBasis)
            or not isinstance(self.enrollment_basis, EnrollmentBasis)
            or not isinstance(self.faculty_counting_basis, FacultyCountingBasis)
            or not isinstance(self.filters, tuple)
            or not self.filters
            or not all(isinstance(item, EntityKey) for item in self.filters)
            or len(set(self.filters)) != len(self.filters)
        ):
            raise ContractError("Solicitação lógica inválida.")
        if self.semantic_variant_id is not None:
            require_text(self.semantic_variant_id)
        if self.temporal_basis == TemporalBasis.SNAPSHOT:
            require_date(self.snapshot_on)
            if not self.period.starts_on <= self.snapshot_on <= self.period.ends_on:
                raise ContractError("A foto deve pertencer ao período informado.")
        elif self.snapshot_on is not None:
            raise ContractError("Data de foto exige a base temporal correspondente.")


@dataclass(frozen=True, slots=True)
class SourceReference:
    logical_source: str
    version: str
    extracted_at: datetime | None
    updated_at: datetime | None

    def __post_init__(self) -> None:
        require_text(self.logical_source)
        require_text(self.version)
        require_timestamp(self.extracted_at)
        require_timestamp(self.updated_at)


@dataclass(frozen=True, slots=True)
class MetricDatum:
    metric: str
    unit: MetricUnit
    value: int | Decimal | None
    availability: Availability = Availability.OBSERVED
    dimensions: tuple[EntityKey, ...] = ()
    kind: MetricKind = MetricKind.QUANTITY

    def __post_init__(self) -> None:
        require_text(self.metric)
        if (
            not isinstance(self.unit, MetricUnit)
            or not isinstance(self.availability, Availability)
            or not isinstance(self.kind, MetricKind)
        ):
            raise ContractError("Unidade ou situação do dado inválida.")
        if not isinstance(self.dimensions, tuple) or not all(
            isinstance(item, EntityKey) for item in self.dimensions
        ):
            raise ContractError("Dimensões lógicas inválidas.")
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ContractError("Dimensões repetidas não definem uma granularidade válida.")
        if self.availability != Availability.OBSERVED:
            if self.value is not None:
                raise ContractError(
                    "Ausência, nulo, falha e não calculável não podem receber zero."
                )
        elif self.unit in COUNT_UNITS:
            if type(self.value) is not int or (
                self.value < 0 and self.kind != MetricKind.ABSOLUTE_CHANGE
            ):
                raise ContractError("Contagens exigem inteiro não negativo.")
        elif not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise ContractError("Horas e percentuais exigem Decimal finito e explícito.")
        elif self.unit in HOUR_UNITS and self.value < 0 and self.kind != MetricKind.ABSOLUTE_CHANGE:
            raise ContractError("Horas não podem ser negativas neste contrato proposto.")


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    request: AnalysisRequest
    execution_id: str
    created_at: datetime
    status: ResultStatus
    data: tuple[MetricDatum, ...]
    units: tuple[MetricUnit, ...]
    origins: tuple[SourceReference, ...]
    catalog_version: str
    rule_version: str
    query_version: str | None
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.request, AnalysisRequest) or not isinstance(
            self.status, ResultStatus
        ):
            raise ContractError("Resultado lógico inválido.")
        try:
            UUID(self.execution_id)
        except (ValueError, TypeError, AttributeError):
            raise ContractError("Identificador de execução inválido.") from None
        if self.created_at is None:
            raise ContractError("O resultado deve registrar quando foi criado.")
        require_timestamp(self.created_at)
        require_text(self.catalog_version)
        require_text(self.rule_version)
        if self.query_version is not None:
            require_text(self.query_version)
        for values, expected_type in (
            (self.data, MetricDatum),
            (self.units, MetricUnit),
            (self.origins, SourceReference),
        ):
            if not isinstance(values, tuple) or not all(
                isinstance(v, expected_type) for v in values
            ):
                raise ContractError("Coleção de resultado inválida.")
        if not self.units or not self.origins or not isinstance(self.warnings, tuple):
            raise ContractError("Resultado exige unidades, origens e avisos explícitos.")
        for warning in self.warnings:
            require_text(warning)
        if any(item.unit not in self.units for item in self.data):
            raise ContractError("As unidades devem refletir os dados entregues.")
        metric_keys = {(item.metric, item.unit, item.dimensions, item.kind) for item in self.data}
        if len(metric_keys) != len(self.data):
            raise ContractError("Métricas repetidas exigem revisão da granularidade.")
        if len({origin.logical_source for origin in self.origins}) != len(self.origins):
            raise ContractError("Cada origem lógica deve ter uma referência temporal inequívoca.")
        if self.request.mode == DataMode.REAL and self.status != ResultStatus.BLOCKED:
            raise ContractError("Adaptadores reais de análises permanecem bloqueados na fase 2.")
        if self.status == ResultStatus.BLOCKED and (self.data or not self.warnings):
            raise ContractError("Resultado bloqueado exige motivo e não pode conter números.")
        if self.status == ResultStatus.PARTIAL and not self.warnings:
            raise ContractError("Resultado parcial exige explicar a limitação.")
        if self.status == ResultStatus.VALID and (
            not self.data
            or not self.request.period.complete
            or any(item.availability != Availability.OBSERVED for item in self.data)
            or any(source.extracted_at is None for source in self.origins)
        ):
            raise ContractError("Resultado incompleto não pode ser apresentado como válido.")
        if self.data and (
            self.request.analysis_id == AnalysisId.FACULTY
            and self.request.temporal_basis == TemporalBasis.UNDEFINED
            or self.request.analysis_id == AnalysisId.ENROLLMENTS
            and self.request.enrollment_basis == EnrollmentBasis.UNDEFINED
        ):
            raise ContractError(
                "Defina a base temporal ou a unidade de matrícula antes do resultado."
            )
        if self.data:
            allowed = {
                AnalysisId.FACULTY: {
                    MetricUnit.PERCENT,
                    MetricUnit.TEACHERS
                    if self.request.faculty_counting_basis == FacultyCountingBasis.PEOPLE
                    else MetricUnit.FUNCTIONAL_REGISTRATIONS,
                },
                AnalysisId.WORKLOAD: HOUR_UNITS,
                AnalysisId.ENROLLMENTS: {
                    MetricUnit.PERCENT,
                    {
                        EnrollmentBasis.REGISTRATIONS: MetricUnit.REGISTRATIONS,
                        EnrollmentBasis.UNIQUE_STUDENTS: MetricUnit.STUDENTS,
                        EnrollmentBasis.ACADEMIC_REGISTRATIONS: MetricUnit.ACADEMIC_REGISTRATIONS,
                    }.get(self.request.enrollment_basis, MetricUnit.RECORDS),
                },
            }[self.request.analysis_id]
            if any(item.unit not in allowed for item in self.data):
                raise ContractError("Unidade incompatível com o significado solicitado.")

    def to_dict(self) -> dict[str, object]:
        """Decimal vira texto para preservar precisão; datas permanecem por origem."""

        def encode(value: object) -> object:
            if isinstance(value, (datetime, date)):
                return value.isoformat()
            if isinstance(value, Decimal):
                return str(value)
            if isinstance(value, dict):
                return {key: encode(item) for key, item in value.items()}
            if isinstance(value, (tuple, list)):
                return [encode(item) for item in value]
            return value

        payload = asdict(self)
        payload["period"] = asdict(self.request.period)
        payload["effective_filters"] = [asdict(item) for item in self.request.filters]
        payload["synthetic"] = self.request.mode == DataMode.SYNTHETIC
        return encode(payload)
