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
from vrac.department_hierarchy import available_institutional_departments, resolve_departments
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
        departments = available_institutional_departments(tuple(data["departments"]))
        if not departments:
            raise ValueError
        return DemoOptions(
            departments,
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
            r.get("vinculo_extraordinario"),
            _number(r["carga_semanal"]),
            _number(r.get("tempo_casa_anos")),
            r.get("titulacao"),
            link_key=r["vinculo_id"],
        )
        for r in parts["cadastro"]
    )
    years = sorted({r["ano"] for r in parts["historico_mensal"] if r["ano"] is not None})
    current_keys = {(r["departamento_alocacao"], r["vinculo_id"]) for r in parts["cadastro"]}
    # Pacote v2: folha desde 2022 pelo departamento da competência, com desligados.
    # Sem anos anteriores nem vínculos fora do cadastro, é a coorte atual do pacote v1.
    by_payroll = any(
        r["ano"] < 2026 or (r["departamento_alocacao"], r["vinculo_id"]) not in current_keys
        for r in parts["historico_mensal"]
        if r["ano"] is not None
    )
    notes = [
        "Origem institucional pseudonimizada; IDs não são matrículas reais. Acesso restrito.",
        "Horas Reais disponíveis somente em 2026. Sem antecedentes, "
        "último semestre conhecido é limitado ao lote.",
    ]
    if by_payroll:
        notes.append(
            f"Histórico mensal de {years[0]} a {years[-1]}, pelo departamento de cada "
            "competência na folha, como o painel Histórico do Departamento."
        )
    else:
        notes.append(
            "Cadastro atual e histórico da população atualmente alocada; "
            "não representa lotação histórica."
        )
    if not any(r.get("titulacao") or r.get("tempo_casa_anos") for r in parts["cadastro"]):
        notes.append("Titulação, tempo de casa e vínculos extraordinários não foram fornecidos.")
    notes = tuple(notes)
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
    # Layout v2 traz código/nome de disciplina e gratificação legíveis; cargas antigas
    # mantêm os identificadores opacos, sem inventar nomes.
    allocations = tuple(
        AllocationRow(
            r["departamento_alocacao"],
            r["unidade_oferta"],
            r["vinculo_id"],
            r["semestre"],
            r.get("disciplina_codigo") or r["disciplina_id"],
            r.get("turma") or r["turma_id"],
            _number(r["horas_alocadas"]),
            r["vagas_preenchidas"],
            {"Sim": "S", "Não": "N"}.get(r["compartilhada"], r["compartilhada"]),
            r["tipo"],
            level=r["nivel"],
            discipline_name=r.get("disciplina_nome"),
            credits=_number(r.get("creditos")),
            mandatory=r["obrigatoria"],
            distance_hours=_number(r.get("horas_distancia")),
            extension_hours=_number(r.get("horas_extensao")),
            vacancies_offered=r["vagas_ofertadas"],
        )
        for r in parts["alocacoes"]
    )
    functions = tuple(
        FunctionRow(
            r["departamento_alocacao"],
            r.get("departamento_distribuicao"),
            r["vinculo_id"],
            r["ano"],
            r["mes"],
            r.get("gratificacao")
            or (
                None
                if r["descricao_id"] is None
                else "Descrição pseudonimizada " + r["descricao_id"]
            ),
            r.get("papel")
            or (None if r["papel_id"] is None else "Papel pseudonimizado " + r["papel_id"]),
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
        elif not by_payroll:
            history_ok = False  # Quadro ausente não pode virar zero de elegíveis.
        # Folha (v2): sem cargo até a competência, Quadro_Vigente fica vazio e o painel
        # exclui a linha dos seis quadros docentes; aqui o quadro ausente faz o mesmo.
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
    if by_payroll:
        available.add("history_by_department")
    errors = list(notes)
    if history_ok:
        available.add("history")
    else:
        errors.append(
            "Histórico bloqueado neste recorte: cargo/quadro mensal ausente, "
            "conflitante ou competência não numérica."
        )
    errors.append("Gratificações sem vigências de função e alunos sem fontes neste lote.")
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
