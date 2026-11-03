"""Conciliação R04 manual, exclusivamente PostgreSQL sintético e leitura."""

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate, period_code
from vrac.analyses.academic_data import ALL_DEPARTMENTS
from vrac.db.synthetic_postgres import Query, _connection, _options, _query, _read_academic_source
from vrac.dev.student_reconciliation import _sql_file, compare_values
from vrac.settings import DemoSource, Settings


def scenarios(source):
    selections = [("Todos os quadros e categorias", (), ())]
    cadres = sorted({r.cadre or "Não informado" for r in source.workloads})
    categories = sorted({r.category or "Não informado" for r in source.workloads})
    selections += [(f"Quadro {v}", (v,), ()) for v in cadres]
    selections += [(f"Categoria {v}", (), (v,)) for v in categories]
    if cadres and categories:
        selections.append(("Quadro e categoria combinados", (cadres[0],), (categories[0],)))
    if len(selections) * len(source.periods) > 500:
        raise ValueError("Limite de cenários de conferência excedido.")
    return [
        (
            name,
            AnalysisFilters(source.periods[0], source.periods[-1], period, cadres=c, categories=k),
        )
        for period in source.periods
        for name, c, k in selections
    ]


def reconcile(connection, source, departments, filters, scenario):
    params = {
        key: json.dumps({x: x for x in values}, ensure_ascii=False)
        for key, values in (
            ("departments", departments),
            ("cadres", filters.cadres),
            ("categories", filters.categories),
        )
    }
    params["semester"] = period_code(filters.workload_period)
    with connection.transaction(), connection.cursor() as cursor:
        cursor.execute(_sql_file("reconcile_workload"), params)
        expected = {row["registration"]: row for row in cursor.fetchall()}
    result = calculate(AnalysisKind.WORKLOAD, source, filters)
    if result.status == "Bloqueado":
        return [{"cenario": scenario, "situacao": "Pendente: fonte dedicada indisponível"}]
    actual = {r[0]: r for r in next(t for t in result.tables if t.key == "workload").rows}
    records = []
    policy = source.policy
    compatible = bool(
        "policy" in source.available
        and policy.synthetic_units
        and policy.real_hours_unit
        and policy.real_hours_unit.strip()
        and policy.real_hours_unit == policy.contracted_hours_unit
    )
    context = {
        "cenario": scenario,
        "departamento": source.department,
        "departamentos_efetivos": departments,
        "filtros": asdict(filters),
        "semestre": filters.workload_period,
        "fonte": source.faculty.source,
        "versao": source.faculty.version,
        "snapshot_conteudo": source.fingerprint,
        "unidade_real": policy.real_hours_unit,
        "unidade_contratada": policy.contracted_hours_unit,
    }
    for reg in sorted(set(expected) | set(actual)):
        ref, row = expected.get(reg), actual.get(reg)
        if ref is None or row is None:
            records.append(
                {
                    **context,
                    "vinculo": reg,
                    "medida": "presença",
                    "esperado": ref is not None,
                    "obtido": row is not None,
                    "diferenca": None,
                    "situacao": "Divergente",
                }
            )
            continue
        hours = ref["hours"]
        if isinstance(hours, Decimal):
            hours = float(hours)
        contracted = ref["contracted"] if ref["contracts"] == 1 else None
        delta = (
            hours - contracted
            if compatible and hours is not None and contracted is not None
            else None
        )
        ratio = (
            hours / contracted * 100
            if compatible and hours is not None and contracted not in (None, 0)
            else None
        )
        coverage = (
            "Nulo na fonte"
            if ref["known"] == 0
            else "Parcial"
            if ref["known"] < ref["parcels"]
            else "Informado"
        )
        for measure, exp, got in (
            ("Horas Reais", hours, row[4]),
            ("Contratada", contracted, row[5]),
            ("Diferença", delta, row[6]),
            ("Razão %", ratio, row[7]),
            ("Cobertura", coverage, row[9]),
        ):
            comparison = (
                compare_values(exp, got)
                if measure != "Cobertura"
                else {
                    "esperado": exp,
                    "obtido": got,
                    "diferenca": None,
                    "situacao": "Confere" if exp == got else "Divergente",
                }
            )
            records.append({**context, "vinculo": reg, "medida": measure, **comparison})
    if not expected and not actual:
        records.append(
            {
                **context,
                "vinculo": "Total",
                "medida": "Vínculos com registro",
                **compare_values(None, result.metrics[0].value),
            }
        )
    else:
        records.append(
            {
                **context,
                "vinculo": "Total",
                "medida": "Vínculos com registro",
                **compare_values(len(expected), result.metrics[0].value),
            }
        )
        values = [r["hours"] for r in expected.values() if r["hours"] is not None]
        records.append(
            {
                **context,
                "vinculo": "Total",
                "medida": "Horas Reais",
                **compare_values(sum(values) if values else None, result.metrics[1].value),
            }
        )
    if "allocations" in source.available:
        selected_regs = set(expected)
        allocation_expected = Counter(
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
            for r in source.allocations
            if r.semester == period_code(filters.workload_period)
            and r.registration in selected_regs
        )
        allocation_actual = Counter(
            next(t for t in result.tables if t.key == "allocation_detail").rows
        )
        for key in allocation_expected.keys() | allocation_actual.keys():
            records.append(
                {
                    **context,
                    "vinculo": key[0],
                    "alocacao": key,
                    "medida": "Linhas de alocação",
                    **compare_values(allocation_expected[key], allocation_actual[key]),
                }
            )
    return records


def run_postgres():
    records, audits = [], []
    with _connection(Settings(demo_source=DemoSource.POSTGRES)) as (connection, version):
        options = _options(connection)
        with connection.cursor() as cursor:
            cursor.execute(_sql_file("reconcile_students_snapshot"))
            snapshot = dict(cursor.fetchone())
        for department in (ALL_DEPARTMENTS, *options.departments):
            selected = options.departments if department == ALL_DEPARTMENTS else (department,)
            source = _read_academic_source(connection, version, department=department)
            for component in ("workloads", "allocations", "policy"):
                if component not in source.available:
                    records.append(
                        {
                            "departamento": department,
                            "situacao": f"Pendente: fonte {component} indisponível",
                        }
                    )
            for period in source.periods:
                params = {
                    "departments": json.dumps({x: x for x in selected}),
                    "semester": period_code(period),
                }
                try:
                    with connection.transaction(), connection.cursor() as cursor:
                        cursor.execute(_sql_file("reconcile_workload_cardinality"), params)
                        audit = dict(cursor.fetchone())
                    audits.append({"departamento": department, "semestre": period, **audit})
                except Exception:
                    audits.append(
                        {
                            "departamento": department,
                            "semestre": period,
                            "pendente": "Auditoria de cardinalidade indisponível",
                        }
                    )
            for name, filters in scenarios(source):
                try:
                    records.extend(reconcile(connection, source, selected, filters, name))
                except Exception:
                    records.append(
                        {
                            "cenario": name,
                            "departamento": department,
                            "semestre": filters.workload_period,
                            "situacao": "Pendente: referência indisponível",
                        }
                    )
    return {
        "evidencia": "PostgreSQL sintético",
        "snapshot_postgres": snapshot,
        "versao_dados": version,
        "registros": records,
        "cardinalidade": audits,
        "limites": [
            "Alocações sem vínculo no recorte podem pertencer a outros departamentos.",
            "Parcelas múltiplas não comprovam duplicação ilegítima.",
            "Categoria do cadastro atual; sem validade institucional.",
            "A referência numérica não concilia indicadores ou cada linha de alocação; "
            "essa revisão permanece separada.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(".cache/prompt4b-postgres"))
    args = parser.parse_args(argv)
    if not args.execute:
        parser.print_help()
        return 2
    try:
        args.output.mkdir(parents=True, exist_ok=False)
    except OSError:
        print("Use uma pasta de saída nova para preservar evidências.")
        return 2
    start = datetime.now(UTC).isoformat()
    try:
        report = run_postgres()
    except Exception:
        report = {
            "evidencia": "PostgreSQL pendente",
            "registros": [],
            "cardinalidade": [],
            "situacao": "Leitura não concluída; TLS preservado, sem fallback.",
        }
    report.update(
        {
            "inicio_utc": start,
            "fim_utc": datetime.now(UTC).isoformat(),
            "natureza": "DEMONSTRAÇÃO — DADOS SINTÉTICOS",
            "sha256_sql": {
                name: hashlib.sha256(_sql_file(name).encode()).hexdigest()
                for name in (
                    "reconcile_workload",
                    "reconcile_workload_cardinality",
                    "reconcile_students_snapshot",
                )
            },
            "sha256_leitura": {
                q.value: hashlib.sha256(_query(q).encode()).hexdigest()
                for q in (Query.WORKLOADS, Query.TEACHING_ALLOCATIONS, Query.POLICY)
            },
        }
    )
    complete = bool(report["registros"]) and all(
        r["situacao"] in {"Confere", "Ausente em ambas"} for r in report["registros"]
    )
    complete &= bool(report["cardinalidade"]) and all(
        not a.get("pendente")
        and not a.get("horas_cadastro_multiplo")
        and not a.get("alocacoes_multiplos_destinos")
        and a.get("horas_origem") == a.get("horas_projecao")
        and a.get("alocacoes_com_vinculo") == a.get("alocacoes_projecao")
        for a in report["cardinalidade"]
    )
    report["conferencia_numerica_e_cardinalidade_concluida"] = complete
    (args.output / "conciliacao.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        "Conferência registrada; "
        + (
            "referência numérica e cardinalidade conferidas; revisar limites."
            if complete
            else "há pendências ou divergências."
        )
    )
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
