"""Leitura agregada da Análise Geral; eventos individuais não chegam à interface."""

import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from vrac.analyses.academic import (
    AnalysisFilters,
    AnalysisKind,
    CalculatedAnalysis,
    ChartSpec,
    ResultTable,
)
from vrac.demo_data import DemoDataError
from vrac.provenance import INSTITUTIONAL_SOURCE
from vrac.settings import DataMode
from vrac.supabase_auth import current_session

FILTERS = {
    "sigla_centro": "Centro",
    "nivel": "Nível",
    "subnivel": "Subnível",
    "curso_codigo": "Código do curso",
    "curso": "Curso",
    "habilitacao_codigo": "Código da habilitação",
    "habilitacao": "Habilitação",
    "turno": "Turno",
    "forma_ingresso": "Forma de ingresso",
    "situacao_atual": "Situação atual",
}
SERIES = {
    "MATRICULADOS": "Matriculados",
    "BOLSISTAS_MATRICULADOS": "Bolsistas matriculados",
    "FORMADOS": "Formados",
    "INGRESSANTES": "Ingressantes",
}


def period_label(value: int) -> str:
    return f"{value // 10}.{value % 10}"


def periods(start: int, end: int) -> tuple[int, ...]:
    if (
        type(start) is not int
        or type(end) is not int
        or start > end
        or start % 10 not in (1, 2)
        or end % 10 not in (1, 2)
        or not 10001 <= start <= end <= 99992
        or end - start > 1000
    ):
        raise ValueError("Intervalo inválido.")
    return tuple(
        y * 10 + s
        for y in range(start // 10, end // 10 + 1)
        for s in (1, 2)
        if start <= y * 10 + s <= end
    )


@dataclass(frozen=True)
class StudentOptions:
    batch: str
    departments: tuple[str, ...]
    start: int
    end: int


def _rpc(name: str, params: dict | None = None) -> dict:
    try:
        session = current_session()
        if session.data_mode != DataMode.PSEUDONYMIZED:
            raise ValueError
        data = session.client.rpc(name, params or {}).execute().data
        if (
            not isinstance(data, dict)
            or data.get("synthetic") is not False
            or data.get("origin") != "institucional_pseudonimizada"
        ):
            raise ValueError
        return data
    except Exception:
        raise DemoDataError(
            "Dados de alunos indisponíveis. Valide sua sessão e tente novamente."
        ) from None


def load_options() -> StudentOptions:
    try:
        data = _rpc("vrac_alunos_options")
        batch = str(UUID(data["batch"]))
        departments = data["departments"]
        if (
            not isinstance(departments, list)
            or not departments
            or len(set(departments)) != len(departments)
            or not set(departments) <= {"ADM", "ECO", "EDU", "ELE", "FIL", "IND", "INF"}
        ):
            raise ValueError
        periods(data["start"], data["end"])
        return StudentOptions(batch, tuple(departments), data["start"], data["end"])
    except Exception:
        raise DemoDataError("Nenhum lote de alunos disponível para seu acesso.") from None


def _scope(options: StudentOptions, departments: tuple[str, ...]) -> dict:
    if not departments or not set(departments) <= set(options.departments):
        raise DemoDataError("Selecione departamentos autorizados para alunos.")
    return {"p_carga": options.batch, "p_departamentos": list(departments)}


def load_filters(options: StudentOptions, departments: tuple[str, ...]) -> dict[str, tuple]:
    data = _rpc("vrac_alunos_filters", _scope(options, departments))
    try:
        values = data["filters"]
        if data["batch"] != options.batch or set(values) != set(FILTERS):
            raise ValueError
        if any(
            not isinstance(v, list) or any(x is not None and not isinstance(x, str) for x in v)
            for v in values.values()
        ):
            raise ValueError
        return {key: tuple(values[key]) for key in FILTERS}
    except Exception:
        raise DemoDataError("Filtros de alunos indisponíveis ou incompatíveis.") from None


def calculate(
    options: StudentOptions,
    departments: tuple[str, ...],
    start: int,
    end: int,
    filters: dict[str, list[str | None]],
) -> CalculatedAnalysis:
    axis = periods(start, end)
    if not options.start <= start <= end <= options.end or not set(filters) <= set(FILTERS):
        raise DemoDataError("Recorte de alunos inválido.")
    if any(
        not isinstance(v, list)
        or not v
        or len(v) > 1000
        or any(x is not None and not isinstance(x, str) for x in v)
        for v in filters.values()
    ):
        raise DemoDataError("Filtros de alunos inválidos.")
    params = _scope(options, departments) | {"p_inicio": start, "p_fim": end, "p_filtros": filters}
    data = _rpc("vrac_alunos_geral", params)
    try:
        if data["batch"] != options.batch or data["unit"] != "matriculas_distintas":
            raise ValueError
        lookup = {}
        for row in data["rows"]:
            key = row["periodo_eixo"], row["indicador"]
            if (
                key in lookup
                or key[0] not in axis
                or key[1] not in SERIES
                or type(row["quantidade"]) is not int
                or row["quantidade"] < 0
            ):
                raise ValueError
            lookup[key] = row["quantidade"]
    except Exception:
        raise DemoDataError("Resultados de alunos incompatíveis; cálculo descartado.") from None
    columns = ("Semestre", *SERIES.values())
    table = ResultTable(
        "student_general",
        "Análise Geral",
        columns,
        tuple((period_label(p), *(lookup.get((p, s)) for s in SERIES)) for p in axis),
        "matrículas acadêmicas distintas",
        "Ausência de evento não equivale a zero.",
    )
    notes = (
        "Origem institucional pseudonimizada; matrículas distintas não equivalem a pessoas únicas.",
        "Direito (DIR/JUR) pendente; não incluído nos resultados.",
        "Eventos classificados na extração conforme as quatro medidas da Análise Geral do PBIP.",
        "Processo seletivo e matrícula individual indisponíveis; forma de ingresso é outro filtro.",
        "Situação atual é cadastral. Ajustes individuais e conciliação com o painel "
        "permanecem pendentes.",
        "Ausências preservadas; sem interpolação, equivalência de cursos ou soma de subtotais.",
    )
    return CalculatedAnalysis(
        AnalysisKind.STUDENTS,
        "Análise temporal › Análise Geral",
        "Calculado" if lookup else "Sem eventos no recorte",
        ", ".join(departments),
        AnalysisFilters(
            period_label(start),
            period_label(end),
            period_label(end),
            courses=tuple(
                v if v is not None else "Não informado (nulo)"
                for v in filters.get("curso_codigo", filters.get("curso", []))
            ),
            qualifications=tuple(
                v if v is not None else "Não informado (nulo)"
                for v in filters.get("habilitacao_codigo", filters.get("habilitacao", []))
            ),
            levels=tuple(
                v if v is not None else "Não informado (nulo)" for v in filters.get("nivel", [])
            ),
            shifts=tuple(
                v if v is not None else "Não informado (nulo)" for v in filters.get("turno", [])
            ),
            entry_kinds=tuple(
                v if v is not None else "Não informado (nulo)"
                for v in filters.get("forma_ingresso", [])
            ),
        ),
        INSTITUTIONAL_SOURCE,
        options.batch,
        hashlib.sha256(json.dumps(params, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        (),
        (table,),
        (ChartSpec(table.key, "Análise Geral", "Semestre", tuple(SERIES.values())),),
        notes,
        "Contagem de matrículas distintas por série e semestre, após os filtros selecionados.",
        "alunos-pbip-eventos-v1",
    )
