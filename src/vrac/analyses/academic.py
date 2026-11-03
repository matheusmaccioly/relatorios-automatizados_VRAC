"""R02–R06: cálculos determinísticos dos roteiros acadêmicos documentados."""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from itertools import combinations

from vrac.analyses.academic_data import AcademicSource, StudentRow
from vrac.analyses.faculty_overview import NOT_INFORMED, semaphore_status

type Scalar = str | int | float | bool | None
HISTORICAL_CADRES = frozenset(
    {"PROF PRINCIPAL", "PROF QCI", "PROF QCP", "PROF HORISTA", "PROF EMERITO", "PROF SUPLEMENTAR"}
)


class AnalysisKind(StrEnum):
    QP = "R02"
    HISTORY = "R03"
    WORKLOAD = "R04"
    FUNCTIONS = "R05"
    STUDENTS = "R06"


TITLES = {
    AnalysisKind.QP: "Corpo docente geral e QP",
    AnalysisKind.HISTORY: "Histórico semestral docente",
    AnalysisKind.WORKLOAD: "Carga horária e alocações",
    AnalysisKind.FUNCTIONS: "Dupla função e funções administrativas",
    AnalysisKind.STUDENTS: "Evolução de matrículas e alunos",
}


@dataclass(frozen=True, slots=True)
class AnalysisFilters:
    first_period: str
    last_period: str
    workload_period: str
    qp_cadres: tuple[str, ...] = ()
    courses: tuple[str, ...] = ()
    cadres: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    qualifications: tuple[str, ...] = ()
    shifts: tuple[str, ...] = ()
    levels: tuple[str, ...] = ()
    entry_kinds: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Metric:
    label: str
    value: int | float | None
    unit: str
    status: str = "Calculado"
    note: str = ""


@dataclass(frozen=True, slots=True)
class ResultTable:
    key: str
    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[Scalar, ...], ...]
    unit: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class ChartSpec:
    table: str
    title: str
    x: str
    series: tuple[str, ...]
    kind: str = "line"


@dataclass(frozen=True, slots=True)
class CalculatedAnalysis:
    kind: AnalysisKind
    title: str
    status: str
    department: str
    filters: AnalysisFilters
    source: str
    version: str
    fingerprint: str
    metrics: tuple[Metric, ...]
    tables: tuple[ResultTable, ...]
    charts: tuple[ChartSpec, ...]
    notes: tuple[str, ...]
    narrative: str
    calculation_version: str = "academic-r02-r06-v1"


def period_code(value: str) -> int:
    if not re.fullmatch(r"[0-9]{4}\.[12]", value) or int(value[:4]) < 1900:
        raise ValueError("Período inválido. Use ano e semestre disponíveis.")
    return int(value[:4]) * 10 + int(value[-1])


def period_label(code: int) -> str:
    return f"{code // 10}.{code % 10}"


def faculty_period(reference: date) -> int:
    return reference.year * 10 + (1 if reference.month <= 7 else 2)


def _periods(source: AcademicSource, filters: AnalysisFilters) -> tuple[int, ...]:
    first, last = period_code(filters.first_period), period_code(filters.last_period)
    workload = period_code(filters.workload_period)
    available = {period_code(x) for x in source.periods}
    if first > last or not {first, last, workload} <= available:
        raise ValueError("Selecione um intervalo e semestre de carga disponíveis.")
    return tuple(sorted(p for p in available if first <= p <= last))


def _label(value: str | None) -> str:
    return value if value else NOT_INFORMED


def _sum(values: list[float | None]) -> float | None:
    known = [value for value in values if value is not None]
    return sum(known) if known else None


def _matches(value: str | None, selection: tuple[str, ...]) -> bool:
    return not selection or _label(value) in selection


def _result(
    kind: AnalysisKind,
    source: AcademicSource,
    filters: AnalysisFilters,
    metrics: list[Metric],
    tables: list[ResultTable],
    notes: list[str],
    charts: list[ChartSpec] | None = None,
    *,
    status: str = "Calculado",
    narrative: str = "",
) -> CalculatedAnalysis:
    return CalculatedAnalysis(
        kind,
        TITLES[kind],
        status,
        source.department,
        filters,
        source.faculty.source,
        source.faculty.version,
        source.fingerprint,
        tuple(metrics),
        tuple(tables),
        tuple(charts or ()),
        tuple(dict.fromkeys(notes)),
        narrative,
        calculation_version="academic-docentes-v2"
        if kind in {AnalysisKind.QP, AnalysisKind.HISTORY}
        else "academic-matriculas-v2"
        if kind == AnalysisKind.STUDENTS
        else "academic-carga-v2"
        if kind == AnalysisKind.WORKLOAD
        else "academic-r02-r06-v1",
    )


def _blocked(kind: AnalysisKind, source: AcademicSource, filters: AnalysisFilters, text: str):
    return _result(kind, source, filters, [], [], [text], status="Bloqueado", narrative=text)


def calculate_qp(source: AcademicSource, filters: AnalysisFilters) -> CalculatedAnalysis:
    if "register" not in source.available:
        return _blocked(AnalysisKind.QP, source, filters, "Cadastro docente indisponível.")
    rows = [r for r in source.faculty.register if _matches(r.category, filters.categories)]
    notes = [
        "QP não tem composição institucional definida nos materiais. O grupo selecionado "
        "é uma simulação explícita por quadro e não uma equivalência institucional.",
        "O filtro do grupo comparado não reduz o denominador geral. A base é o cadastro atual, "
        "não o histórico do intervalo selecionado.",
    ]
    if not rows:
        return _result(
            AnalysisKind.QP,
            source,
            filters,
            [],
            [],
            notes,
            status="Sem dados",
            narrative="Não há registros no cadastro para este recorte; ausência não é zero.",
        )
    known_cadres = {_label(r.cadre) for r in source.faculty.register}
    if not set(filters.qp_cadres) <= known_cadres:
        raise ValueError("O grupo comparado contém quadro indisponível neste recorte.")
    general = {r.registration for r in rows if r.registration}
    qp = {r.registration for r in rows if r.registration and r.cadre in filters.qp_cadres}
    unknown = {r.registration for r in rows if r.registration and not r.cadre} - qp
    others = general - qp - unknown
    if any(not r.registration for r in rows):
        notes.append("Há registros sem matrícula funcional; eles não entram na contagem.")
    selected = bool(filters.qp_cadres)
    complete = not unknown and selected
    metrics = [Metric("Geral", len(general), "matrículas funcionais distintas")]
    metrics += [
        Metric(
            "Grupo QP simulado",
            len(qp) if selected else None,
            "matrículas funcionais",
            "Simulação" if selected else "Grupo não selecionado",
        ),
        Metric("Classificação ausente", len(unknown), "matrículas funcionais"),
        Metric(
            "Demais",
            len(others) if complete else None,
            "matrículas funcionais",
            "Simulação" if complete else "Classificação incompleta",
        ),
        Metric(
            "Participação do grupo",
            100 * len(qp) / len(general) if complete and general else None,
            "%",
            "Simulação" if complete and general else "Não calculável",
        ),
    ]
    table = ResultTable(
        "comparison",
        "Geral e grupo comparado",
        ("Resultado", "Quantidade", "Situação"),
        tuple((m.label, m.value, m.status) for m in metrics),
        "por indicador",
    )
    bars = ResultTable(
        "groups",
        "Partição da população",
        ("Grupo", "Matrículas"),
        (
            ("Grupo selecionado", len(qp) if selected else None),
            ("Demais classificados", len(others) if selected else None),
            ("Quadro ausente", len(unknown)),
        ),
        "matrículas funcionais distintas",
    )
    departments = []
    for department in sorted({_label(r.department) for r in rows}):
        local = [r for r in rows if _label(r.department) == department and r.registration]
        local_general = {r.registration for r in local}
        local_qp = {r.registration for r in local if r.cadre in filters.qp_cadres}
        local_unknown = {r.registration for r in local if not r.cadre} - local_qp
        local_complete = selected and not local_unknown
        departments.append(
            (
                department,
                len(local_general),
                len(local_qp) if selected else None,
                len(local_unknown),
                len(local_general - local_qp) if local_complete else None,
                100 * len(local_qp) / len(local_general)
                if local_complete and local_general
                else None,
            )
        )
    department_table = ResultTable(
        "departments",
        "Comparação entre departamentos — cadastro atual",
        (
            "Departamento",
            "Geral",
            "Grupo QP simulado",
            "Classificação ausente",
            "Demais",
            "Participação (%)",
        ),
        tuple(departments),
        "matrículas funcionais distintas; participação em %",
        "O grupo QP não reduz o geral de cada departamento. Matrículas presentes em "
        "mais de um departamento não devem ser somadas para obter o geral do recorte.",
    )
    notes.append(
        "O filtro Quadros docentes não se aplica à R02: use Quadros do grupo QP para "
        "definir o numerador; categoria recorta ambos os conjuntos. Na comparação "
        "departamental, cada participação usa o geral do próprio departamento."
    )
    return _result(
        AnalysisKind.QP,
        source,
        filters,
        metrics,
        [table, bars, department_table],
        notes,
        [
            ChartSpec("groups", "Composição do grupo simulado", "Grupo", ("Matrículas",), "bar"),
            ChartSpec(
                "departments",
                "Geral e QP por departamento",
                "Departamento",
                ("Geral", "Grupo QP simulado"),
                "grouped_bar",
            ),
        ]
        if selected
        else [
            ChartSpec("departments", "Geral por departamento", "Departamento", ("Geral",), "bar")
        ],
        status="Simulação" if complete else "Parcial",
        narrative=f"O cadastro contém {len(general)} matrículas funcionais distintas. "
        "O grupo é definido exclusivamente pelos quadros exibidos nos filtros.",
    )


def calculate_history(source: AcademicSource, filters: AnalysisFilters) -> CalculatedAnalysis:
    if "history" not in source.available:
        return _blocked(
            AnalysisKind.HISTORY, source, filters, "Fonte de histórico docente indisponível."
        )
    periods = _periods(source, filters)
    observed: dict[int, list] = defaultdict(list)
    eligible: dict[int, list] = defaultdict(list)
    invalid = 0
    for row in source.history:
        if row.reference_date is None:
            invalid += 1
            continue
        p = faculty_period(row.reference_date)
        if p not in periods:
            continue
        observed[p].append(row)
        if not row.person_key:
            invalid += 1
        elif (
            row.status == "A"
            and row.payroll_batch in {"3", "4", "7"}
            and row.leave_code != "A4"
            and row.cadre in HISTORICAL_CADRES
            and _matches(row.category, filters.categories)
        ):
            eligible[p].append(row)
    cadres = tuple(sorted({r.cadre for rows in eligible.values() for r in rows if r.cadre}))
    shown = filters.cadres or cadres
    summary, by_cadre, monthly, monthly_history, details = [], [], [], [], []
    for period in periods:
        rows = eligible[period]
        total = len({r.person_key for r in rows}) if observed[period] else None
        months = len({r.reference_date.month for r in observed[period]})
        summary.append((period_label(period), total, months, 7 if period % 10 == 1 else 5))
        for cadre in shown:
            amount = (
                len({r.person_key for r in rows if r.cadre == cadre}) if observed[period] else None
            )
            by_cadre.append((period_label(period), cadre, amount))
        for month in sorted({r.reference_date.month for r in observed[period]}):
            monthly.append(
                (
                    period_label(period),
                    f"{period // 10}-{month:02}",
                    len({r.person_key for r in rows if r.reference_date.month == month}),
                )
            )
        observed_months = {r.reference_date.month for r in observed[period]}
        expected_months = range(1, 8) if period % 10 == 1 else range(8, 13)
        for month in expected_months:
            month_rows = [r for r in rows if r.reference_date.month == month]
            present = month in observed_months
            monthly_history.append(
                (
                    period_label(period),
                    f"{period // 10}-{month:02}",
                    month,
                    len({r.person_key for r in month_rows}) if present else None,
                    *(
                        len({r.person_key for r in month_rows if r.cadre == cadre})
                        if present
                        else None
                        for cadre in shown
                    ),
                )
            )
        for row in rows:
            details.append(
                (
                    period_label(period),
                    row.reference_date.isoformat()[:10],
                    row.department,
                    row.registration,
                    row.cadre,
                    row.category,
                    row.payroll_batch,
                )
            )
    notes = [
        (
            "Pessoas distintas são recalculadas na união dos meses do "
            "semestre; contagens mensais não são somadas."
        ),
        (
            "Calendário docente documentado: janeiro a julho = semestre 1; "
            "agosto a dezembro = semestre 2."
        ),
        (
            "Situação A; lotes 3/4/7; exclusão A4; seis quadros docentes "
            "documentados. Lotação histórica."
        ),
        (
            "Uma pessoa pode constar em dois quadros no semestre. As séries "
            "por quadro não formam uma soma do total."
        ),
        (
            "Os gráficos mensais recalculam pessoas distintas em cada competência. "
            "Competência ausente permanece sem valor; competência observada sem "
            "pessoas elegíveis tem zero. O filtro de quadro seleciona séries e "
            "não reduz o total independente."
        ),
    ]
    if invalid:
        notes.append(f"{invalid} registro(s) sem identidade ou data não entram na contagem.")
    if any(r[2] < r[3] for r in summary):
        notes.append(
            "Há semestres sem todas as competências esperadas; ausência não foi convertida em zero."
        )
    wide = []
    for label, total, _, _ in summary:
        counts = {cadre: count for p, cadre, count in by_cadre if p == label}
        wide.append((label, total, *(counts.get(c) for c in shown)))
    tables = [
        ResultTable(
            "history",
            "Presença por semestre",
            ("Período", "Total", *shown),
            tuple(wide),
            "pessoas distintas",
        ),
        ResultTable(
            "coverage",
            "Cobertura das competências",
            ("Período", "Pessoas", "Meses presentes", "Meses esperados"),
            tuple(summary),
            "meses e pessoas",
        ),
        ResultTable(
            "monthly",
            "Detalhamento mensal",
            ("Período", "Competência", "Pessoas"),
            tuple(monthly),
            "pessoas distintas no mês",
        ),
        ResultTable(
            "monthly_history",
            "Professores ativos por semestre e mês",
            ("Período", "Competência", "Mês", "Total", *shown),
            tuple(monthly_history),
            "pessoas distintas no mês",
            "Total independente das séries por quadro; uma pessoa em mais de um quadro "
            "pode aparecer em mais de uma série. Competência sem registros fica ausente.",
        ),
        ResultTable(
            "history_detail",
            "Registros históricos elegíveis",
            (
                "Período",
                "Referência",
                "Departamento histórico",
                "Matrícula fictícia",
                "Quadro",
                "Categoria",
                "Lote",
            ),
            tuple(details),
            "registros; não pessoas",
        ),
    ]
    return _result(
        AnalysisKind.HISTORY,
        source,
        filters,
        [Metric("Semestres com dados", sum(bool(observed[p]) for p in periods), "semestres")],
        tables,
        notes,
        [
            ChartSpec(
                "monthly_history",
                "Quantidade de professores ativos ao longo do tempo",
                "Competência",
                ("Total",),
            ),
            ChartSpec(
                "monthly_history",
                "Professores ativos por quadro, semestre e mês",
                "Competência",
                tuple(shown),
                "stacked_bar",
            ),
            ChartSpec("history", "Total de pessoas distintas por semestre", "Período", ("Total",)),
            ChartSpec(
                "history",
                "Presenças por quadro — séries sobrepostas",
                "Período",
                tuple(shown),
                "stacked_bar",
            ),
        ],
        status="Calculado"
        if all(r[2] == r[3] for r in summary) and not invalid
        else "Parcial"
        if any(observed.values())
        else "Sem dados",
        narrative=(
            "O histórico mostra presença de pessoas no departamento de cada "
            "competência, sem somar meses."
        ),
    )


def calculate_workload(source: AcademicSource, filters: AnalysisFilters) -> CalculatedAnalysis:
    if "workloads" not in source.available:
        return _blocked(
            AnalysisKind.WORKLOAD, source, filters, "Fonte de Horas Reais indisponível."
        )
    selected = period_code(filters.workload_period)
    grouped: dict[str, list] = defaultdict(list)
    for row in source.workloads:
        if (
            row.semester == selected
            and row.registration
            and _matches(row.cadre, filters.cadres)
            and _matches(row.category, filters.categories)
        ):
            grouped[row.registration].append(row)
    compatible = bool(
        "policy" in source.available
        and source.policy.synthetic_units
        and source.policy.real_hours_unit
        and source.policy.real_hours_unit.strip()
        and source.policy.real_hours_unit == source.policy.contracted_hours_unit
    )
    unit = source.policy.real_hours_unit or "unidade não informada"
    notes = [
        (
            "Horas Reais vêm da fonte dedicada, por vínculo e semestre. Não "
            "são reconstruídas por soma das disciplinas."
        ),
        (
            "Semáforo reproduz literalmente os nomes e limites documentados; "
            "não avalia produtividade ou necessidade de contratação."
        ),
        (
            "Detalhamento de disciplinas preserva compartilhamentos, vagas "
            "zero e ausentes; não altera o indicador oficial."
        ),
        "Categoria vem do cadastro atual; não comprova categoria histórica.",
        "Vagas preenchidas não são alunos únicos. Vagas zero exigem conferência; "
        "data de matrícula e exceções não estão disponíveis nesta fonte.",
        "Compartilhada S/N não identifica grupo: não há dedução nem rateio. "
        "Currículo e grupo de compartilhamento não estão disponíveis.",
        f"Unidades declaradas: Horas Reais = {source.policy.real_hours_unit or 'não informada'}; "
        f"contratada = {source.policy.contracted_hours_unit or 'não informada'}; "
        "alocações = unidade não informada.",
    ]
    if compatible:
        notes.append(
            "Comparação em unidades declaradas exclusivamente para a "
            "simulação. A unidade institucional permanece não comprovada."
        )
    else:
        notes.append(
            "Diferença e razão bloqueadas: unidades e referências compatíveis não foram informadas."
        )
    detail, distribution = [], Counter()
    complete_hours = []
    partial_hours = False
    for registration, rows in sorted(grouped.items()):
        hours = _sum([r.real_hours for r in rows])
        contracts = {r.contracted_hours for r in rows if r.contracted_hours is not None}
        contracted = next(iter(contracts)) if len(contracts) == 1 else None
        statuses = {semaphore_status(r.real_hours, r.cadre) for r in rows}
        indicator = next(iter(statuses)) if len(statuses) == 1 else "Indicadores distintos"
        missing = sum(r.real_hours is None for r in rows)
        partial_hours |= missing > 0
        distribution[indicator] += 1
        complete_hours.append(hours)
        difference = (
            hours - contracted
            if compatible and hours is not None and contracted is not None
            else None
        )
        ratio = (
            hours / contracted * 100
            if compatible and hours is not None and contracted not in (None, 0)
            else None
        )
        detail.append(
            (
                registration,
                rows[0].name,
                rows[0].department,
                rows[0].cadre,
                hours,
                contracted,
                difference,
                ratio,
                indicator,
                "Parcial"
                if missing and hours is not None
                else "Nulo na fonte"
                if hours is None
                else "Informado",
            )
        )
        if missing and hours is not None:
            notes.append(
                "Existem somas com parcela nula: o valor conhecido é exibido como parcial."
            )
        if len(contracts) > 1:
            notes.append(
                "Há vínculo com cargas contratuais conflitantes; sua comparação fica indisponível."
            )
    detail_table = ResultTable(
        "workload",
        "Carga por vínculo no semestre",
        (
            "Matrícula fictícia",
            "Nome fictício",
            "Departamento",
            "Quadro",
            "Horas Reais",
            "Carga contratada",
            "Diferença (simulação)",
            "Razão % (simulação)",
            "Indicador do painel",
            "Cobertura",
        ),
        tuple(detail),
        unit,
    )
    real_dist = Counter("ausente" if r[4] is None else str(r[4]) for r in detail)
    contract_dist = Counter("ausente" if r[5] is None else str(r[5]) for r in detail)
    allocations = [
        r for r in source.allocations if r.semester == selected and r.registration in grouped
    ]
    allocation_table = ResultTable(
        "allocation_detail",
        "Alocações por disciplina e turma",
        (
            "Matrícula fictícia",
            "Departamento do vínculo",
            "Departamento da disciplina",
            "Disciplina",
            "Turma",
            "Horas alocadas",
            "Vagas preenchidas",
            "Compartilhada",
            "Classificação",
        ),
        tuple(
            (
                r.registration,
                r.department,
                r.teaching_department,
                r.discipline,
                r.class_id,
                r.allocated_hours,
                r.vacancies_filled,
                r.shared,
                r.classification,
            )
            for r in allocations
        ),
        "registros de alocação; vagas não são alunos únicos",
    )
    tables = [
        detail_table,
        ResultTable(
            "real_distribution",
            "Distribuição de Horas Reais",
            ("Carga", "Vínculos"),
            tuple(sorted(real_dist.items())),
            "vínculos",
        ),
        ResultTable(
            "contract_distribution",
            "Distribuição de carga contratada",
            ("Carga", "Vínculos"),
            tuple(sorted(contract_dist.items())),
            "vínculos",
        ),
        ResultTable(
            "indicators",
            "Indicadores conforme o painel",
            ("Indicador", "Vínculos"),
            tuple(sorted(distribution.items())),
            "vínculos",
        ),
        allocation_table,
    ]
    if "allocations" not in source.available:
        notes.append(
            "Detalhamento de disciplinas indisponível; Horas Reais permanecem disponíveis."
        )
    return _result(
        AnalysisKind.WORKLOAD,
        source,
        filters,
        [
            Metric(
                "Vínculos com registro", len(grouped) if grouped else None, "matrículas funcionais"
            ),
            Metric(
                "Horas Reais informadas",
                _sum(complete_hours),
                unit,
                "Parcial" if partial_hours else "Calculado",
            ),
            Metric(
                "Carga ausente",
                sum(h is None for h in complete_hours) if grouped else None,
                "vínculos",
            ),
        ],
        tables,
        notes,
        [
            ChartSpec(
                "real_distribution", "Distribuição de Horas Reais", "Carga", ("Vínculos",), "bar"
            ),
            ChartSpec(
                "contract_distribution",
                "Distribuição de carga contratada",
                "Carga",
                ("Vínculos",),
                "bar",
            ),
        ],
        status="Sem dados" if not grouped else "Parcial" if partial_hours else "Calculado",
        narrative=(
            f"Semestre {filters.workload_period}: cargas oficiais e alocações "
            "são apresentadas em visões separadas."
        ),
    )


def _as_date(value: date) -> date:
    return date(value.year, value.month, value.day)


def calculate_functions(source: AcademicSource, filters: AnalysisFilters) -> CalculatedAnalysis:
    periods = _periods(source, filters)
    first = date(periods[0] // 10, 1 if periods[0] % 10 == 1 else 8, 1)
    last = date(periods[-1] // 10 + (periods[-1] % 10 == 2), 8 if periods[-1] % 10 == 1 else 1, 1)
    register = [
        r
        for r in source.faculty.register
        if _matches(r.cadre, filters.cadres) and _matches(r.category, filters.categories)
    ]
    registrations = {r.registration for r in register if r.registration}
    register_available = "register" in source.available
    if not register_available:
        if filters.cadres or filters.categories:
            return _blocked(
                AnalysisKind.FUNCTIONS,
                source,
                filters,
                "Cadastro indisponível para aplicar os filtros docentes às funções.",
            )
        registrations = {
            r.registration for r in (*source.functions, *source.appointments) if r.registration
        }
    dual = {r.registration for r in register if r.registration and r.dual_role == "S"}
    events = [
        r
        for r in source.functions
        if r.registration in registrations
        and 1 <= r.month <= 12
        and faculty_period(date(r.year, r.month, 1)) in periods
    ]
    appointments = [
        a
        for a in source.appointments
        if a.registration in registrations
        and a.administrative
        and _as_date(a.start) < last
        and (a.end is None or _as_date(a.end) >= first)
        and (a.end is None or _as_date(a.end) >= _as_date(a.start))
    ]
    confirmed = {a.registration for a in appointments}
    simultaneous = []
    for one, two in combinations(appointments, 2):
        if one.registration != two.registration or one.role == two.role:
            continue
        start = max(first, _as_date(one.start), _as_date(two.start))
        end = min(
            last - timedelta(days=1),
            _as_date(one.end) if one.end else last,
            _as_date(two.end) if two.end else last,
        )
        if start < last and start <= end:
            simultaneous.append(
                (one.registration, one.role, two.role, start.isoformat(), end.isoformat())
            )
    have_events = "functions" in source.available
    have_appointments = "appointments" in source.available
    if not register and not events and not appointments and register_available:
        return _result(
            AnalysisKind.FUNCTIONS,
            source,
            filters,
            [],
            [],
            [],
            status="Sem dados",
            narrative="Não há registros neste recorte; ausência não é zero.",
        )
    notes = [
        (
            "Dupla função cadastral, registro de gratificação e cargo "
            "administrativo são evidências distintas."
        ),
        (
            "Quantidade de registros de função conta linhas; quantidade de "
            "vínculos conta matrículas distintas."
        ),
        (
            "Não são exibidos valores financeiros. Papéis sucessivos não "
            "comprovam exercício simultâneo."
        ),
        (
            "O indicador de dupla função refere-se ao cadastro atual; eventos "
            "e vigências usam o intervalo selecionado."
        ),
    ]
    if source.policy.synthetic_appointments:
        notes.append(
            "Comprovações e vigências administrativas são cenários gerados "
            "exclusivamente para simulação, sem validade institucional."
        )
    metrics = [
        Metric(
            "Dupla função no cadastro", len(dual) if register else None, "matrículas funcionais"
        ),
        Metric(
            "Vínculos com registro de função",
            len({r.registration for r in events}) if have_events else None,
            "matrículas funcionais",
            "Calculado" if have_events else "Fonte indisponível",
        ),
        Metric(
            "Registros de função",
            len(events) if have_events else None,
            "linhas",
            "Calculado" if have_events else "Fonte indisponível",
        ),
        Metric(
            "Função administrativa com evidência",
            len(confirmed) if have_appointments else None,
            "matrículas funcionais",
            "Simulação" if source.policy.synthetic_appointments else "Fonte indisponível",
        ),
        Metric(
            "Vínculos com papéis simultâneos",
            len({r[0] for r in simultaneous}) if have_appointments else None,
            "matrículas funcionais",
        ),
    ]
    comparison = tuple(
        (
            r.registration,
            r.name,
            _label(r.dual_role),
            sum(e.registration == r.registration for e in events) if have_events else None,
            "Simulação com evidência"
            if r.registration in confirmed
            else "Sem evidência no recorte",
        )
        for r in register
    )
    tables = [
        ResultTable(
            "function_comparison",
            "Evidências por vínculo",
            (
                "Matrícula fictícia",
                "Nome fictício",
                "Dupla função",
                "Registros de função",
                "Evidência administrativa",
            ),
            comparison,
            "por vínculo",
        ),
        ResultTable(
            "function_events",
            "Registros de função no intervalo",
            (
                "Ano",
                "Mês",
                "Matrícula fictícia",
                "Departamento",
                "Departamento de distribuição",
                "Descrição",
                "Papel",
            ),
            tuple(
                (
                    r.year,
                    r.month,
                    r.registration,
                    r.department,
                    r.distribution_department,
                    r.description,
                    r.role,
                )
                for r in events
            ),
            "linhas da fonte",
        ),
        ResultTable(
            "appointments",
            "Vigências com comprovação sintética",
            ("Matrícula fictícia", "Papel", "Início", "Fim", "Evidência"),
            tuple(
                (
                    r.registration,
                    r.role,
                    r.start.isoformat()[:10],
                    r.end.isoformat()[:10] if r.end else None,
                    r.evidence,
                )
                for r in appointments
            ),
            "registros de vigência",
        ),
        ResultTable(
            "simultaneous",
            "Sobreposição de papéis distintos",
            ("Matrícula fictícia", "Papel A", "Papel B", "Início comum", "Fim comum"),
            tuple(simultaneous),
            "pares de papéis; não contratações",
        ),
    ]
    tables.append(
        ResultTable(
            "function_groups",
            "Vínculos por evidência",
            ("Evidência", "Vínculos"),
            tuple((m.label, m.value) for m in metrics if m.unit == "matrículas funcionais"),
            "matrículas funcionais distintas",
        )
    )
    return _result(
        AnalysisKind.FUNCTIONS,
        source,
        filters,
        metrics,
        tables,
        notes,
        charts=[
            ChartSpec(
                "function_groups",
                "Evidências de função por vínculo",
                "Evidência",
                ("Vínculos",),
                "bar",
            )
        ],
        status="Sem dados"
        if not register and register_available
        else "Simulação"
        if have_appointments and have_events and register_available
        else "Parcial",
        narrative=(
            "As evidências são apresentadas separadamente; a existência de "
            "gratificação não define função administrativa."
        ),
    )


def _student_matches(row: StudentRow, filters: AnalysisFilters) -> bool:
    return (not filters.courses or row.course in filters.courses) and all(
        _matches(value, selected)
        for value, selected in (
            (row.qualification, filters.qualifications),
            (row.shift, filters.shifts),
            (row.level, filters.levels),
            (row.entry_kind, filters.entry_kinds),
        )
    )


def calculate_students(source: AcademicSource, filters: AnalysisFilters) -> CalculatedAnalysis:
    periods = _periods(source, filters)
    have_history, have_current = (
        "student_history" in source.available,
        "students" in source.available,
    )
    if not (have_history or have_current):
        return _blocked(AnalysisKind.STUDENTS, source, filters, "Fontes acadêmicas indisponíveis.")
    history = [r for r in source.student_history if _student_matches(r, filters)]
    current = [r for r in source.students if _student_matches(r, filters)]
    # O limite de ingresso de B-M-035 vem do cadastro, sem multiplicar a fato histórica.
    entry_by_registration: dict[int, list[int]] = defaultdict(list)
    for row in source.students:
        if row.registration is not None and row.entry_period is not None:
            entry_by_registration[row.registration].append(row.entry_period)
    have_scholarships = "scholarships" in source.available
    scholarships = {
        (r.registration, r.period) for r in source.scholarships if r.registration is not None
    }
    rows, course_rows, changes = [], [], []
    courses = tuple(sorted({r.course for r in (*history, *current)}))

    def count_at(period: int, course: str | None = None) -> tuple:
        hs = [r for r in history if (course is None or r.course == course)]
        cs = [r for r in current if (course is None or r.course == course)]
        # O detalhe deve reproduzir a seleção individual do código do curso.
        completions: dict[int, int] = {}
        for row in cs:
            if (
                row.registration is not None
                and row.status in {"FR", "TD"}
                and row.period is not None
            ):
                completions[row.registration] = min(
                    completions.get(row.registration, row.period), row.period
                )
        observed = any(r.period == period for r in hs)
        candidates = {
            r.registration
            for r in hs
            if r.period == period and r.status in {"MT", "MC"} and r.registration is not None
        }
        missing_entries = any(not entry_by_registration.get(r) for r in candidates)
        eligible = {
            r.registration
            for r in hs
            if r.period == period
            and r.status in {"MT", "MC"}
            and r.registration is not None
            and entry_by_registration.get(r.registration)
            and min(entry_by_registration[r.registration]) <= period
        }
        enrolled = (
            len(eligible)
            if observed and have_history and have_current and not missing_entries
            else None
        )
        scholarship = (
            len({r for r in eligible if (r, period) in scholarships})
            if enrolled is not None and have_scholarships
            else None
        )
        completed = (
            sum(event == period for event in completions.values())
            if have_current and (observed or any(r.period == period for r in cs))
            else None
        )
        entrants = {
            r.registration
            for r in hs
            if r.registration is not None
            and r.entry_period == period
            and (r.period == period or r.entry_kind == "Dupla Diplomacao")
        }
        entering = len(entrants) if have_history and (observed or entrants) else None
        return (enrolled, scholarship, completed, entering)

    for period in periods:
        amounts = count_at(period)
        rows.append((period_label(period), *amounts))
        for course in courses:
            course_rows.append((course, period_label(period), *count_at(period, course)))
    for previous, current_row in zip(rows, rows[1:], strict=False):
        base, value = previous[1], current_row[1]
        delta = value - base if value is not None and base is not None else None
        percentage = (
            (value - base) / base * 100 if value is not None and base not in (None, 0) else None
        )
        changes.append(
            (
                previous[0],
                current_row[0],
                base,
                value,
                delta,
                percentage,
                "Ausência de dado" if delta is None else "Base zero" if base == 0 else "Calculado",
            )
        )
    notes = [
        (
            "Unidade: matrículas acadêmicas distintas, não pessoas únicas. "
            "Séries usam populações próprias."
        ),
        "Matriculados: MT/MC por período e limite de ingresso do cadastro (B-M-035).",
        (
            "Bolsistas: existência de pelo menos um registro de bolsa na "
            "matrícula/período (B-M-038); linhas repetidas não multiplicam "
            "bolsistas."
        ),
        (
            "A projeção sintética de bolsas por departamento usa pares de matrícula/departamento "
            "do histórico sem vigência por período; não reconstrói transferências."
        ),
        (
            "Formados: FR/TD no cadastro e menor período por matrícula "
            "(B-M-036); HF não foi acrescentado. Não é uma reconstrução completa "
            "dos eventos históricos de formação."
        ),
        (
            "Ingressantes: ingresso no ponto do eixo e período do aluno igual "
            "ao ponto, ou Dupla Diplomacao (B-M-070)."
        ),
        (
            "Período sem registros fica ausente; base zero não produz "
            "variação percentual. Estoques de semestres não são somados."
        ),
        (
            "Cursos permanecem separados por código. Nenhuma equivalência ou "
            "transferência foi presumida pelo nome."
        ),
    ]
    if not have_scholarships:
        notes.append("Fonte de bolsas indisponível; apenas a série de bolsistas fica bloqueada.")
    if not have_current:
        notes.append(
            "Cadastro acadêmico indisponível; matriculados, bolsistas e formados ficam bloqueados."
        )
    if have_current and any(
        r.registration is not None
        and r.status in {"MT", "MC"}
        and r.period in periods
        and not entry_by_registration.get(r.registration)
        for r in history
    ):
        notes.append(
            "Ingresso desconhecido no cadastro lido: matriculados e bolsistas ficam ausentes "
            "nos pontos e cursos com esses candidatos; ingresso desconhecido não vira zero."
        )
    missing = sum(r.registration is None for r in history)
    if missing:
        notes.append(
            f"{missing} registro(s) acadêmico(s) sem matrícula foram excluídos das contagens."
        )
    headers = ("Período", "Matriculados", "Bolsistas matriculados", "Formados", "Ingressantes")
    tables = [
        ResultTable(
            "students",
            "Quatro séries acadêmicas",
            headers,
            tuple(rows),
            "matrículas acadêmicas distintas",
        ),
        ResultTable(
            "student_courses",
            "Séries separadas por curso",
            ("Curso", *headers),
            tuple(course_rows),
            "matrículas acadêmicas distintas",
        ),
        ResultTable(
            "enrollment_change",
            "Variação de matriculados entre períodos",
            ("De", "Para", "Base", "Atual", "Diferença", "Variação %", "Situação"),
            tuple(changes),
            "matrículas e percentual",
        ),
    ]
    last = rows[-1]
    return _result(
        AnalysisKind.STUDENTS,
        source,
        filters,
        [
            Metric(
                label,
                value,
                "matrículas acadêmicas",
                "Calculado" if value is not None else "Ausente/indisponível",
            )
            for label, value in zip(headers[1:], last[1:], strict=True)
        ],
        tables,
        notes,
        [ChartSpec("students", "Evolução das quatro séries acadêmicas", "Período", headers[1:])],
        status="Sem dados"
        if all(v is None for row in rows for v in row[1:])
        else "Parcial"
        if any(v is None for row in rows for v in row[1:])
        else "Calculado",
        narrative=(
            f"As quatro séries são recalculadas por período. Os cartões referem-se a {last[0]}."
        ),
    )


def calculate(
    kind: AnalysisKind, source: AcademicSource, filters: AnalysisFilters
) -> CalculatedAnalysis:
    if not isinstance(kind, AnalysisKind):
        raise ValueError("Análise fora da lista disponível.")
    _periods(source, filters)
    calculators = {
        AnalysisKind.QP: calculate_qp,
        AnalysisKind.HISTORY: calculate_history,
        AnalysisKind.WORKLOAD: calculate_workload,
        AnalysisKind.FUNCTIONS: calculate_functions,
        AnalysisKind.STUDENTS: calculate_students,
    }
    return calculators[kind](source, filters)
