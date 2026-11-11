"""R01 Situação geral do departamento: reprodução da página "Análise Geral" do painel.

Regras reproduzidas (D-022), com referência à documentação semântica local:
- Cadastro atual `V_FUNCIONARIO`; unidade de contagem: matrícula funcional (`MATRICULA`).
- Cartão e quadro: contagem distinta de matrículas (agregação 2 dos visuais).
- Categoria funcional (`CARGO`): contagem de linhas com matrícula (agregação 5).
- Horas Reais (Semestre Atual): soma de `HORAS_REAIS` no maior `SEMESTRE` do contexto,
  que na linha da tabela é a própria matrícula (A-M-009/A-M-010); ligação
  `V_HORAS_REAIS_PROF[MATRICULA_PRF]` → `V_FUNCIONARIO[MATRICULAINT]`.
- Status CH (Semáforo): coluna calculada A-CC-007, com comparação de texto sem
  diferenciar maiúsculas, como no motor do painel; Resultado CH Texto (A-M-012)
  usa o status único do semestre atual.

- Filtro de página da Análise Geral: quadro diferente de vazio, ADMINISTRATIVO,
  ESTAGIÁRIO e MONITOR (inventário do PBIP em base/, 11/11/2026).
Nenhuma conclusão sobre suficiência de pessoal, produtividade ou contratação.
"""

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from enum import StrEnum

NOT_INFORMED = "Não informado"
UNIT_LABEL = "matrículas funcionais distintas"
# Filtro de página bloqueado da Análise Geral do painel: NOT QUADRO IN {null, ...}.
NON_FACULTY_CADRES = frozenset({"ADMINISTRATIVO", "ESTAGIÁRIO", "MONITOR"})
PAGE_FILTER_NOTE = (
    "Como no painel, a população exclui quadro vazio, ADMINISTRATIVO, ESTAGIÁRIO e MONITOR."
)


def is_faculty_cadre(cadre: str | None) -> bool:
    """Reproduz o filtro de página do painel; quadro vazio também fica fora."""
    return bool(cadre and cadre.strip()) and cadre.strip().upper() not in NON_FACULTY_CADRES


class OverviewStatus(StrEnum):
    VALID = "valid"
    PARTIAL = "partial"
    EMPTY_SOURCE = "empty_source"
    EMPTY_FILTERS = "empty_filters"


@dataclass(frozen=True, slots=True)
class RegisterRow:
    """Uma linha do cadastro atual. `person_key` serve só para avisos; nunca é exibido."""

    department: str | None
    registration: str | None
    registration_int: int | None
    person_key: str | None
    name: str | None
    cadre: str | None
    category: str | None
    status: str | None
    dual_role: str | None
    extraordinary: str | None
    weekly_hours: float | None
    tenure_years: float | None
    degree: str | None
    link_key: str | None = None


@dataclass(frozen=True, slots=True)
class RealHoursRow:
    registration_int: int | None
    semester: int | None
    hours: float | None
    cadre: str | None
    link_key: str | None = None


@dataclass(frozen=True, slots=True)
class FacultySource:
    """Recorte de um departamento já lido da origem, sem filtros da tela aplicados."""

    department: str
    register: tuple[RegisterRow, ...]
    real_hours: tuple[RealHoursRow, ...]
    source: str
    version: str
    real_hours_available: bool = True
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OverviewFilters:
    """Seleções fechadas; `None` significa todos os valores do cadastro do departamento."""

    cadres: frozenset[str] | None = None
    categories: frozenset[str] | None = None
    statuses: frozenset[str] | None = None
    dual_roles: frozenset[str] | None = None


@dataclass(frozen=True, slots=True)
class FilterOptions:
    cadres: tuple[str, ...]
    categories: tuple[str, ...]
    statuses: tuple[str, ...]
    dual_roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DetailRow:
    department: str | None
    registration: str | None
    name: str | None
    cadre: str | None
    category: str | None
    weekly_hours: float | None
    real_hours: float | None
    real_hours_semester: str | None
    indicator: str | None
    degree: str | None
    tenure_years: float | None
    dual_role: str | None
    extraordinary: str | None
    hours_state: str = "Valor informado"


@dataclass(frozen=True, slots=True)
class FacultyOverview:
    department: str
    status: OverviewStatus
    total: int | None
    by_cadre: tuple[tuple[str, int], ...]
    by_category: tuple[tuple[str, int], ...]
    detail: tuple[DetailRow, ...]
    warnings: tuple[str, ...]
    narrative: str
    source: str
    version: str
    filters: OverviewFilters = field(default_factory=OverviewFilters)
    by_department: tuple[tuple[str, int], ...] = ()
    fingerprint: str = ""


def semester_label(semester: int | None) -> str | None:
    if semester is None:
        return None
    return f"{semester // 10}.{semester % 10}"


def _same_text(value: str | None, expected: str) -> bool:
    # O motor do painel compara textos sem diferenciar maiúsculas e minúsculas.
    return value is not None and value.casefold() == expected.casefold()


def semaphore_status(hours: float | None, cadre: str | None) -> str:
    """Reprodução literal da coluna calculada Status CH (Semáforo), A-CC-007."""
    principal = _same_text(cadre, "PRINCIPAL")
    integral = _same_text(cadre, "COMPLEMENTAR TEMPO INTEGRAL")
    partial = _same_text(cadre, "COMPLEMENTAR TEMPO PARCIAL")
    if hours is None:
        return "Sem CH (em branco)"
    if hours == 0:
        return "Sem alocação (CH = 0)"
    if not (principal or integral or partial):
        return "Sem regra definida"
    if principal and hours < 7:
        return "Abaixo do necessário"
    if principal and hours > 44:
        return "Acima do necessário"
    if not principal and hours > 30:
        return "Muito acima (verificar coord./múltiplas turmas)"
    if integral and hours < 16:
        return "Abaixo do necessário"
    if integral and hours > 20:
        return "Acima do necessário"
    if partial and hours < 12:
        return "Abaixo do necessário"
    if partial and hours > 15:
        return "Acima do necessário"
    return "Dentro do esperado"


def _link_key(row: RegisterRow | RealHoursRow) -> int | str | None:
    """Identidade opaca institucional ou matrícula numérica da origem sintética."""
    return row.link_key if row.link_key is not None else row.registration_int


def current_real_hours(
    rows: Iterable[RealHoursRow],
) -> dict[int | str, tuple[float | None, int, str | None]]:
    """Por matrícula: (Horas Reais do semestre atual, semestre, Resultado CH Texto)."""
    by_registration: dict[int | str, list[RealHoursRow]] = defaultdict(list)
    for row in rows:
        key = _link_key(row)
        if key is not None and row.semester is not None:
            by_registration[key].append(row)
    result: dict[int | str, tuple[float | None, int, str | None]] = {}
    for registration, items in by_registration.items():
        semester = max(item.semester for item in items if item.semester is not None)
        current = [item for item in items if item.semester == semester]
        values = [item.hours for item in current if item.hours is not None]
        # SUM de valores em branco resulta em branco, não em zero.
        hours = sum(values) if values else None
        statuses = {semaphore_status(item.hours, item.cadre) for item in current}
        # SELECTEDVALUE: somente um status distinto produz texto.
        indicator = next(iter(statuses)) if len(statuses) == 1 else None
        result[registration] = (hours, semester, indicator)
    return result


def _label(value: str | None) -> str:
    return value if value not in (None, "") else NOT_INFORMED


def filter_options(source: FacultySource) -> FilterOptions:
    rows = [row for row in source.register if is_faculty_cadre(row.cadre)]

    def values(attribute: str) -> tuple[str, ...]:
        return tuple(sorted({_label(getattr(row, attribute)) for row in rows}))

    return FilterOptions(values("cadre"), values("category"), values("status"), values("dual_role"))


def _accepts(selected: frozenset[str] | None, value: str | None) -> bool:
    return selected is None or _label(value) in selected


def _describe(selected: frozenset[str] | None) -> str:
    return "todos" if selected is None else ", ".join(sorted(selected)) or "nenhum"


def describe_filters(filters: OverviewFilters) -> tuple[tuple[str, str], ...]:
    return (
        ("Quadro", _describe(filters.cadres)),
        ("Categoria funcional", _describe(filters.categories)),
        ("Situação", _describe(filters.statuses)),
        ("Dupla função", _describe(filters.dual_roles)),
    )


def _validate_selection(name: str, selected: frozenset[str] | None, allowed: Sequence[str]) -> None:
    if selected is not None and not selected <= set(allowed):
        raise ValueError(f"Seleção inválida para {name}.")


def compute_overview(source: FacultySource, filters: OverviewFilters) -> FacultyOverview:
    """Calcular o resultado sem acesso a dados; mesma entrada produz a mesma saída."""
    options = filter_options(source)
    fingerprint = hashlib.sha256(json.dumps(asdict(source), sort_keys=True).encode()).hexdigest()
    _validate_selection("quadro", filters.cadres, options.cadres)
    _validate_selection("categoria funcional", filters.categories, options.categories)
    _validate_selection("situação", filters.statuses, options.statuses)
    _validate_selection("dupla função", filters.dual_roles, options.dual_roles)

    def result(status: OverviewStatus, narrative: str, warnings: tuple[str, ...] = ()):
        return FacultyOverview(
            source.department,
            status,
            None,
            (),
            (),
            (),
            warnings,
            narrative,
            source.source,
            source.version,
            filters,
            fingerprint=fingerprint,
        )

    if not source.register:
        return result(
            OverviewStatus.EMPTY_SOURCE,
            f"Não há vínculos no cadastro para o departamento {source.department}. "
            "Ausência de registros não significa zero.",
        )
    eligible = [
        row
        for row in source.register
        if is_faculty_cadre(row.cadre)
        and _accepts(filters.cadres, row.cadre)
        and _accepts(filters.categories, row.category)
        and _accepts(filters.statuses, row.status)
        and _accepts(filters.dual_roles, row.dual_role)
    ]
    if not eligible:
        return result(
            OverviewStatus.EMPTY_FILTERS,
            "Nenhum vínculo do cadastro atende aos filtros escolhidos. "
            "Ausência de registros não significa zero.",
        )

    warnings: list[str] = [PAGE_FILTER_NOTE, *source.notes]
    with_registration = [row for row in eligible if row.registration not in (None, "")]
    missing_registration = len(eligible) - len(with_registration)
    if missing_registration:
        warnings.append(
            f"{missing_registration} linha(s) do cadastro sem matrícula não entram nas "
            "contagens; verificar a origem."
        )
    total = len({row.registration for row in with_registration})

    cadre_sets: dict[str, set[str]] = defaultdict(set)
    for row in with_registration:
        cadre_sets[_label(row.cadre)].add(row.registration or "")
    by_cadre = tuple(sorted(((k, len(v)) for k, v in cadre_sets.items()), key=_order))
    by_category = tuple(
        sorted(Counter(_label(row.category) for row in with_registration).items(), key=_order)
    )
    if sum(count for _, count in by_cadre) != total:
        warnings.append(
            "Há matrículas com mais de um quadro no cadastro; as barras por quadro "
            "se sobrepõem e não somam o total."
        )
    if NOT_INFORMED in dict(by_cadre) or NOT_INFORMED in dict(by_category):
        warnings.append(
            "Há vínculos sem quadro ou categoria informados; aparecem como "
            f"“{NOT_INFORMED}” e não foram reclassificados."
        )

    registrations_by_person: dict[str, set[str]] = defaultdict(set)
    for row in with_registration:
        if row.person_key:
            registrations_by_person[row.person_key].add(row.registration or "")
    multiple = sum(1 for regs in registrations_by_person.values() if len(regs) > 1)
    if multiple:
        warnings.append(
            f"{multiple} pessoa(s) aparece(m) com mais de um vínculo. O total conta "
            "matrículas funcionais, como o painel, e não pessoas distintas."
        )

    hours = current_real_hours(source.real_hours) if source.real_hours_available else {}
    if not source.real_hours_available:
        warnings.append(
            "Fonte de Horas Reais indisponível: somente as cargas e seus resultados "
            "na lista ficam indisponíveis; a composição cadastral continua calculada."
        )
    detail = tuple(
        DetailRow(
            row.department,
            row.registration,
            row.name,
            row.cadre,
            row.category,
            row.weekly_hours,
            *_hours_columns(None if _link_key(row) is None else hours.get(_link_key(row))),
            row.degree,
            row.tenure_years,
            row.dual_role,
            row.extraordinary,
            "Fonte indisponível"
            if not source.real_hours_available
            else "Sem registro"
            if _link_key(row) not in hours
            else "Nulo na fonte"
            if hours[_link_key(row)][0] is None
            else "Valor informado",
        )
        for row in sorted(eligible, key=lambda r: (r.registration or "", r.name or ""))
    )
    if any(item.indicator == "Sem regra definida" for item in detail):
        warnings.append(
            "Indicador de CH “Sem regra definida”: a regra do painel reconhece os quadros "
            "PRINCIPAL, COMPLEMENTAR TEMPO INTEGRAL e COMPLEMENTAR TEMPO PARCIAL; outros "
            "nomes de quadro não recebem faixa. Nenhuma equivalência foi presumida. O "
            "resultado não avalia produtividade."
        )
    if any(_link_key(row) not in hours for row in eligible):
        warnings.append(
            "Há vínculos sem registro na fonte de Horas Reais; essas células aparecem como "
            "ausentes, não como zero."
        )

    narrative = (
        f"No cadastro atual, o departamento {source.department} apresenta {total} "
        f"{UNIT_LABEL} na população selecionada (quadro: {_describe(filters.cadres)}; "
        f"categoria: {_describe(filters.categories)}; situação: {_describe(filters.statuses)}; "
        f"dupla função: {_describe(filters.dual_roles)}). A distribuição por quadro e por "
        "categoria funcional está nas tabelas."
    )
    return FacultyOverview(
        source.department,
        OverviewStatus.PARTIAL if not source.real_hours_available else OverviewStatus.VALID,
        total,
        by_cadre,
        by_category,
        detail,
        tuple(warnings),
        narrative,
        source.source,
        source.version,
        filters,
        tuple(sorted(Counter(_label(row.department) for row in with_registration).items())),
        fingerprint,
    )


def _order(item: tuple[str, int]) -> tuple[bool, int, str]:
    # Maior quantidade primeiro; "Não informado" sempre ao final.
    return (item[0] == NOT_INFORMED, -item[1], item[0])


def _hours_columns(
    value: tuple[float | None, int, str | None] | None,
) -> tuple[float | None, str | None, str | None]:
    if value is None:
        return (None, None, None)
    hours, semester, indicator = value
    return (hours, semester_label(semester), indicator)
