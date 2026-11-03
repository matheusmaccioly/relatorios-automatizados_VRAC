"""Hierarquia explícita de filtros, sem inferir relações institucionais."""

from dataclasses import dataclass

from vrac.analyses.academic_data import ALL_DEPARTMENTS

ALL_CENTERS = "Todos os centros"
UNKNOWN_CENTER = "Centro não informado"


@dataclass(frozen=True, slots=True)
class DepartmentRelation:
    center: str
    department: str


@dataclass(frozen=True, slots=True)
class DepartmentHierarchy:
    relations: tuple[DepartmentRelation, ...]
    source: str
    note: str

    def __post_init__(self) -> None:
        departments = [row.department for row in self.relations]
        if (
            not departments
            or len(set(departments)) != len(departments)
            or any(not row.center.strip() or not row.department.strip() for row in self.relations)
        ):
            raise ValueError("A hierarquia deve ter um único centro por departamento disponível.")

    @property
    def centers(self) -> tuple[str, ...]:
        return tuple(sorted({row.center for row in self.relations}))

    def departments_for(self, center: str) -> tuple[str, ...]:
        if center not in (*self.centers, ALL_CENTERS):
            raise ValueError("Selecione um centro disponível na demonstração.")
        return tuple(
            sorted(
                row.department
                for row in self.relations
                if center == ALL_CENTERS or row.center == center
            )
        )


def hierarchy_for_departments(
    departments: tuple[str, ...], *, source: str, synthetic_centers: bool = False
) -> DepartmentHierarchy:
    """Só a fixture pública tem centros simulados; fonte sem relação conserva a lacuna."""
    fixture_centers = {
        "SINT-A": "Centro sintético 1",
        "SINT-VAZIO": "Centro sintético 1",
        "SINT-B": "Centro sintético 2",
    }
    return DepartmentHierarchy(
        tuple(
            DepartmentRelation(
                fixture_centers.get(department, UNKNOWN_CENTER)
                if synthetic_centers
                else UNKNOWN_CENTER,
                department,
            )
            for department in departments
        ),
        source,
        (
            "Centros fictícios, usados somente para demonstrar a hierarquia Centro > Departamento."
            if synthetic_centers
            else "A origem sintética não fornece a relação Centro > Departamento. "
            "O mapeamento de centros está pendente; departamentos permanecem identificados."
        ),
    )


def resolve_departments(
    available: tuple[str, ...], department: str, departments: tuple[str, ...] | None
) -> tuple[str, ...]:
    """Validar o recorte antes das consultas; rótulos de conjunto não são parâmetros SQL."""
    selected = (
        (available if department == ALL_DEPARTMENTS else (department,))
        if departments is None
        else departments
    )
    if (
        not selected
        or any(value not in available for value in selected)
        or len(set(selected)) != len(selected)
        or not department.strip()
    ):
        raise ValueError("Selecione departamentos disponíveis na demonstração.")
    return selected
