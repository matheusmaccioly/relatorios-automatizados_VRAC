"""Entradas tipadas dos roteiros acadêmicos; valores separados das fontes físicas."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime

from vrac.analyses.faculty_overview import FacultySource

ALL_DEPARTMENTS = "Todos os departamentos"


@dataclass(frozen=True, slots=True)
class HistoryRow:
    department: str
    person_key: str | None
    registration: str | None
    reference_date: date | datetime | None
    cadre: str | None
    category: str | None
    status: str | None
    payroll_batch: str | None
    leave_code: str | None


@dataclass(frozen=True, slots=True)
class WorkloadRow:
    department: str
    registration: str | None
    semester: int
    name: str | None
    cadre: str | None
    category: str | None
    real_hours: float | None
    contracted_hours: float | None


@dataclass(frozen=True, slots=True)
class AllocationRow:
    department: str
    teaching_department: str
    registration: str | None
    semester: int
    discipline: str
    class_id: str
    allocated_hours: float | None
    vacancies_filled: int | None
    shared: str | None
    classification: str | None


@dataclass(frozen=True, slots=True)
class FunctionRow:
    department: str
    distribution_department: str | None
    registration: str | None
    year: int
    month: int
    description: str | None
    role: str | None


@dataclass(frozen=True, slots=True)
class AppointmentRow:
    department: str
    registration: str
    role: str
    start: date | datetime
    end: date | datetime | None
    evidence: str
    administrative: bool


@dataclass(frozen=True, slots=True)
class StudentRow:
    registration: int | None
    department: str
    course: str
    course_name: str
    qualification: str | None
    shift: str | None
    level: str | None
    entry_period: int | None
    period: int | None
    status: str | None
    entry_kind: str | None


@dataclass(frozen=True, slots=True)
class ScholarshipRow:
    registration: int | None
    period: int | None


@dataclass(frozen=True, slots=True)
class SimulationPolicy:
    """Convenções exclusivamente fictícias; nunca são aprovação institucional."""

    real_hours_unit: str | None = None
    contracted_hours_unit: str | None = None
    synthetic_units: bool = False
    synthetic_appointments: bool = False


@dataclass(frozen=True, slots=True)
class AcademicSource:
    department: str
    faculty: FacultySource
    periods: tuple[str, ...]
    history: tuple[HistoryRow, ...] = ()
    workloads: tuple[WorkloadRow, ...] = ()
    allocations: tuple[AllocationRow, ...] = ()
    functions: tuple[FunctionRow, ...] = ()
    appointments: tuple[AppointmentRow, ...] = ()
    students: tuple[StudentRow, ...] = ()
    student_history: tuple[StudentRow, ...] = ()
    scholarships: tuple[ScholarshipRow, ...] = ()
    policy: SimulationPolicy = SimulationPolicy()
    available: frozenset[str] = frozenset()
    errors: tuple[str, ...] = ()

    @property
    def fingerprint(self) -> str:
        payload = asdict(self)
        payload["available"] = sorted(self.available)
        encoded = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
