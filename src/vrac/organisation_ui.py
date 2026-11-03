"""Seletores dependentes de Centro e Departamento, compartilhados pelas análises."""

from dataclasses import dataclass

import streamlit as st

from vrac.analyses.academic_data import ALL_DEPARTMENTS
from vrac.department_hierarchy import ALL_CENTERS, DepartmentHierarchy


@dataclass(frozen=True, slots=True)
class OrganisationScope:
    center: str
    department: str
    departments: tuple[str, ...]

    @property
    def label(self) -> str:
        return (
            self.department if self.center == ALL_CENTERS else f"{self.center} · {self.department}"
        )

    @property
    def source_arguments(self) -> dict:
        if self.center == ALL_CENTERS:
            return {"department": self.department}
        return {"department": self.label, "departments": self.departments}


def organisation_filters(
    hierarchy: DepartmentHierarchy, *, prefix: str, department_label: str = "Departamento"
) -> OrganisationScope:
    center_key, department_key = f"{prefix}_center", f"{prefix}_department"
    centers = (ALL_CENTERS, *hierarchy.centers)
    if st.session_state.get(center_key, ALL_CENTERS) not in centers:
        st.session_state[center_key] = ALL_CENTERS
    first, second = st.columns(2)
    with first:
        center = st.selectbox("Centro", centers, key=center_key)
    available = hierarchy.departments_for(center)
    departments = (*available, ALL_DEPARTMENTS)
    if st.session_state.get(department_key, departments[0]) not in departments:
        st.session_state[department_key] = departments[0]
    with second:
        department = st.selectbox(department_label, departments, key=department_key)
    st.caption(hierarchy.note)
    selected = available if department == ALL_DEPARTMENTS else (department,)
    return OrganisationScope(center, department, selected)
