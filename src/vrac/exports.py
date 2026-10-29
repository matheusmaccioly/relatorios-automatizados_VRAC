"""Exportação inicial do resultado exibido, com filtros, avisos e versões.

A exportação não recalcula: serializa exatamente o resultado que está na tela. Toda
linha carrega o recorte e os avisos, para que um número não circule separado de suas
limitações. Texto que o Excel interpretaria como fórmula é neutralizado.
"""

import csv
import json
from io import StringIO

from vrac.analyses.contracts import AnalysisResult, Availability, ResultStatus
from vrac.analyses.rules import FacultyRule
from vrac.presentation import filters_table, result_table
from vrac.settings import DataMode

#: Excel em português usa ponto e vírgula como separador de lista.
CSV_DELIMITER = ";"
#: BOM para o Excel reconhecer UTF-8 sem conversão manual.
CSV_ENCODING = "utf-8-sig"

_RISKY_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


class ExportBlocked(PermissionError):
    """Exportação negada; não revelar origem física ou infraestrutura."""


def _safe_cell(value: object) -> str:
    """Neutralizar fórmula sem alterar números já validados pelo contrato."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "sim" if value else "não"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text.startswith(_RISKY_PREFIXES):
        return f"'{text}"
    return text


def _guard(result: AnalysisResult) -> None:
    if result.status == ResultStatus.BLOCKED:
        raise ExportBlocked("Resultado bloqueado não gera exportação: não há números a exportar.")
    if result.request.mode == DataMode.REAL:
        raise ExportBlocked("Exportação de dados reais depende de autorização institucional.")


def result_csv(result: AnalysisResult, rule: FacultyRule) -> bytes:
    """CSV autoexplicativo: cada linha repete recorte, versões e avisos."""
    _guard(result)
    context = {
        f"Filtro · {row['Filtro']}": row["Valor"]
        for row in filters_table(result.request, rule).to_dict("records")
    }
    warnings = " | ".join(result.warnings)
    table = result_table(result)
    header = [
        *table.columns,
        *context,
        "Situação do resultado",
        "Versão do catálogo",
        "Versão da regra",
        "Execução",
        "Calculado em",
        "Dados sintéticos",
        "Avisos",
    ]
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, delimiter=CSV_DELIMITER, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([_safe_cell(column) for column in header])
    for row in table.to_dict("records"):
        writer.writerow(
            [
                *(_safe_cell(row[column]) for column in table.columns),
                *(_safe_cell(value) for value in context.values()),
                _safe_cell(result.status.value),
                _safe_cell(result.catalog_version),
                _safe_cell(result.rule_version),
                _safe_cell(result.execution_id),
                _safe_cell(result.created_at.isoformat()),
                _safe_cell(result.request.mode == DataMode.SYNTHETIC),
                _safe_cell(warnings),
            ]
        )
    return buffer.getvalue().encode(CSV_ENCODING)


def result_json(result: AnalysisResult, rule: FacultyRule) -> bytes:
    """JSON completo, preservando Decimal como texto e a regra aplicada."""
    _guard(result)
    payload = result.to_dict()
    payload["rule"] = {
        "rule_id": rule.rule_id,
        "rule_version": rule.rule_version,
        "label": rule.label,
        "counting_basis": rule.counting_basis.value,
        "temporal_basis": rule.temporal_basis.value,
        "semantic_variant_id": rule.semantic_variant_id,
        "approval_status": rule.approval.status.value,
        "pending_decisions": list(rule.requires_decisions),
        "limitations": list(rule.limitations),
    }
    payload["availability_legend"] = {item.value: item.name.lower() for item in Availability}
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def export_filename(result: AnalysisResult, extension: str) -> str:
    """Nome previsível, sem nome físico de fonte, departamento real ou credencial."""
    period = result.request.period.identifier.replace(".", "-")
    marker = "sintetico" if result.request.mode == DataMode.SYNTHETIC else "real"
    return f"composicao_docente_{period}_{marker}_{result.execution_id[:8]}.{extension}"
