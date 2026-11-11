"""R02–R06: cálculos determinísticos dos roteiros acadêmicos documentados."""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import date, timedelta
from enum import StrEnum
from itertools import combinations

from vrac.analyses.academic_data import AcademicSource, StudentRow
from vrac.analyses.faculty_overview import (
    NOT_INFORMED,
    PAGE_FILTER_NOTE,
    is_faculty_cadre,
    semaphore_status,
)
from vrac.indicators import indicator_rank
from vrac.provenance import is_institutional

type Scalar = str | int | float | bool | None
HISTORICAL_CADRES = frozenset(
    {"PROF PRINCIPAL", "PROF QCI", "PROF QCP", "PROF HORISTA", "PROF EMERITO", "PROF SUPLEMENTAR"}
)


class AnalysisKind(StrEnum):
    COMPARISON = "R02"
    QP = "R02"  # Nome antigo, mantido como sinônimo do código interno.
    HISTORY = "R03"
    WORKLOAD = "R04"
    FUNCTIONS = "R05"
    STUDENTS = "R06"


# Títulos seguem as páginas dos painéis de referência (base/) e os slides do roteiro.
TITLES = {
    AnalysisKind.COMPARISON: "Comparação entre grupos de quadro",
    AnalysisKind.HISTORY: "Histórico do departamento",
    AnalysisKind.WORKLOAD: "Carga horária dos professores",
    AnalysisKind.FUNCTIONS: "Gratificações e funções",
    AnalysisKind.STUDENTS: "Análise Geral dos alunos",
}
FACULTY_UNIT = "professores (matrículas funcionais distintas)"
DEFAULT_GROUP_A = "QP"
DEFAULT_GROUP_B = "Geral"
QP_CADRE = "PROF PRINCIPAL"  # Decisão de Talita/Matheus em 11/11/2026: QP = PROF PRINCIPAL.
DEFAULT_STATUS = "ATIVO"  # Seleção padrão do segmentador Situação no painel.
# Séries e título do gráfico da página Análise Geral do painel de alunos.
STUDENT_SERIES = (
    "Quantidade Alunos Matriculados (MT e MC)",
    "Quantidade Bolsistas Matriculados (MT e MC)",
    "Quantidade Formados",
    "Quantidade Ingressantes no(s) Curso(s)",
)
STUDENT_CHART_TITLE = "Alunos e Bolsistas Matriculados, Formados e Ingressantes por Ano e Semestre"


@dataclass(frozen=True, slots=True)
class AnalysisFilters:
    first_period: str
    last_period: str
    workload_period: str
    group_a_cadres: tuple[str, ...] = ()
    courses: tuple[str, ...] = ()
    cadres: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    qualifications: tuple[str, ...] = ()
    shifts: tuple[str, ...] = ()
    levels: tuple[str, ...] = ()
    entry_kinds: tuple[str, ...] = ()
    # Comparação entre grupos: cada grupo é uma seleção de Quadro › Categoria Funcional,
    # como o segmentador do painel; seleção vazia inclui todos os valores.
    group_a_categories: tuple[str, ...] = ()
    group_a_name: str = DEFAULT_GROUP_A
    group_b_cadres: tuple[str, ...] = ()
    group_b_categories: tuple[str, ...] = ()
    group_b_name: str = DEFAULT_GROUP_B
    statuses: tuple[str, ...] = ()


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


PARTICIPATION = "Participação (%)"


def chart_unit(result: CalculatedAnalysis, specification: ChartSpec) -> str:
    """Unidade das séries desenhadas, que podem ser subconjunto da tabela."""
    if result.kind == AnalysisKind.COMPARISON and specification.table == "departments":
        return "%" if PARTICIPATION in specification.series else FACULTY_UNIT
    return next(table.unit for table in result.tables if table.key == specification.table)


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
    if is_institutional(source.faculty.source):
        tables = [
            replace(
                t,
                columns=tuple(
                    "Vínculo pseudonimizado" if c == "Matrícula fictícia" else c for c in t.columns
                ),
            )
            for t in tables
        ]
        if "history_by_department" not in source.available:
            notes = [
                n.replace("Lotação histórica.", "Alocação atual; coorte do cadastro exportado.")
                for n in notes
            ]
        notes.extend(source.errors)
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
        if kind in {AnalysisKind.COMPARISON, AnalysisKind.HISTORY}
        else "academic-matriculas-v2"
        if kind == AnalysisKind.STUDENTS
        else "academic-carga-v2"
        if kind == AnalysisKind.WORKLOAD
        else "academic-funcoes-v2"
        if kind == AnalysisKind.FUNCTIONS
        else "academic-r02-r06-v1",
    )


def _blocked(kind: AnalysisKind, source: AcademicSource, filters: AnalysisFilters, text: str):
    return _result(kind, source, filters, [], [], [text], status="Bloqueado", narrative=text)


RESERVED_GROUP_NAMES = frozenset({"Departamento", PARTICIPATION, "Em ambos os grupos"})


def _in_group(row, cadres: tuple[str, ...], categories: tuple[str, ...]) -> bool:
    return _matches(row.cadre, cadres) and _matches(row.category, categories)


def _describe_group(cadres: tuple[str, ...], categories: tuple[str, ...]) -> str:
    quadros = ", ".join(cadres) or "todos os quadros"
    return quadros + (f" › {', '.join(categories)}" if categories else "")


def calculate_comparison(source: AcademicSource, filters: AnalysisFilters) -> CalculatedAnalysis:
    """Mesmo visual do painel com duas seleções de Quadro › Categoria Funcional (slide 7)."""
    kind = AnalysisKind.COMPARISON
    if "register" not in source.available:
        return _blocked(kind, source, filters, "Cadastro docente indisponível.")
    name_a = filters.group_a_name.strip() or DEFAULT_GROUP_A
    name_b = filters.group_b_name.strip() or DEFAULT_GROUP_B
    if name_a == name_b:
        raise ValueError("Use nomes diferentes para os dois grupos.")
    if {name_a, name_b} & RESERVED_GROUP_NAMES or max(len(name_a), len(name_b)) > 40:
        raise ValueError("Nome de grupo inválido. Use até 40 caracteres.")
    population = [
        r
        for r in source.faculty.register
        if r.registration and is_faculty_cadre(r.cadre) and _matches(r.status, filters.statuses)
    ]
    known = {_label(r.cadre) for r in population}
    if population and not {*filters.group_a_cadres, *filters.group_b_cadres} <= known:
        raise ValueError("Um dos grupos contém quadro indisponível neste recorte.")
    description_a = _describe_group(filters.group_a_cadres, filters.group_a_categories)
    description_b = _describe_group(filters.group_b_cadres, filters.group_b_categories)
    notes = [
        PAGE_FILTER_NOTE,
        "Cada grupo é uma seleção de Quadro › Categoria Funcional, como o filtro do painel; "
        "os dois grupos usam o mesmo departamento e a mesma situação.",
        f"{name_a}: {description_a}. {name_b}: {description_b}.",
        "Base: cadastro atual. Unidade: matrícula funcional distinta, como o cartão "
        "Quantidade de professores do painel.",
    ]
    if not population:
        return _result(
            kind,
            source,
            filters,
            [],
            [],
            notes,
            status="Sem dados",
            narrative="Não há professores no cadastro para este recorte; ausência não é zero.",
        )

    def members(rows, cadres, categories) -> set:
        return {r.registration for r in rows if _in_group(r, cadres, categories)}

    group_a = members(population, filters.group_a_cadres, filters.group_a_categories)
    group_b = members(population, filters.group_b_cadres, filters.group_b_categories)
    both = group_a & group_b
    # Percentual só quando um grupo está contido no outro (ex.: QP dentro do Geral).
    if group_a <= group_b:
        part, whole, share_label = 0, 1, f"{name_a} em % de {name_b}"
    elif group_b <= group_a:
        part, whole, share_label = 1, 0, f"{name_b} em % de {name_a}"
    else:
        part = whole = share_label = None
        notes.append(
            "Os grupos não estão contidos um no outro; o percentual não é calculado. "
            "Professores presentes nos dois grupos aparecem em Em ambos os grupos."
        )

    def share(sets: tuple[set, set]) -> float | None:
        if share_label is None or not sets[whole]:
            return None
        return 100 * len(sets[part]) / len(sets[whole])

    metrics = [
        Metric(name_a, len(group_a), FACULTY_UNIT, note=description_a),
        Metric(name_b, len(group_b), FACULTY_UNIT, note=description_b),
    ]
    if share_label is None:
        metrics.append(Metric("Em ambos os grupos", len(both), FACULTY_UNIT))
    else:
        value = share((group_a, group_b))
        metrics.append(
            Metric(share_label, value, "%", "Calculado" if value is not None else "Não calculável")
        )
    departments = []
    for department in sorted({_label(r.department) for r in population}):
        local = [r for r in population if _label(r.department) == department]
        local_a = members(local, filters.group_a_cadres, filters.group_a_categories)
        local_b = members(local, filters.group_b_cadres, filters.group_b_categories)
        departments.append(
            (
                department,
                len(local_a),
                len(local_b),
                len(local_a & local_b),
                share((local_a, local_b)),
            )
        )
    department_table = ResultTable(
        "departments",
        "Quantidade de professores por Departamento",
        ("Departamento", name_a, name_b, "Em ambos os grupos", PARTICIPATION),
        tuple(departments),
        f"{FACULTY_UNIT}; participação em %",
        (f"Participação = {share_label}, no próprio departamento. " if share_label else "")
        + "Professores com matrícula em mais de um departamento não devem ser somados.",
    )
    groups_table = ResultTable(
        "groups",
        "Definição dos grupos",
        ("Grupo", "Quadro › Categoria Funcional", "Quantidade de professores"),
        ((name_a, description_a, len(group_a)), (name_b, description_b, len(group_b))),
        FACULTY_UNIT,
    )
    charts = [
        ChartSpec(
            "departments",
            "Quantidade de professores por Departamento",
            "Departamento",
            (name_a, name_b),
            "grouped_bar",
        )
    ]
    if share_label is not None and len(departments) > 1:
        charts.append(
            ChartSpec(
                "departments",
                f"{share_label} por departamento",
                "Departamento",
                (PARTICIPATION,),
                "bar",
            )
        )
    return _result(
        kind,
        source,
        filters,
        metrics,
        [department_table, groups_table],
        notes,
        charts,
        narrative=(
            f"No cadastro atual, {name_a} reúne {len(group_a)} e {name_b} reúne "
            f"{len(group_b)} professores (matrículas funcionais distintas)."
        ),
    )


calculate_qp = calculate_comparison  # Nome antigo.


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


WORKLOAD_COLUMNS = (
    "Matrícula fictícia",
    "Nome fictício",
    "Departamento",
    "Quadro de Professores",
    "Categoria Funcional",
    "Indicador de CH",
    "Horas Reais (Semestre Atual)",
    "CH Contratada",
    "Cobertura",
)
ALLOCATION_COLUMNS = (
    "Matrícula fictícia",
    "Departamento do professor",
    "Depto",
    "Nível",
    "Disciplina",
    "Nome Disciplina",
    "Turma",
    "Créditos",
    "CH na Disciplina",
    "Compartilhada?",
    "Obrigatória?",
    "H EAD",
    "H EXT",
    "Tipo",
    "Vagas OF",
    "Vagas OC",
    "Qtd. de Professores",
)


def calculate_workload(source: AcademicSource, filters: AnalysisFilters) -> CalculatedAnalysis:
    """Página Análise de Carga Horária: Horas Reais da fonte dedicada e Indicador de CH."""
    if "workloads" not in source.available:
        return _blocked(
            AnalysisKind.WORKLOAD, source, filters, "Fonte de Horas Reais indisponível."
        )
    selected = period_code(filters.workload_period)
    # Situação vem do cadastro atual, como o segmentador da página (padrão ATIVO).
    status_of: dict[str, set[str]] = defaultdict(set)
    for row in source.faculty.register:
        if row.registration:
            status_of[row.registration].add(_label(row.status))
    grouped: dict[str, list] = defaultdict(list)
    for row in source.workloads:
        if (
            row.semester == selected
            and row.registration
            and _matches(row.cadre, filters.cadres)
            and _matches(row.category, filters.categories)
            and (
                not filters.statuses
                or bool(status_of.get(row.registration, set()) & set(filters.statuses))
            )
        ):
            grouped[row.registration].append(row)
    unit = source.policy.real_hours_unit or "horas"
    notes = [
        "Horas Reais (Semestre Atual) vêm da fonte dedicada, por professor e semestre, "
        "como no painel. Não são reconstruídas pela soma das disciplinas.",
        "O Indicador de CH reproduz literalmente a regra do painel; não avalia "
        "produtividade nem necessidade de contratação.",
        "O Indicador de CH não considera disciplinas ministradas em outros departamentos.",
        "Categoria Funcional e Situação vêm do cadastro atual.",
        "Vagas OC são vagas ocupadas, não alunos únicos. A CH na Disciplina detalha a "
        "distribuição e não substitui as Horas Reais.",
        "Qtd. de Professores conta somente professores presentes nos departamentos lidos; "
        "colegas de outros departamentos na mesma turma não entram.",
    ]
    detail, distribution = [], Counter()
    partial_hours = False
    for registration, rows in grouped.items():
        hours = _sum([r.real_hours for r in rows])
        contracts = {r.contracted_hours for r in rows if r.contracted_hours is not None}
        contracted = next(iter(contracts)) if len(contracts) == 1 else None
        statuses = {semaphore_status(r.real_hours, r.cadre) for r in rows}
        indicator = next(iter(statuses)) if len(statuses) == 1 else "Resultados distintos"
        missing = sum(r.real_hours is None for r in rows)
        partial_hours |= missing > 0
        distribution[indicator] += 1
        detail.append(
            (
                registration,
                rows[0].name,
                rows[0].department,
                rows[0].cadre,
                rows[0].category,
                indicator,
                hours,
                contracted,
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
            notes.append("Há professor com CH Contratada conflitante; o valor fica ausente.")
    # Slide 8 do roteiro: ordem decrescente de Horas Reais; ausentes ao final.
    detail.sort(key=lambda r: (r[6] is None, -(r[6] or 0), (r[1] or "").casefold(), r[0]))
    real_dist = Counter("ausente" if r[6] is None else _format_number(r[6]) for r in detail)
    contract_dist = Counter("ausente" if r[7] is None else _format_number(r[7]) for r in detail)
    allocations = [
        r for r in source.allocations if r.semester == selected and r.registration in grouped
    ]
    teachers: dict[tuple, set[str]] = defaultdict(set)
    for r in source.allocations:
        if r.semester == selected and r.registration:
            teachers[(r.discipline, r.class_id)].add(r.registration)
    allocation_table = ResultTable(
        "allocation_detail",
        "Detalhamento das turmas oferecidas",
        ALLOCATION_COLUMNS,
        tuple(
            (
                r.registration,
                r.department,
                r.teaching_department,
                r.level,
                r.discipline,
                r.discipline_name,
                r.class_id,
                r.credits,
                r.allocated_hours,
                r.shared,
                r.mandatory,
                r.distance_hours,
                r.extension_hours,
                r.classification,
                r.vacancies_offered,
                r.vacancies_filled,
                len(teachers[(r.discipline, r.class_id)]) if r.discipline else None,
            )
            for r in sorted(
                allocations,
                key=lambda r: (
                    r.registration,
                    r.level or "",
                    r.discipline or "",
                    r.class_id or "",
                ),
            )
        ),
        "turmas por professor; vagas não são alunos únicos",
        "Filtros do painel: CH na disciplina e vagas ocupadas sem restrição. "
        "A CH na Disciplina não deve ser somada para substituir Horas Reais.",
    )
    tables = [
        ResultTable(
            "workload",
            "CH Real dos Professores em Disciplinas",
            WORKLOAD_COLUMNS,
            tuple(detail),
            unit,
        ),
        ResultTable(
            "real_distribution",
            "Quantidade de professores por CH Real em Disciplinas",
            ("Horas Reais", "Professores"),
            tuple(sorted(real_dist.items(), key=_number_order)),
            "professores",
        ),
        ResultTable(
            "contract_distribution",
            "Quantidade de professores distintos por CH Contratada",
            ("CH Contratada", "Professores"),
            tuple(sorted(contract_dist.items(), key=_number_order)),
            "professores",
        ),
        ResultTable(
            "indicators",
            "Quantidade de professores por Indicador de CH",
            ("Indicador de CH", "Professores"),
            tuple(sorted(distribution.items(), key=lambda item: indicator_rank(item[0]))),
            "professores",
        ),
        allocation_table,
    ]
    if "allocations" not in source.available:
        notes.append("Detalhamento das turmas indisponível; Horas Reais permanecem disponíveis.")
    return _result(
        AnalysisKind.WORKLOAD,
        source,
        filters,
        [
            Metric(
                "Quantidade de professores distintos",
                len(grouped) if grouped else None,
                FACULTY_UNIT,
            ),
            Metric(
                "Horas Reais informadas",
                _sum([r[6] for r in detail]),
                unit,
                "Parcial" if partial_hours else "Calculado",
            ),
            Metric(
                "Sem Horas Reais",
                sum(r[6] is None for r in detail) if grouped else None,
                "professores",
            ),
        ],
        tables,
        notes,
        [
            ChartSpec(
                "indicators",
                "Quantidade de professores por Indicador de CH",
                "Indicador de CH",
                ("Professores",),
                "bar",
            ),
            ChartSpec(
                "real_distribution",
                "Quantidade de professores por CH Real em Disciplinas",
                "Horas Reais",
                ("Professores",),
                "bar",
            ),
            ChartSpec(
                "contract_distribution",
                "Quantidade de professores distintos por CH Contratada",
                "CH Contratada",
                ("Professores",),
                "bar",
            ),
        ],
        status="Sem dados" if not grouped else "Parcial" if partial_hours else "Calculado",
        narrative=(
            f"Semestre {filters.workload_period}: professores em ordem decrescente de Horas "
            "Reais. O detalhamento das turmas aparece em tabela separada."
        ),
    )


def _format_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}".replace(".", ",")


def _number_order(item: tuple[str, int]) -> tuple[bool, float]:
    try:
        return (False, float(item[0].replace(",", ".")))
    except ValueError:
        return (True, 0.0)


def _as_date(value: date) -> date:
    return date(value.year, value.month, value.day)


def calculate_functions(source: AcademicSource, filters: AnalysisFilters) -> CalculatedAnalysis:
    """Página Análise de Gratificações, com dupla função do cadastro em coluna própria."""
    kind = AnalysisKind.FUNCTIONS
    periods = _periods(source, filters)
    first = date(periods[0] // 10, 1 if periods[0] % 10 == 1 else 8, 1)
    last = date(periods[-1] // 10 + (periods[-1] % 10 == 2), 8 if periods[-1] % 10 == 1 else 1, 1)
    register = [
        r
        for r in source.faculty.register
        if is_faculty_cadre(r.cadre)
        and _matches(r.cadre, filters.cadres)
        and _matches(r.category, filters.categories)
        and _matches(r.status, filters.statuses)
    ]
    registrations = {r.registration for r in register if r.registration}
    register_available = "register" in source.available
    if not register_available:
        if filters.cadres or filters.categories or filters.statuses:
            return _blocked(
                kind,
                source,
                filters,
                "Cadastro indisponível para aplicar os filtros docentes às gratificações.",
            )
        registrations = {
            r.registration for r in (*source.functions, *source.appointments) if r.registration
        }
    dual = {r.registration for r in register if r.registration and r.dual_role in {"S", "Sim"}}
    events = [
        r
        for r in source.functions
        if r.registration in registrations
        and 1 <= r.month <= 12
        and faculty_period(date(r.year, r.month, 1)) in periods
    ]
    have_events = "functions" in source.available
    have_appointments = "appointments" in source.available
    if not register and not events and register_available:
        return _result(
            kind,
            source,
            filters,
            [],
            [],
            [],
            status="Sem dados",
            narrative="Não há registros neste recorte; ausência não é zero.",
        )
    notes = [
        "Gratificação registrada na folha não comprova, sozinha, o exercício de função "
        "administrativa; papéis sucessivos não comprovam exercício simultâneo.",
        "Quantidade de professores conta matrículas distintas; registros contam linhas.",
        "Não são exibidos valores financeiros.",
        "Dupla Função vem do cadastro atual; gratificações usam o intervalo selecionado.",
    ]
    if not register_available:
        notes.append("Cadastro docente indisponível; dupla função não pode ser apurada.")
    if not have_events:
        notes.append("Fonte de gratificações indisponível; essas contagens ficam ausentes.")
    metrics = [
        Metric(
            "Professores com dupla função",
            len(dual) if register else None,
            FACULTY_UNIT,
            "Calculado"
            if register
            else "Fonte indisponível"
            if not register_available
            else "Sem dados",
        ),
        Metric(
            "Quantidade total de professores distintos com gratificação",
            len({r.registration for r in events}) if have_events else None,
            FACULTY_UNIT,
            "Calculado" if have_events else "Fonte indisponível",
        ),
        Metric(
            "Registros de gratificação",
            len(events) if have_events else None,
            "linhas",
            "Calculado" if have_events else "Fonte indisponível",
        ),
    ]

    def distinct_by(key) -> tuple[tuple[str, int], ...]:
        groups: dict[str, set] = defaultdict(set)
        for event in events:
            groups[key(event)].add(event.registration)
        return tuple(sorted(((k, len(v)) for k, v in groups.items()), key=lambda i: (-i[1], i[0])))

    by_function = distinct_by(lambda e: _label(e.description))
    by_department = distinct_by(lambda e: _label(e.department))
    monthly: dict[str, set] = defaultdict(set)
    for event in events:
        monthly[f"{event.year}-{event.month:02}"].add(event.registration)
    cadre_of = {r.registration: r.cadre for r in register if r.registration}
    tables = [
        ResultTable(
            "by_function",
            "Quantidade de professores com gratificação por função",
            ("Gratificação", "Professores"),
            by_function,
            FACULTY_UNIT,
        ),
        ResultTable(
            "by_department",
            "Quantidade de professores distintos com gratificação por departamento",
            ("Departamento", "Professores"),
            by_department,
            FACULTY_UNIT,
        ),
        ResultTable(
            "by_month",
            "Quantidade de professores que receberam gratificações no período",
            ("Competência", "Professores"),
            tuple((k, len(v)) for k, v in sorted(monthly.items())),
            f"{FACULTY_UNIT} no mês; meses não são somados",
        ),
        ResultTable(
            "function_events",
            "Gratificações",
            (
                "Departamento",
                "Depto. Distribuição",
                "Matrícula fictícia",
                "Quadro de Professores",
                "Mês",
                "Ano",
                "Gratificação",
                "Papel",
            ),
            tuple(
                (
                    r.department,
                    r.distribution_department,
                    r.registration,
                    cadre_of.get(r.registration),
                    r.month,
                    r.year,
                    r.description,
                    r.role,
                )
                for r in sorted(
                    events,
                    key=lambda e: (e.year, e.month, e.registration or "", e.description or ""),
                )
            ),
            "linhas da fonte",
        ),
        ResultTable(
            "function_comparison",
            "Gratificações e dupla função por professor",
            ("Matrícula fictícia", "Nome fictício", "Dupla Função", "Registros de gratificação"),
            tuple(
                (
                    r.registration,
                    r.name,
                    _label(r.dual_role),
                    sum(e.registration == r.registration for e in events) if have_events else None,
                )
                for r in register
            ),
            "por professor",
        ),
    ]
    status = "Calculado" if have_events and register_available else "Parcial"
    if have_appointments:
        # Somente a demonstração sintética traz atos e vigências; a fonte institucional não.
        appointments = [
            a
            for a in source.appointments
            if a.registration in registrations
            and a.administrative
            and _as_date(a.start) < last
            and (a.end is None or _as_date(a.end) >= first)
            and (a.end is None or _as_date(a.end) >= _as_date(a.start))
        ]
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
        confirmed = {a.registration for a in appointments}
        simulated = source.policy.synthetic_appointments
        metrics += [
            Metric(
                "Função administrativa com evidência",
                len(confirmed),
                FACULTY_UNIT,
                "Simulação" if simulated else "Calculado",
            ),
            Metric(
                "Professores com papéis simultâneos",
                len({r[0] for r in simultaneous}),
                FACULTY_UNIT,
            ),
        ]
        tables += [
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
        if simulated:
            notes.append(
                "Comprovações e vigências administrativas são cenários gerados "
                "exclusivamente para simulação, sem validade institucional."
            )
            status = "Simulação" if have_events and register_available else "Parcial"
    if register_available and not register:
        status = "Sem dados"
    return _result(
        kind,
        source,
        filters,
        metrics,
        tables,
        notes,
        charts=[
            ChartSpec(
                "by_function",
                "Quantidade de professores com gratificação por função",
                "Gratificação",
                ("Professores",),
                "bar",
            ),
            ChartSpec(
                "by_department",
                "Quantidade de professores distintos com gratificação por departamento",
                "Departamento",
                ("Professores",),
                "bar",
            ),
            ChartSpec(
                "by_month",
                "Quantidade de professores que receberam gratificações no período",
                "Competência",
                ("Professores",),
            ),
        ],
        status=status,
        narrative=(
            "Professores com gratificação no intervalo, por função, departamento e mês, "
            "como na página Análise de Gratificações do painel."
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
    registered = {row.registration for row in source.students if row.registration is not None}
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
        # DAX: sem cadastro não conta; ingresso em branco é comparado como 0 e conta.
        eligible = {
            r
            for r in candidates
            if r in registered
            and (not entry_by_registration.get(r) or min(entry_by_registration[r]) <= period)
        }
        enrolled = len(eligible) if observed and have_history and have_current else None
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
        "Matriculados: MT/MC por período e ingresso do cadastro até o período (B-M-035). "
        "Como no painel, matrícula sem cadastro não conta e ingresso em branco conta.",
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
        r.registration in registered
        and r.status in {"MT", "MC"}
        and r.period in periods
        and not entry_by_registration.get(r.registration)
        for r in history
    ):
        notes.append(
            "Há matrículas com ingresso em branco no cadastro; como no painel, elas contam "
            "entre os matriculados."
        )
    missing = sum(r.registration is None for r in history)
    if missing:
        notes.append(
            f"{missing} registro(s) acadêmico(s) sem matrícula foram excluídos das contagens."
        )
    headers = ("Período", *STUDENT_SERIES)
    tables = [
        ResultTable(
            "students",
            STUDENT_CHART_TITLE,
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
            "Variação de alunos matriculados entre períodos",
            ("De", "Para", "Base", "Atual", "Diferença", "Variação %", "Situação"),
            tuple(changes),
            "matrículas e percentual",
        ),
    ]
    last = rows[-1]
    # Recorte do detalhe por curso, sem somar cursos; ausente vai ao fim e não vira zero.
    tables.append(
        ResultTable(
            "student_courses_latest",
            f"Matriculados por curso em {last[0]}",
            ("Curso", STUDENT_SERIES[0]),
            tuple(
                sorted(
                    ((row[0], row[2]) for row in course_rows if row[1] == last[0]),
                    key=lambda item: (item[1] is None, -(item[1] or 0), item[0]),
                )
            ),
            "matrículas acadêmicas distintas",
            "Cada curso é contado separadamente; as barras não devem ser somadas.",
        )
    )
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
        [
            ChartSpec("students", STUDENT_CHART_TITLE, "Período", headers[1:]),
            *(
                [
                    ChartSpec(
                        "student_courses_latest",
                        f"Matriculados por curso em {last[0]}",
                        "Curso",
                        (STUDENT_SERIES[0],),
                        "bar",
                    )
                ]
                if len(courses) > 1
                else []
            ),
        ],
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
        AnalysisKind.COMPARISON: calculate_comparison,
        AnalysisKind.HISTORY: calculate_history,
        AnalysisKind.WORKLOAD: calculate_workload,
        AnalysisKind.FUNCTIONS: calculate_functions,
        AnalysisKind.STUDENTS: calculate_students,
    }
    return calculators[kind](source, filters)
