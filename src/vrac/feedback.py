"""Registro sintético por sessão, sem conexão a armazenamento operacional."""

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from vrac.analyses.export import safe_cell

CATEGORIES = ("Útil", "Divergência", "Dificuldade", "Sugestão")
OVERVIEW_STATUS = {
    "valid": "Calculado",
    "partial": "Parcial",
    "empty_source": "Sem dados na fonte",
    "empty_filters": "Sem dados no filtro",
}


@dataclass(frozen=True, slots=True)
class Feedback:
    execution_id: str
    analysis: str
    execution_status: str
    execution_at: str
    category: str
    text: str
    created_at: str


def create_feedback(
    execution_id: str,
    analysis: str,
    status: str,
    execution_at: datetime,
    category: str,
    text: str,
    created_at: datetime,
) -> Feedback:
    UUID(execution_id)
    if category not in CATEGORIES or not analysis or not status:
        raise ValueError("Selecione uma categoria e uma execução válida.")
    if execution_at.utcoffset() is None or created_at.utcoffset() is None:
        raise ValueError("As datas devem informar o fuso horário.")
    text = text.strip()
    if len(text) > 1000:
        raise ValueError("O comentário deve ter no máximo 1.000 caracteres.")
    if category != "Útil" and not text:
        raise ValueError("Descreva brevemente o ponto, sem dados pessoais ou acadêmicos.")
    return Feedback(
        execution_id,
        analysis,
        status,
        execution_at.isoformat(),
        category,
        text,
        created_at.isoformat(),
    )


def feedback_csv(records: list[Feedback]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";", lineterminator="\r\n")
    writer.writerow(
        [
            "Execução",
            "Análise",
            "Situação",
            "Cálculo (UTC)",
            "Categoria",
            "Comentário",
            "Registro (UTC)",
        ]
    )
    for item in records:
        writer.writerow(
            [
                safe_cell(value)
                for value in (
                    item.execution_id,
                    item.analysis,
                    item.execution_status,
                    item.execution_at,
                    item.category,
                    item.text,
                    item.created_at,
                )
            ]
        )
    return stream.getvalue().encode("utf-8-sig")
