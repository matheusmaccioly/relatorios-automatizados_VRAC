"""Cenários fictícios para testar a fundação; não definem resultados institucionais."""

from dataclasses import dataclass
from datetime import datetime
from random import Random

from vrac.authorization import require_data_access
from vrac.settings import Settings

DEPARTMENTS = ("SINT-A", "SINT-B")
PERIODS = ("2025.2", "2026.1", "2026.2")
SYNTHETIC_SEED = 21
DATASET_VERSION = "synthetic-v1"


@dataclass(frozen=True)
class FacultyRecord:
    department: str
    period: str
    reference_month: str
    teacher_id: str
    contract_id: str
    employment_type: str
    real_hours: float | None


@dataclass(frozen=True)
class TeachingAllocation:
    department: str
    teaching_department: str
    period: str
    teacher_id: str
    class_id: str
    curriculum_id: str | None
    sharing_id: str | None
    allocated_hours: float | None
    students: int | None
    classification: str | None


@dataclass(frozen=True)
class SyntheticDataset:
    faculty: tuple[FacultyRecord, ...]
    allocations: tuple[TeachingAllocation, ...]
    version: str = DATASET_VERSION
    synthetic: bool = True
    source: str = "Memória"
    loaded_at: datetime | None = None


def load_demo_data(settings: Settings, *, seed: int = SYNTHETIC_SEED) -> SyntheticDataset:
    """Autorizar antes de criar fixtures. Modo real nunca recebe dados fictícios."""
    require_data_access(settings)
    rng = Random(seed)
    faculty = [
        FacultyRecord("SINT-A", "2026.1", "2026-03", "SYN-DOC-001", "V01", "Tipo A", 4.0),
        FacultyRecord("SINT-A", "2026.1", "2026-04", "SYN-DOC-001", "V01", "Tipo A", 4.0),
        FacultyRecord("SINT-A", "2026.1", "2026-03", "SYN-DOC-001", "V02", "Tipo B", None),
        FacultyRecord("SINT-A", "2026.1", "2026-03", "SYN-DOC-002", "V03", "Tipo B", 0.0),
        FacultyRecord("SINT-B", "2026.1", "2026-03", "SYN-DOC-003", "V04", "Tipo A", 6.0),
        FacultyRecord("SINT-A", "2025.2", "2025-09", "SYN-DOC-001", "V01", "Tipo A", 4.0),
    ]
    allocations = [
        TeachingAllocation(
            "SINT-A",
            "SINT-A",
            "2026.1",
            "SYN-DOC-001",
            "SYN-T01",
            "C01",
            "SH01",
            4.0,
            12,
            "Regular sintética",
        ),
        TeachingAllocation(
            "SINT-A",
            "SINT-A",
            "2026.1",
            "SYN-DOC-001",
            "SYN-T01",
            "C02",
            "SH01",
            4.0,
            12,
            "Regular sintética",
        ),
        TeachingAllocation(
            "SINT-A",
            "SINT-B",
            "2026.1",
            "SYN-DOC-001",
            "SYN-T02",
            "C03",
            None,
            2.0,
            0,
            None,
        ),
        TeachingAllocation(
            "SINT-B",
            "SINT-B",
            "2026.1",
            "SYN-DOC-003",
            "SYN-T03",
            "C04",
            None,
            6.0,
            None,
            None,
        ),
    ]
    rng.shuffle(faculty)
    rng.shuffle(allocations)
    return SyntheticDataset(faculty=tuple(faculty), allocations=tuple(allocations))


def select_demo_data(data: SyntheticDataset, *, department: str, period: str) -> SyntheticDataset:
    """Selecionar um cenário fechado sem agregar, deduplicar ou calcular métricas."""
    if department not in DEPARTMENTS or period not in PERIODS:
        raise ValueError("Selecione um departamento e período da demonstração.")
    return SyntheticDataset(
        faculty=tuple(
            row for row in data.faculty if row.department == department and row.period == period
        ),
        allocations=tuple(
            row for row in data.allocations if row.department == department and row.period == period
        ),
    )
