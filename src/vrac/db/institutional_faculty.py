"""Adaptador fechado das sete exportações docentes; sem dados sintéticos ou fallback."""

from collections import defaultdict
from datetime import date
from uuid import UUID

from vrac.analyses.academic_data import (
    AcademicSource,
    AllocationRow,
    FunctionRow,
    HistoryRow,
    WorkloadRow,
)
from vrac.analyses.faculty_overview import FacultySource, RealHoursRow, RegisterRow
from vrac.authorization import require_data_access
from vrac.db.faculty_csv_reader import load_scope
from vrac.demo_data import DemoDataError, DemoOptions
from vrac.department_hierarchy import resolve_departments
from vrac.provenance import INSTITUTIONAL_SOURCE
from vrac.settings import DataMode, Settings
from vrac.supabase_auth import current_session


def load_options(settings: Settings) -> DemoOptions:
    require_data_access(settings)
    if settings.data_mode != DataMode.PSEUDONYMIZED:
        raise DemoDataError("Selecione a origem institucional pseudonimizada.")
    try:
        session = current_session()
        data = session.client.rpc("vrac_docentes_options").execute().data
        if (
            data["synthetic"] is not False
            or data["origin"] != "institucional_pseudonimizada"
            or data["batch"] != session.batch
            or tuple(data["departments"]) != session.departments
            or not data["periods"]
        ):
            raise ValueError
        return DemoOptions(
            tuple(data["departments"]),
            tuple(data["periods"]),
            data["periods"][-1],
            INSTITUTIONAL_SOURCE,
        )
    except Exception:
        raise DemoDataError(
            "Filtros institucionais indisponíveis. Valide novamente sua sessão."
        ) from None


def load_faculty_departments(settings: Settings) -> tuple[str, ...]:
    return load_options(settings).departments


def _number(value: object) -> float | None:
    return None if value is None else float(value)


def adapt(
    parts: dict[str, list[dict]], *, department: str, batch: str, periods: tuple[str, ...]
) -> AcademicSource:
    """Regras de vínculo e competência verificadas no pacote e no modelo fornecidos."""
    register = tuple(
        RegisterRow(
            r["departamento_alocacao"],
            r["vinculo_id"],
            None,
            r["pessoa_id"],
            r["nome_ficticio"],
            r["quadro"],
            r["categoria"],
            r["situacao"],
            r["dupla_funcao"],
            None,
            _number(r["carga_semanal"]),
            None,
            None,
            link_key=r["vinculo_id"],
        )
        for r in parts["cadastro"]
    )
    notes = (
        "Origem institucional pseudonimizada; IDs não são matrículas reais. Acesso restrito.",
        "Cadastro atual e histórico da população atualmente alocada; "
        "não representa lotação histórica.",
        "Horas Reais disponíveis somente em 2026. Sem antecedentes, "
        "último semestre conhecido é limitado ao lote.",
        "Titulação, tempo de casa e vínculos extraordinários não foram fornecidos.",
    )
    real = tuple(
        RealHoursRow(
            None, r["semestre"], _number(r["horas_reais"]), r["quadro"], link_key=r["vinculo_id"]
        )
        for r in parts["horas_reais"]
    )
    faculty = FacultySource(department, register, real, INSTITUTIONAL_SOURCE, batch, notes=notes)
    lookup = defaultdict(list)
    for r in register:
        lookup[(r.department, r.registration)].append(r)

    def one(rows: list, field: str):
        values = {getattr(r, field) for r in rows}
        return next(iter(values)) if len(values) == 1 else None

    workloads = tuple(
        WorkloadRow(
            r["departamento_alocacao"],
            r["vinculo_id"],
            r["semestre"],
            one(lookup[(r["departamento_alocacao"], r["vinculo_id"])], "name"),
            r["quadro"],
            one(lookup[(r["departamento_alocacao"], r["vinculo_id"])], "category"),
            _number(r["horas_reais"]),
            _number(r["horas_contratuais"]),
        )
        for r in parts["horas_reais"]
    )
    allocations = tuple(
        AllocationRow(
            r["departamento_alocacao"],
            r["unidade_oferta"],
            r["vinculo_id"],
            r["semestre"],
            r["disciplina_id"],
            r["turma_id"],
            _number(r["horas_alocadas"]),
            r["vagas_preenchidas"],
            {"Sim": "S", "Não": "N"}.get(r["compartilhada"], r["compartilhada"]),
            None,
        )
        for r in parts["alocacoes"]
    )
    functions = tuple(
        FunctionRow(
            r["departamento_alocacao"],
            None,
            r["vinculo_id"],
            r["ano"],
            r["mes"],
            None if r["descricao_id"] is None else "Descrição pseudonimizada " + r["descricao_id"],
            None if r["papel_id"] is None else "Papel pseudonimizado " + r["papel_id"],
        )
        for r in parts["eventos_funcoes"]
    )
    movements = defaultdict(list)
    history_ok = True
    for r in parts["historico_cargos"]:
        if r["competencia"] is None:
            continue  # ISBLANK excluído pelo modelo original
        try:
            # FOLHA é ordenável numérico, não uma data. Preserva inclusive meses 00/13.
            competence = int(r["competencia"])
        except (ValueError, TypeError):
            history_ok = False
            continue
        movements[(r["departamento_alocacao"], r["vinculo_id"])].append(
            (competence, r["quadro"], r["categoria"])
        )
    history = []
    for r in parts["historico_mensal"]:
        candidates = [
            m
            for m in movements[(r["departamento_alocacao"], r["vinculo_id"])]
            if m[0] <= r["ano"] * 100 + r["mes"]
        ]
        cadre = category = None
        if candidates:
            latest = max(m[0] for m in candidates)
            current = {(m[1], m[2]) for m in candidates if m[0] == latest}
            if len(current) == 1:
                cadre, category = current.pop()
            else:
                history_ok = False  # Não inventar collation para MAX de textos conflitantes.
        else:
            history_ok = False  # Quadro ausente não pode virar zero de elegíveis.
        history.append(
            HistoryRow(
                r["departamento_alocacao"],
                r["pessoa_id"],
                r["vinculo_id"],
                date(r["ano"], r["mes"], 1),
                cadre,
                category,
                "A" if r["ativo"] == 1 else None,
                None if r["lote"] is None else str(r["lote"]),
                "A4" if r["excluido_a4"] == 1 else None,
            )
        )
    available = {"register", "real_hours", "workloads", "allocations", "functions"}
    errors = list(notes)
    if history_ok:
        available.add("history")
    else:
        errors.append(
            "Histórico bloqueado neste recorte: cargo/quadro mensal ausente, "
            "conflitante ou competência não numérica."
        )
    errors.append(
        "Comparação entre cargas bloqueada até confirmação das unidades; "
        "funções sem vigências e alunos sem fontes neste lote."
    )
    return AcademicSource(
        department,
        faculty,
        periods,
        history=tuple(history),
        workloads=workloads,
        allocations=allocations,
        functions=functions,
        available=frozenset(available),
        errors=tuple(errors),
    )


def load_academic_source(
    settings: Settings, *, department: str, departments: tuple[str, ...] | None = None
) -> AcademicSource:
    options = load_options(settings)
    try:
        selected = resolve_departments(options.departments, department, departments)
        batch = current_session().batch
        parts = {
            name: list(load_scope(batch=UUID(batch), component=name, departments=selected))
            for name in (
                "cadastro",
                "horas_reais",
                "historico_mensal",
                "historico_cargos",
                "alocacoes",
                "eventos_funcoes",
            )
        }
        return adapt(parts, department=department, batch=batch, periods=options.periods)
    except (ValueError, TypeError, KeyError):
        raise DemoDataError(
            "Carga institucional incompatível; nenhum dado sintético foi carregado."
        ) from None


def load_faculty_source(
    settings: Settings, *, department: str, departments: tuple[str, ...] | None = None
) -> FacultySource:
    options = load_options(settings)
    try:
        selected = resolve_departments(options.departments, department, departments)
        batch = current_session().batch
        parts = {
            name: list(load_scope(batch=UUID(batch), component=name, departments=selected))
            for name in ("cadastro", "horas_reais")
        }
        parts.update(
            {
                name: []
                for name in ("historico_mensal", "historico_cargos", "alocacoes", "eventos_funcoes")
            }
        )
        return adapt(parts, department=department, batch=batch, periods=options.periods).faculty
    except (ValueError, KeyError, TypeError):
        raise DemoDataError("Cadastro institucional incompatível.") from None
