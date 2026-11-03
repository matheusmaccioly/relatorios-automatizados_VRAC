"""Conferência manual R06 no PostgreSQL sintético existente; nunca inicia ou carrega banco."""

import argparse
import csv
import hashlib
import io
import json
from dataclasses import asdict, replace
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate, period_code
from vrac.analyses.academic_data import ALL_DEPARTMENTS, AcademicSource
from vrac.analyses.export import safe_cell
from vrac.db.synthetic_postgres import (
    Query,
    _connection,
    _options,
    _query,
    _read_academic_source,
)
from vrac.demo_data import DemoDataError
from vrac.settings import DemoSource, Settings

if TYPE_CHECKING:
    from psycopg import Connection

DIMENSIONS = {
    "courses": "course",
    "qualifications": "qualification",
    "shifts": "shift",
    "levels": "level",
    "entry_kinds": "entry_kind",
}
POPULATIONS = ("Matriculados", "Bolsistas matriculados", "Formados", "Ingressantes")
REFERENCE_FILES = (
    "reconcile_students_scope",
    "reconcile_students_counts",
    "reconcile_students_scholarships",
)


def reference_sql(*, scholarships: bool = False) -> str:
    """Duas consultas fechadas de referência; nenhuma interpolação de filtros em SQL."""
    suffix = REFERENCE_FILES[2 if scholarships else 1]
    return "\n".join(_sql_file(name) for name in (REFERENCE_FILES[0], suffix))


def _sql_file(name: str) -> str:
    resource = files("vrac").joinpath("sql", "synthetic_demo", f"{name}.sql")
    if resource.is_file():
        return resource.read_text(encoding="utf-8")
    root = Path(__file__).resolve().parents[3] / "sql" / "synthetic_demo"
    return (root / f"{name}.sql").read_text(encoding="utf-8")


def reference_parameters(
    departments: tuple[str, ...], filters: AnalysisFilters, period: str, course: str | None
) -> dict[str, object]:
    selections = {"departments": departments}
    selections.update({key: getattr(filters, key) for key in DIMENSIONS})
    return {
        **{
            key: json.dumps({value: value for value in values})
            for key, values in selections.items()
        },
        "period": period_code(period),
        "course": course,
    }


def scenarios(source: AcademicSource) -> tuple[tuple[str, AnalysisFilters], ...]:
    """Seleções individuais, múltiplas e combinação observada, limitadas à base lida."""
    base = AnalysisFilters(source.periods[0], source.periods[-1], source.periods[-1])
    result = [("Sem filtros acadêmicos", base)]
    rows = (*source.students, *source.student_history)
    for key, field in DIMENSIONS.items():
        values = sorted({getattr(row, field) or "Não informado" for row in rows})
        result.extend((f"{key}: {value}", replace(base, **{key: (value,)})) for value in values)
        if len(values) > 1:
            result.append((f"{key}: seleção múltipla", replace(base, **{key: tuple(values[:2])})))
    if rows:
        row = rows[0]
        selection = {
            key: (getattr(row, field) or "Não informado",) for key, field in DIMENSIONS.items()
        }
        result.append(("Combinação das cinco dimensões", replace(base, **selection)))
    if len(source.periods) > 1:
        result.append(("Intervalo final", replace(base, first_period=source.periods[-2])))
    if len(result) > 100:
        raise DemoDataError("A conferência excede 100 cenários por recorte; revisar a rotina.")
    return tuple(result)


def compare_values(expected: int | float | None, obtained: int | float | None) -> dict:
    return {
        "esperado": expected,
        "obtido": obtained,
        "diferenca": obtained - expected if obtained is not None and expected is not None else None,
        "situacao": ("Ausente em ambas" if expected is None else "Confere")
        if expected == obtained
        else "Divergente",
    }


def reconcile_source(
    connection: "Connection",
    source: AcademicSource,
    departments: tuple[str, ...],
    filters: AnalysisFilters,
    scenario: str,
) -> list[dict]:
    """Obtido usa produção; esperado usa agregações SQL independentes no mesmo snapshot."""
    result = calculate(AnalysisKind.STUDENTS, source, filters)
    tables = {table.key: table for table in result.tables}
    records = []
    independent_totals = {}
    for key in ("students", "student_courses"):
        if key not in tables:
            continue
        for row in tables[key].rows:
            course, period, amounts = (
                (None, row[0], row[1:]) if key == "students" else (row[0], row[1], row[2:])
            )
            parameters = reference_parameters(departments, filters, period, course)
            expected, pending = {}, {}
            for scholarships in (False, True):
                populations = (
                    (POPULATIONS[1],)
                    if scholarships
                    else (POPULATIONS[0], POPULATIONS[2], POPULATIONS[3])
                )
                try:
                    with connection.transaction(), connection.cursor() as cursor:
                        cursor.execute(reference_sql(scholarships=scholarships), parameters)
                        expected.update(cursor.fetchone())
                except Exception:
                    # Nunca exportar a exceção do driver, SQL, paths ou credenciais.
                    pending.update(dict.fromkeys(populations, "Referência SQL indisponível"))
            context = {
                "cenario": scenario,
                "departamento": source.department,
                "departamentos_efetivos": departments,
                "centro": "Centro não informado",
                "filtros": asdict(filters),
                "periodo": period,
                "curso": course,
                "fonte": source.faculty.source,
                "versao_dados": source.faculty.version,
                "snapshot_conteudo": source.fingerprint,
                "versao_calculo": result.calculation_version,
            }
            for population, obtained in zip(POPULATIONS, amounts, strict=True):
                comparison = compare_values(expected.get(population), obtained)
                if population in pending:
                    comparison["situacao"] = "Pendente: " + pending[population]
                records.append({**context, "populacao": population, **comparison})
            if course is None:
                independent_totals[period] = (
                    expected.get(POPULATIONS[0]),
                    bool(pending.get(POPULATIONS[0])),
                )
    for row in tables["enrollment_change"].rows if "enrollment_change" in tables else ():
        base, base_pending = independent_totals[row[0]]
        current, current_pending = independent_totals[row[1]]
        delta = current - base if base is not None and current is not None else None
        percentage = delta / base * 100 if delta is not None and base != 0 else None
        for population, expected, obtained in (
            ("Diferença de matriculados", delta, row[4]),
            ("Variação percentual de matriculados", percentage, row[5]),
        ):
            comparison = compare_values(expected, obtained)
            if base_pending or current_pending:
                comparison["situacao"] = "Pendente: referência SQL indisponível"
            records.append(
                {
                    **context,
                    "periodo": f"{row[0]} → {row[1]}",
                    "curso": None,
                    "populacao": population,
                    **comparison,
                }
            )
    if not result.tables:
        records.append(
            {"cenario": scenario, "situacao": "Pendente: fontes acadêmicas indisponíveis"}
        )
    return records


def run_postgres() -> dict:
    settings = Settings(demo_source=DemoSource.POSTGRES)
    records, scopes = [], []
    # Leitor existente e referências compartilham conexão/transação REPEATABLE READ.
    with _connection(settings) as (connection, version):
        options = _options(connection)
        with connection.cursor() as cursor:
            cursor.execute(_sql_file("reconcile_students_snapshot"))
            snapshot = dict(cursor.fetchone())
        for department in (ALL_DEPARTMENTS, *options.departments):
            selected = options.departments if department == ALL_DEPARTMENTS else (department,)
            source = _read_academic_source(connection, version, department=department)
            scopes.append(
                {
                    "departamento": department,
                    "snapshot_conteudo": source.fingerprint,
                    "fontes_disponiveis": sorted(source.available),
                    "avisos": source.errors,
                }
            )
            for scenario, filters in scenarios(source):
                records.extend(reconcile_source(connection, source, selected, filters, scenario))
    return {
        "natureza": "DEMONSTRAÇÃO — DADOS SINTÉTICOS; sem validade institucional",
        "evidencia": "PostgreSQL sintético",
        "versao_dados": version,
        "snapshot_postgres": snapshot,
        "recortes": scopes,
        "registros": records,
        "limites": [
            "Centro não informado: projeção PostgreSQL sem relação de centros.",
            "Bolsas por departamento sem vigência temporal; não reconstrói transferências.",
            "Formados FR/TD no cadastro: não reconstitui todos os eventos históricos.",
            "Contagens de matrículas acadêmicas, não pessoas únicas; cursos separados por código.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute", action="store_true", help="Executar leitura sintética explícita."
    )
    parser.add_argument("--output", type=Path, default=Path(".cache/prompt4a-postgres"))
    args = parser.parse_args(argv)
    if not args.execute:
        parser.print_help()
        return 2
    try:
        args.output.mkdir(parents=True, exist_ok=False)
    except OSError:
        print("Use uma pasta de saída nova para preservar as evidências anteriores.")
        return 2
    started = datetime.now(UTC).isoformat()
    try:
        report = run_postgres()
    except DemoDataError:
        report = {
            "evidencia": "PostgreSQL pendente",
            "registros": [],
            "situacao": "Leitura não concluída; confira o ambiente sintético existente. "
            "TLS e validação de certificado preservados; sem fallback.",
        }
    report.update(
        {
            "inicio_utc": started,
            "fim_utc": datetime.now(UTC).isoformat(),
            "sha256_sql_referencia": [
                hashlib.sha256(reference_sql(scholarships=flag).encode()).hexdigest()
                for flag in (False, True)
            ],
            "sha256_sql_leitura": {
                q.value: hashlib.sha256(_query(q).encode()).hexdigest()
                for q in (Query.STUDENTS, Query.STUDENT_HISTORY, Query.SCHOLARSHIPS)
            },
        }
    )
    records = report["registros"]
    complete = bool(records) and all(
        r["situacao"] in {"Confere", "Ausente em ambas"} for r in records
    )
    report["conciliacao_concluida"] = complete
    (args.output / "conciliacao.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if records:
        stream = io.StringIO()
        columns = list(dict.fromkeys(key for row in records for key in row))
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";")
        writer.writeheader()
        for row in records:
            writer.writerow(
                {
                    key: safe_cell(
                        json.dumps(value, ensure_ascii=False)
                        if isinstance(value, (dict, tuple, list))
                        else value
                    )
                    for key, value in row.items()
                }
            )
        (args.output / "conciliacao.csv").write_bytes(stream.getvalue().encode("utf-8-sig"))
    print(
        "Conferência registrada; "
        + ("sem divergências." if complete else "há pendências/divergências.")
    )
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
