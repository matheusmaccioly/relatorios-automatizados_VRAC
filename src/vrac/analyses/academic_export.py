"""Exportar os roteiros calculados, com filtros e proveniência em cada tabela."""

import csv
import io
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import datetime
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from vrac.analyses.academic import CalculatedAnalysis, ResultTable, export_folder
from vrac.analyses.export import safe_cell
from vrac.provenance import INSTITUTIONAL_SOURCE, is_institutional, nature

FILTER_LABELS = {
    "first_period": "Semestre inicial",
    "last_period": "Semestre final",
    "workload_period": "Semestre da carga",
    "group_a_cadres": "Grupo A — quadros",
    "courses": "Cursos",
    "cadres": "Quadro",
    "categories": "Categoria Funcional",
    "qualifications": "Habilitações",
    "shifts": "Turnos",
    "levels": "Níveis",
    "entry_kinds": "Formas de ingresso",
    "group_a_categories": "Grupo A — categorias",
    "group_a_name": "Grupo A — nome",
    "group_b_cadres": "Grupo B — quadros",
    "group_b_categories": "Grupo B — categorias",
    "group_b_name": "Grupo B — nome",
    "statuses": "Situação",
}


def result_context(result: CalculatedAnalysis, context: Mapping[str, str] | None) -> dict[str, str]:
    return dict(context or {}) | {
        "Origem": result.source,
        "Versão dos dados": result.version,
        "Snapshot": result.fingerprint,
        "Versão do cálculo": result.calculation_version,
    }


def table_csv(
    result: CalculatedAnalysis,
    table: ResultTable,
    generated_at: datetime,
    context: Mapping[str, str] | None = None,
) -> bytes:
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter=";", lineterminator="\r\n")
    metadata = [
        ("Identificação", nature(result.source)),
        ("Análise", f"{result.kind}: {result.title}"),
        ("Tabela", table.title),
        ("Departamento", result.department),
        ("Situação", result.status),
        ("Origem", result.source),
        ("Versão dos dados", result.version),
        ("Versão do cálculo", result.calculation_version),
        ("Snapshot", result.fingerprint),
        ("Unidade", table.unit),
        ("Gerado em UTC", generated_at.isoformat()),
    ]
    metadata += [
        (f"Filtro: {FILTER_LABELS[key]}", ", ".join(value) if isinstance(value, tuple) else value)
        for key, value in asdict(result.filters).items()
    ]
    metadata += [("Aviso", value) for value in result.notes]
    if context is not None:
        metadata += [
            (f"Contexto: {key}", value) for key, value in result_context(result, context).items()
        ]
    if table.note:
        metadata.append(("Limitação da tabela", table.note))
    for row in (*metadata, (), table.columns, *table.rows):
        writer.writerow([safe_cell(value) for value in row])
    return stream.getvalue().encode("utf-8-sig")


def summary_table(result: CalculatedAnalysis) -> ResultTable:
    return ResultTable(
        "summary",
        "Resultados calculados",
        ("Resultado", "Valor", "Unidade", "Situação"),
        tuple((m.label, m.value, m.unit, m.status) for m in result.metrics),
        "por resultado",
    )


def report_zip(
    results: Sequence[CalculatedAnalysis],
    generated_at: datetime,
    images: Mapping[str, bytes] | None = None,
    additional_files: Mapping[str, bytes] | None = None,
    context: Mapping[str, str] | None = None,
    additional_analyses: Sequence[Mapping[str, str]] = (),
) -> bytes:
    """Pacote fechado das análises solicitadas, sem persistir registros no servidor."""
    stream = io.BytesIO()
    with ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:

        def write(name: str, data: bytes) -> None:
            if ".." in name or name.startswith(("/", "\\")) or "\\" in name:
                raise ValueError("Nome inválido no pacote de exportação.")
            info = ZipInfo(name, date_time=generated_at.timetuple()[:6])
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)

        origins = {r.source for r in results} | {
            item.get("source", "") for item in additional_analyses
        }
        origins.add((context or {}).get("Origem", ""))
        origins.discard("")
        if any(is_institutional(o) for o in origins) and any(
            not is_institutional(o) for o in origins
        ):
            raise ValueError("Origens não podem ser misturadas no mesmo pacote.")
        institutional = any(is_institutional(o) for o in origins)
        source_label = INSTITUTIONAL_SOURCE if institutional else ""
        manifest = {
            "synthetic": not institutional,
            "origin": "institucional_pseudonimizada" if institutional else "synthetic",
            "validity": nature(source_label),
            "generated_at_utc": generated_at.isoformat(),
            "context": dict(context or {}),
            "analyses": [asdict(r) for r in results],
            "additional_analyses": [dict(item) for item in additional_analyses],
        }
        write("manifesto.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
        write(
            "LEIA-ME.txt",
            (
                nature(source_label)
                + "\n"
                + "Cada CSV inclui filtros, unidades, avisos e identificação do snapshot.\n"
                "Ausente não é zero. Estoques acadêmicos e contagens mensais não são somados.\n"
                "QP é comparação exploratória; unidades e vigências "
                "dependem das evidências da origem.\n"
                "Nenhum resultado recomenda contratação, avalia produtividade "
                "ou confirma regra institucional.\n"
            ).encode(),
        )
        for result in results:
            for table in (summary_table(result), *result.tables):
                write(
                    f"{export_folder(result.kind)}/{table.key}.csv",
                    table_csv(result, table, generated_at, context),
                )
        for name, data in (images or {}).items():
            write(name, data)
        for name, data in (additional_files or {}).items():
            write(name, data)
    return stream.getvalue()
