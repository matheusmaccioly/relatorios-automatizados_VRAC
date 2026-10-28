"""Plano de identidade das séries; não agrega matrículas nem infere equivalências."""

from dataclasses import dataclass
from datetime import date

from vrac.analyses.catalog import ApprovalStatus
from vrac.analyses.contracts import (
    AcademicPeriod,
    ContractError,
    EntityKey,
    EntityKind,
    require_date,
    require_text,
)
from vrac.settings import DataMode


@dataclass(frozen=True, slots=True)
class CourseEquivalence:
    source_course: EntityKey
    target_course: EntityKey
    valid_from: date
    valid_until: date
    source_reference: str
    source_version: str
    approval_status: ApprovalStatus
    synthetic: bool
    reviewer_role: str | None = None
    reviewed_on: date | None = None
    evidence_reference: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.source_course, EntityKey)
            or not isinstance(self.target_course, EntityKey)
            or self.source_course.kind != EntityKind.COURSE
            or self.target_course.kind != EntityKind.COURSE
            or self.source_course == self.target_course
            or not isinstance(self.approval_status, ApprovalStatus)
            or type(self.synthetic) is not bool
        ):
            raise ContractError("Equivalência de curso inválida.")
        require_date(self.valid_from)
        require_date(self.valid_until)
        require_text(self.source_reference)
        require_text(self.source_version)
        if self.valid_from > self.valid_until:
            raise ContractError("Vigência da equivalência inválida.")
        if self.approval_status == ApprovalStatus.APPROVED:
            require_text(self.reviewer_role)
            require_date(self.reviewed_on)
            require_text(self.evidence_reference)


@dataclass(frozen=True, slots=True)
class CourseSeriesIdentity:
    original_course: EntityKey
    series_course: EntityKey
    combined: bool
    warnings: tuple[str, ...]


def resolve_course_series(
    course: EntityKey,
    period: AcademicPeriod,
    equivalences: tuple[CourseEquivalence, ...] = (),
    *,
    mode: DataMode = DataMode.SYNTHETIC,
) -> CourseSeriesIdentity:
    if not isinstance(course, EntityKey) or course.kind != EntityKind.COURSE:
        raise ContractError("Curso e programa não são entidades equivalentes.")
    if not isinstance(period, AcademicPeriod) or not isinstance(mode, DataMode):
        raise ContractError("Recorte da série inválido.")
    if not isinstance(equivalences, tuple) or not all(
        isinstance(e, CourseEquivalence) for e in equivalences
    ):
        raise ContractError("Mapa de equivalências inválido.")
    overlapping = [
        item
        for item in equivalences
        if item.source_course == course
        and item.approval_status == ApprovalStatus.APPROVED
        and item.synthetic == (mode == DataMode.SYNTHETIC)
        and item.valid_from <= period.ends_on
        and item.valid_until >= period.starts_on
    ]
    if len(overlapping) != 1 or not (
        overlapping[0].valid_from
        <= period.starts_on
        <= period.ends_on
        <= overlapping[0].valid_until
    ):
        return CourseSeriesIdentity(
            course,
            course,
            False,
            (
                "Séries separadas: equivalência aprovada, inequívoca e vigente "
                "em todo o período não disponível.",
            ),
        )
    target = overlapping[0].target_course
    if any(item.source_course == target for item in equivalences):
        return CourseSeriesIdentity(
            course,
            course,
            False,
            ("Cadeia ou ciclo de equivalências exige revisão, sem fusão automática.",),
        )
    return CourseSeriesIdentity(course, target, True, ())
