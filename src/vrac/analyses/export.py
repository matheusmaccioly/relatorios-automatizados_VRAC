"""Exportação CSV da R01 com filtros, origem, unidade e avisos junto dos valores."""

import csv
import io
from datetime import datetime

from vrac.analyses.faculty_overview import (
    QP_BLOCK_REASON,
    UNIT_LABEL,
    FacultyOverview,
    OverviewStatus,
    describe_filters,
)
from vrac.provenance import is_institutional, nature

# Planilhas executam células iniciadas por estes caracteres como fórmulas.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
MISSING = "ausente"


def safe_cell(value: object) -> str:
    if value is None:
        return MISSING
    if isinstance(value, float | int) and not isinstance(value, bool):
        # CSV preserva a precisão; arredondamento de apresentação não altera o arquivo.
        return str(value).replace(".", ",")
    text = str(value)
    # Espaços antes do prefixo também podem ser descartados ao abrir em planilha.
    return (
        "'" + text
        if text.startswith(_FORMULA_PREFIXES) or text.lstrip().startswith(("=", "+", "-", "@"))
        else text
    )


def _write(rows: list[list[object]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerows([[safe_cell(cell) for cell in row] for row in rows])
    # BOM para o Excel em português reconhecer UTF-8.
    return buffer.getvalue().encode("utf-8-sig")


def _header(
    overview: FacultyOverview, generated_at: datetime, context: dict[str, str] | None = None
) -> list[list[object]]:
    rows: list[list[object]] = [
        ["Seção", "Item", "Valor"],
        [
            "Identificação",
            "Natureza",
            nature(overview.source),
        ],
        ["Identificação", "Análise", "R01 Situação geral do departamento"],
        ["Identificação", "Departamento", overview.department],
        ["Identificação", "Referência", "Cadastro atual"],
        ["Identificação", "Unidade", UNIT_LABEL],
        ["Identificação", "Unidade por categoria e departamento", "linhas com matrícula"],
        ["Identificação", "Origem", overview.source],
        ["Identificação", "Versão dos dados", overview.version],
        ["Identificação", "Snapshot", overview.fingerprint],
        ["Identificação", "Gerado em (UTC)", generated_at.strftime("%d/%m/%Y %H:%M:%S")],
    ]
    rows += [["Filtro", name, value] for name, value in describe_filters(overview.filters)]
    rows += [["Contexto", name, value] for name, value in (context or {}).items()]
    rows += [["Aviso", str(index), text] for index, text in enumerate(overview.warnings, 1)]
    return rows


def summary_csv(
    overview: FacultyOverview, generated_at: datetime, context: dict[str, str] | None = None
) -> bytes:
    rows = _header(overview, generated_at, context)
    if overview.status not in {OverviewStatus.VALID, OverviewStatus.PARTIAL}:
        rows.append(["Resultado", "Situação", overview.narrative])
        return _write(rows)
    rows.append(["Resultado", "Total", overview.total])
    rows += [["Por quadro", label, count] for label, count in overview.by_cadre]
    rows += [["Por categoria funcional", label, count] for label, count in overview.by_category]
    rows += [["Por departamento", label, count] for label, count in overview.by_department]
    rows += [
        ["Geral e QP", "Geral", overview.total],
        ["Geral e QP", "QP, demais e participação", "bloqueado — " + QP_BLOCK_REASON],
        ["Texto", "Resumo", overview.narrative],
    ]
    return _write(rows)


DETAIL_COLUMNS = (
    ("department", "Departamento"),
    ("registration", "Matrícula fictícia"),
    ("name", "Nome fictício"),
    ("cadre", "Quadro"),
    ("category", "Categoria funcional"),
    ("weekly_hours", "Carga horária semanal"),
    ("real_hours", "Horas Reais (semestre atual)"),
    ("real_hours_semester", "Semestre das Horas Reais"),
    ("indicator", "Resultado de carga (regra do painel)"),
    ("degree", "Titulação"),
    ("tenure_years", "Tempo de casa (anos)"),
    ("dual_role", "Dupla função"),
    ("extraordinary", "Vínculo extraordinário"),
    ("hours_state", "Estado das Horas Reais"),
)


def detail_csv(
    overview: FacultyOverview, generated_at: datetime, context: dict[str, str] | None = None
) -> bytes:
    rows = _header(overview, generated_at, context)
    rows.append([])
    rows.append(
        [
            "Vínculo pseudonimizado"
            if key == "registration" and is_institutional(overview.source)
            else label
            for key, label in DETAIL_COLUMNS
        ]
    )
    rows += [[getattr(item, key) for key, _ in DETAIL_COLUMNS] for item in overview.detail]
    return _write(rows)
