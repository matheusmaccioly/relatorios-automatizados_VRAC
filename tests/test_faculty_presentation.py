"""A lista docente mantém os valores da R01 ao reproduzir as duas referências."""

from dataclasses import replace

from vrac.analyses.faculty_overview import OverviewFilters, compute_overview
from vrac.analyses.faculty_overview_fixture import load_fixture
from vrac.faculty_presentation import _detail_frames


def test_faculty_lists_sort_names_without_losing_duplicate_rows_or_source_states() -> None:
    overview = compute_overview(load_fixture("SINT-A"), OverviewFilters())
    first, second, *others = overview.detail
    detail = (
        replace(first, name="Zélia fictícia"),
        replace(second, name="Ana fictícia"),
        replace(second, name="Ana fictícia"),
        *others,
    )
    general, workload = _detail_frames(replace(overview, detail=detail))
    assert len(general) == len(workload) == len(detail)
    assert list(general.columns) == [
        "Departamento",
        "Matrícula fictícia",
        "Nome fictício",
        "Quadro",
        "Categoria funcional",
    ]
    assert general["Nome fictício"].tolist()[:2] == ["Ana fictícia", "Ana fictícia"]
    assert general.iloc[-1]["Nome fictício"] == "Zélia fictícia"
    assert workload.iloc[0]["Horas Reais (semestre atual)"] == "0"
    assert workload.iloc[0]["CH contratada"] == "20"
    assert workload.iloc[0]["Indicador de carga (regra do painel)"] == "Sem alocação (CH = 0)"
    assert list(workload.columns)[:9] == [
        "Semestre das Horas Reais",
        "Departamento",
        "Matrícula fictícia",
        "Nome fictício",
        "Quadro",
        "Categoria funcional",
        "Indicador de carga (regra do painel)",
        "Horas Reais (semestre atual)",
        "CH contratada",
    ]
    states = workload.set_index("Matrícula fictícia")
    assert states.loc["880000004", "Horas Reais (semestre atual)"] == "ausente"
    assert states.loc["880000004", "Estado das Horas Reais"] == "Nulo na fonte"
    assert states.loc["880000005", "Horas Reais (semestre atual)"] == "ausente"
    assert states.loc["880000005", "Estado das Horas Reais"] == "Sem registro"


def test_empty_faculty_lists_retain_the_column_contract() -> None:
    overview = compute_overview(load_fixture("SINT-VAZIO"), OverviewFilters())
    general, workload = _detail_frames(overview)
    assert general.empty and workload.empty
    assert "Matrícula fictícia" in general
    assert "Estado das Horas Reais" in workload
