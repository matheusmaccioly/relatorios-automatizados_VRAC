"""Exemplos fixos de contratos, sem cálculo ou validação de resultado institucional."""

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from decimal import Decimal

from vrac.analyses.catalog import ApprovalStatus
from vrac.analyses.contracts import (
    AcademicPeriod,
    AnalysisId,
    AnalysisRequest,
    Availability,
    EnrollmentBasis,
    EntityKey,
    EntityKind,
    MetricDatum,
    MetricUnit,
    SourceReference,
    TemporalBasis,
)
from vrac.analyses.references import ReferenceCase


@dataclass(frozen=True, slots=True)
class SyntheticObservation:
    entity: EntityKey
    observed_on: date
    value: int | Decimal | None


@dataclass(frozen=True, slots=True)
class SyntheticCase:
    identifier: str
    description: str
    observations: tuple[SyntheticObservation, ...]
    reference: ReferenceCase
    limitations: tuple[str, ...]
    synthetic: bool = True


def synthetic_contract_cases() -> tuple[SyntheticCase, ...]:
    """Quantidades abaixo são expectativas de fixtures, não resultados aprovados."""
    period = AcademicPeriod("SYN-2026.1", date(2026, 1, 10), date(2026, 6, 20), True)
    department = EntityKey(EntityKind.EMPLOYMENT_DEPARTMENT, "SYN-DEP-A")
    teacher = EntityKey(EntityKind.TEACHER, "SYN-DOC-001")
    other_teacher = EntityKey(EntityKind.TEACHER, "SYN-DOC-002")
    faculty = AnalysisRequest(
        AnalysisId.FACULTY, period, (department,), temporal_basis=TemporalBasis.ANY_MONTH
    )
    course = EntityKey(EntityKind.COURSE, "SYN-CURSO-001")
    enrollments = AnalysisRequest(
        AnalysisId.ENROLLMENTS, period, (course,), enrollment_basis=EnrollmentBasis.REGISTRATIONS
    )
    workload = AnalysisRequest(AnalysisId.WORKLOAD, period, (department,))
    origin = SourceReference(
        "synthetic.logical_source",
        "fixture-v1",
        datetime(2026, 7, 2, 12, tzinfo=UTC),
        datetime(2026, 6, 30, 9, tzinfo=UTC),
    )
    second_origin = SourceReference(
        "synthetic.second_source",
        "fixture-v1",
        datetime(2026, 7, 3, 12, tzinfo=UTC),
        datetime(2026, 6, 28, 9, tzinfo=UTC),
    )

    def reference(identifier, request, expected, origins=(origin,)):
        return ReferenceCase(
            identifier=identifier,
            request=request,
            rule_version="fixture-rule-v1",
            origins=origins,
            expected=expected,
            validation_status=ApprovalStatus.PENDING,
            synthetic=True,
        )

    cases = (
        SyntheticCase(
            "duplicate_records",
            "Pessoa repetida em meses diferentes não é nova pessoa.",
            (
                SyntheticObservation(teacher, date(2026, 2, 1), 1),
                SyntheticObservation(teacher, date(2026, 3, 1), 1),
                SyntheticObservation(other_teacher, date(2026, 3, 1), 1),
            ),
            reference(
                "synthetic-duplicate", faculty, (MetricDatum("total", MetricUnit.TEACHERS, 2),)
            ),
            ("Expectativa sob a alternativa presença em qualquer mês; não soma mensal.",),
        ),
        SyntheticCase(
            "null_value",
            "Valor nulo tem estado próprio e não é zero.",
            (SyntheticObservation(teacher, date(2026, 3, 1), None),),
            reference(
                "synthetic-null",
                workload,
                (MetricDatum("horas_reais", MetricUnit.WEEKLY_HOURS, None, Availability.NULL),),
            ),
            ("Fonte e unidade são inteiramente fictícias.",),
        ),
        SyntheticCase(
            "observed_zero",
            "Zero observado é valor numérico válido.",
            (SyntheticObservation(teacher, date(2026, 3, 1), Decimal("0")),),
            reference(
                "synthetic-zero",
                workload,
                (MetricDatum("horas_reais", MetricUnit.WEEKLY_HOURS, Decimal("0")),),
            ),
            ("Não confundir com ausência de registros.",),
        ),
        SyntheticCase(
            "no_rows",
            "Fonte sem linhas não produz contagem zero automaticamente.",
            (),
            reference(
                "synthetic-empty",
                faculty,
                (MetricDatum("total", MetricUnit.TEACHERS, None, Availability.NO_ROWS),),
            ),
            ("Recorte sem dados; nenhuma interpretação institucional inferida.",),
        ),
        SyntheticCase(
            "partial_period",
            "Semestre incompleto exige identificação explícita.",
            (),
            reference(
                "synthetic-partial",
                replace(faculty, period=replace(period, complete=False)),
                (MetricDatum("total", MetricUnit.TEACHERS, 1),),
            ),
            ("Não comparar com semestre completo como se a cobertura fosse idêntica.",),
        ),
        SyntheticCase(
            "zero_denominator",
            "Base zero mantém percentual não calculável.",
            (
                SyntheticObservation(course, period.starts_on, 0),
                SyntheticObservation(course, period.ends_on, 5),
            ),
            reference(
                "synthetic-zero-base",
                enrollments,
                (
                    MetricDatum(
                        "variacao_percentual", MetricUnit.PERCENT, None, Availability.UNDEFINED
                    ),
                ),
            ),
            ("Nenhuma divisão ou cálculo percentual é executado por esta fixture.",),
        ),
        SyntheticCase(
            "distinct_source_dates",
            "Extração e atualização são separadas por origem.",
            (),
            reference(
                "synthetic-dates",
                workload,
                (MetricDatum("horas_reais", MetricUnit.WEEKLY_HOURS, Decimal("4")),),
                (origin, second_origin),
            ),
            ("Não usar data da consulta como data de atualização institucional.",),
        ),
    )
    return cases
