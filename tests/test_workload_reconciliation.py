"""Conferência R04 offline; SQLite não comprova a instância PostgreSQL."""

import re
import sqlite3
from contextlib import nullcontext
from dataclasses import asdict, replace
from datetime import UTC, datetime
from io import BytesIO
from zipfile import ZipFile

import pytest

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_data import AllocationRow, SimulationPolicy, WorkloadRow
from vrac.analyses.academic_export import report_zip, table_csv
from vrac.analyses.academic_fixture import load_fixture
from vrac.analyses.faculty_overview import semaphore_status
from vrac.branding import load_branding
from vrac.charts import academic_chart
from vrac.dev import workload_reconciliation as recon

FILTERS = AnalysisFilters("2024.1", "2026.2", "2026.1")


def row(reg, real, contract, cadre="PRINCIPAL", semester=20261):
    return WorkloadRow("SINT-A", reg, semester, "SYN", cadre, "C", real, contract)


def detail(result):
    return {r[0]: r for r in next(t for t in result.tables if t.key == "workload").rows}


class SqliteReference:
    def __init__(self, source):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute("ATTACH DATABASE ':memory:' AS vrac_sintetico")
        self.db.execute(
            "CREATE TABLE vrac_sintetico.analysis_workloads "
            "(department, registration, semester, name, cadre, category, "
            "real_hours, contracted_hours)"
        )
        self.db.executemany(
            "INSERT INTO vrac_sintetico.analysis_workloads VALUES (?,?,?,?,?,?,?,?)",
            [tuple(asdict(r).values()) for r in source.workloads],
        )

    def transaction(self):
        return nullcontext()

    def cursor(self):
        return nullcontext(self)

    def execute(self, sql, params):
        sql = re.sub(r"%\((\w+)\)s", r":\1", sql)
        sql = sql.replace("json_each_text(CAST(", "json_each(CAST(")
        sql = sql.replace(" AS json))", " AS text))")
        self.result = self.db.execute(sql, params)

    def fetchall(self):
        return self.result.fetchall()


def test_offline_reference_scenarios_match_and_detect_tampering(monkeypatch):
    source = load_fixture("SINT-A")
    connection = SqliteReference(source)
    records = []
    for name, filters in recon.scenarios(source):
        records += recon.reconcile(connection, source, ("SINT-A",), filters, name)
    assert len(records) > 100
    assert all(r["situacao"] in {"Confere", "Ausente em ambas"} for r in records)
    original = recon.calculate

    def wrong(*args):
        result = original(*args)
        metric = replace(result.metrics[0], value=999)
        return replace(result, metrics=(metric, *result.metrics[1:]))

    monkeypatch.setattr(recon, "calculate", wrong)
    assert any(
        r["situacao"] == "Divergente"
        for r in recon.reconcile(connection, source, ("SINT-A",), FILTERS, "teste")
    )


def test_null_contract_policy_and_coverage_are_independent():
    source = load_fixture("SINT-A")
    rows = (
        row("V1", 10, 20),
        row("V1", None, 20),
        row("V2", None, 5),
        row("V3", 4, 0),
        row("V4", 4, 8),
        row("V4", 3, 9),
        row("V5", 999, 1, semester=20262),
    )
    source = replace(source, workloads=rows)
    result = calculate(AnalysisKind.WORKLOAD, source, FILTERS)
    values = detail(result)
    assert values["V1"][5:9] == ("Resultados distintos", 10, 20, "Parcial")
    assert values["V2"][6] is None and values["V2"][8] == "Nulo na fonte"
    assert values["V3"][6:8] == (4, 0)
    assert values["V4"][6:8] == (7, None)  # CH Contratada conflitante fica ausente
    assert (
        "V5" not in values and result.status == "Parcial" and result.metrics[1].status == "Parcial"
    )
    partial_only = replace(source, workloads=rows[:2])
    assert calculate(AnalysisKind.WORKLOAD, partial_only, FILTERS).metrics[1].status == "Parcial"
    for policy, available in (
        (SimulationPolicy(), source.available),
        (SimulationPolicy("h", "min", True), source.available),
        (SimulationPolicy(" ", " ", True), source.available),
        (source.policy, source.available - {"policy"}),
    ):
        result = calculate(
            AnalysisKind.WORKLOAD, replace(source, policy=policy, available=available), FILTERS
        )
        # A política declara só a unidade; as horas exibidas não dependem dela.
        assert detail(result)["V1"][6:8] == (10, 20)


@pytest.mark.parametrize(
    "cadre,hours,expected",
    [
        ("PRINCIPAL", 6, "Abaixo do necessário"),
        ("PRINCIPAL", 7, "Dentro do esperado"),
        ("PRINCIPAL", 44, "Dentro do esperado"),
        ("PRINCIPAL", 45, "Acima do necessário"),
        ("COMPLEMENTAR TEMPO INTEGRAL", 15, "Abaixo do necessário"),
        ("COMPLEMENTAR TEMPO INTEGRAL", 16, "Dentro do esperado"),
        ("COMPLEMENTAR TEMPO INTEGRAL", 20, "Dentro do esperado"),
        ("COMPLEMENTAR TEMPO INTEGRAL", 21, "Acima do necessário"),
        ("COMPLEMENTAR TEMPO PARCIAL", 11, "Abaixo do necessário"),
        ("COMPLEMENTAR TEMPO PARCIAL", 12, "Dentro do esperado"),
        ("COMPLEMENTAR TEMPO PARCIAL", 15, "Dentro do esperado"),
        ("COMPLEMENTAR TEMPO PARCIAL", 16, "Acima do necessário"),
        ("COMPLEMENTAR TEMPO PARCIAL", 31, "Muito acima (verificar coord./múltiplas turmas)"),
        ("PROF PRINCIPAL", 12, "Sem regra definida"),
        ("PROF PRINCIPAL", 0, "Sem alocação (CH = 0)"),
        (None, None, "Sem CH (em branco)"),
    ],
)
def test_panel_indicator_boundaries(cadre, hours, expected):
    assert semaphore_status(hours, cadre) == expected


def test_allocations_keep_cross_departments_shared_zero_null_and_missing_classification():
    source = load_fixture("SINT-A")
    allocations = (
        AllocationRow("SINT-A", "SINT-A", "V1", 20261, "TCC", "T1", 7, 0, "S", None),
        AllocationRow("SINT-A", "SINT-B", "V1", 20261, "TCC", "T1", 8, None, "S", None),
        AllocationRow("SINT-A", "SINT-B", "V1", 20262, "OUTRA", "T2", 100, 1, "N", None),
    )
    source = replace(source, workloads=(row("V1", 10, 20),), allocations=allocations)
    result = calculate(AnalysisKind.WORKLOAD, source, FILTERS)
    actual = next(t for t in result.tables if t.key == "allocation_detail").rows
    assert len(actual) == 2 and actual[0][1:3] == ("SINT-A", "SINT-A")
    assert actual[1][1:3] == ("SINT-A", "SINT-B") and actual[0][15] == 0 and actual[1][15] is None
    assert actual[0][13] is None and actual[0][-1] == 1  # um professor na turma
    assert detail(result)["V1"][6] == 10
    no_alloc = replace(source, allocations=(), available=source.available - {"allocations"})
    result = calculate(AnalysisKind.WORKLOAD, no_alloc, FILTERS)
    assert detail(result)["V1"][6] == 10 and any("indisponível" in n for n in result.notes)
    no_hours = replace(source, workloads=(), available=source.available - {"workloads"})
    assert calculate(AnalysisKind.WORKLOAD, no_hours, FILTERS).status == "Bloqueado"
    assert calculate(AnalysisKind.STUDENTS, no_hours, FILTERS).status != "Bloqueado"


def test_cli_requires_explicit_execution(capsys):
    assert recon.main([]) == 2
    assert "--execute" in capsys.readouterr().out


def test_workload_export_and_chart_follow_tables_and_warnings():
    from matplotlib import pyplot as plt

    source = replace(load_fixture("SINT-A"), workloads=(row("V1", 10, 20), row("V1", None, 20)))
    result = calculate(AnalysisKind.WORKLOAD, source, FILTERS)
    distribution = next(t for t in result.tables if t.key == "real_distribution")
    detail_table = next(t for t in result.tables if t.key == "workload")
    now = datetime(2026, 11, 3, tzinfo=UTC)
    csv = table_csv(result, detail_table, now)
    decoded = csv.decode("utf-8-sig")
    assert "DEMONSTRAÇÃO" in decoded and source.fingerprint in decoded
    assert "Parcial" in decoded and "2026.1" in decoded and "h/semana (simulação)" in decoded
    figure = academic_chart(result, result.charts[0], load_branding())
    assert [bar.get_height() for bar in figure.axes[0].patches] == [r[1] for r in distribution.rows]
    plt.close(figure)
    with ZipFile(BytesIO(report_zip((result,), now))) as archive:
        assert archive.read("4-carga-horaria/workload.csv") == csv
        assert b'"synthetic": true' in archive.read("manifesto.json")
