"""Catálogo fechado de conferências descritivas; sem IA ou decisões de pessoal."""

from collections import Counter
from dataclasses import dataclass, replace

from vrac.analyses.academic_data import AcademicSource


@dataclass(frozen=True, slots=True)
class QualityCheck:
    identifier: str
    description: str
    count: int | None
    level: str
    consequence: str


def inspect_source(source: AcademicSource) -> tuple[QualityCheck, ...]:
    register_missing = sum(not r.registration for r in source.faculty.register)
    history_missing = sum(not r.person_key or r.reference_date is None for r in source.history)
    lot_keys = Counter((r.registration, r.reference_date) for r in source.history)
    repeated_lots = sum(v > 1 for v in lot_keys.values())
    student_keys = Counter((r.registration, r.period) for r in source.student_history)
    repeated_academic = sum(v > 1 for v in student_keys.values())
    student_ids = {r.registration for r in source.students if r.registration is not None}
    scholarship_unknown = sum(r.registration not in student_ids for r in source.scholarships)
    missing_academic = sum(r.registration is None for r in source.student_history)
    unknown_cadre = sum(not r.cadre for r in source.faculty.register)
    workload_missing = sum(r.real_hours is None for r in source.workloads)
    negative_hours = sum(r.real_hours is not None and r.real_hours < 0 for r in source.workloads)
    invalid_appointments = sum(
        r.end is not None and r.end.isoformat()[:10] < r.start.isoformat()[:10]
        for r in source.appointments
    )
    checks = (
        QualityCheck(
            "C01",
            "Cadastro sem matrícula funcional",
            register_missing,
            "Atenção",
            "Registros sem chave ficam fora das contagens; não criar identidade.",
        ),
        QualityCheck(
            "C02",
            "Histórico sem pessoa ou data",
            history_missing,
            "Atenção",
            "Linhas inválidas ficam fora da presença semestral e geram aviso.",
        ),
        QualityCheck(
            "C03",
            "Matrícula/competência com mais de uma linha de folha",
            repeated_lots,
            "Informação",
            "A presença é recalculada por pessoas; não somar lotes ou meses.",
        ),
        QualityCheck(
            "C04",
            "Matrícula/período acadêmico com múltiplos registros",
            repeated_academic,
            "Informação",
            "As séries contam matrículas distintas e preservam a regra de situação.",
        ),
        QualityCheck(
            "C05",
            "Bolsa sem cadastro acadêmico no recorte",
            scholarship_unknown,
            "Atenção",
            "O vínculo é conferido na população elegível; linhas de bolsa não são alunos.",
        ),
        QualityCheck(
            "C06",
            "Histórico acadêmico sem matrícula",
            missing_academic,
            "Atenção",
            "Não contar chave ausente como matrícula ou zero.",
        ),
        QualityCheck(
            "C07",
            "Quadro ausente no cadastro",
            unknown_cadre,
            "Atenção",
            "QP não é concluído com classificação incompleta.",
        ),
        QualityCheck(
            "C08",
            "Horas Reais nulas na fonte",
            workload_missing,
            "Atenção",
            "Nulo permanece ausente; somas com parcelas nulas são parciais.",
        ),
        QualityCheck(
            "C09",
            "Horas Reais negativas",
            negative_hours,
            "Atenção",
            "Conferir o valor de origem; não emitir julgamento de produtividade.",
        ),
        QualityCheck(
            "C10",
            "Vigência com fim anterior ao início",
            invalid_appointments,
            "Atenção",
            "Vigências inválidas não comprovam simultaneidade.",
        ),
    )
    dependencies = (
        "register",
        "history",
        "history",
        "student_history",
        "students",
        "student_history",
        "register",
        "workloads",
        "workloads",
        "appointments",
    )
    return tuple(
        c
        if dependency in source.available
        and (c.identifier != "C05" or "scholarships" in source.available)
        else replace(
            c,
            count=None,
            level="Fonte indisponível",
            consequence="Conferência indisponível neste snapshot.",
        )
        for c, dependency in zip(checks, dependencies, strict=True)
    )
