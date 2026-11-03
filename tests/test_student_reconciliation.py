"""Referência SQL independente em SQLite offline; isto NÃO comprova leitura PostgreSQL."""

import csv
import io
import json
import math
import re
import sqlite3
from contextlib import contextmanager, nullcontext
from dataclasses import asdict, replace
from datetime import UTC, datetime
from zipfile import ZipFile

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_data import ALL_DEPARTMENTS, ScholarshipRow, StudentRow
from vrac.analyses.academic_export import report_zip, table_csv
from vrac.analyses.academic_fixture import load_fixture
from vrac.branding import load_branding
from vrac.charts import academic_chart, figure_png
from vrac.demo_data import DemoDataError, DemoOptions
from vrac.dev import student_reconciliation as reconciliation

FILTERS = AnalysisFilters("2024.1", "2026.2", "2026.2")


def student(reg, period=20241, status="MT", entry=20241, **changes):
    row = StudentRow(
        reg,
        "SINT-A",
        "C1",
        "Curso semelhante",
        "H1",
        "D",
        "GR",
        entry,
        period,
        status,
        "Ingresso sintético",
    )
    return replace(row, **changes)


def source_for(history, current, scholarships=()):
    return replace(
        load_fixture("SINT-A"),
        student_history=tuple(history),
        students=tuple(current),
        scholarships=tuple(scholarships),
    )


def tables(source, filters=FILTERS):
    return {t.key: t for t in calculate(AnalysisKind.STUDENTS, source, filters).tables}


class OfflineReference:
    """Executa o SQL de referência com apenas adaptação de binding e função JSON."""

    def __init__(self, source):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("ATTACH DATABASE ':memory:' AS vrac_sintetico")
        fields = tuple(StudentRow.__dataclass_fields__)
        # DDL só no SQLite em memória do teste, nunca no PostgreSQL/institucional.
        for name, values in (
            ("students", source.students),
            ("student_history", source.student_history),
        ):
            self.connection.execute(
                f"CREATE TABLE vrac_sintetico.analysis_{name} (" + ", ".join(fields) + ")"
            )
            self.connection.executemany(
                f"INSERT INTO vrac_sintetico.analysis_{name} VALUES ("
                + ",".join("?" for _ in fields)
                + ")",
                [tuple(asdict(row).values()) for row in values],
            )
        self.connection.execute(
            "CREATE TABLE vrac_sintetico.analysis_scholarships (registration, period, department)"
        )
        self.connection.executemany(
            "INSERT INTO vrac_sintetico.analysis_scholarships VALUES (?, ?, ?)",
            [
                (row.registration, row.period, department)
                for row in source.scholarships
                for registration, department in {
                    (r.registration, r.department) for r in source.student_history
                }
                if registration == row.registration
            ],
        )

    def transaction(self):
        return nullcontext()

    def cursor(self):
        return nullcontext(self)

    def execute(self, sql, parameters):
        sql = re.sub(r"%\((\w+)\)s", r":\1", sql)
        sql = re.sub(r"json_each_text\(CAST\((:\w+) AS json\)\)", r"json_each(\1)", sql)
        self.result = self.connection.execute(sql, parameters)

    def fetchone(self):
        return dict(self.result.fetchone())

    def close(self):
        self.connection.close()


def compare(source, filters=FILTERS, scenario="Caso offline"):
    reference = OfflineReference(source)
    try:
        departments = tuple(
            sorted({r.department for r in (*source.students, *source.student_history)})
        )
        records = reconciliation.reconcile_source(
            reference, source, departments or ("SINT-A",), filters, scenario
        )
    finally:
        reference.close()
    assert records
    assert all(r["situacao"] in {"Confere", "Ausente em ambas"} for r in records), records
    return records


def test_completion_detail_matches_individual_course_and_never_leaks_mt_mc():
    source = source_for(
        [],
        [
            student(1, status="FR"),
            student(1, 20242, course="C2"),
            student(2, status="FR"),
            student(2, 20242, "TD", course="C2"),
            student(2, 20251, "TD", course="C2"),
            student(3, status="HF"),
        ],
    )
    result = tables(source)
    # No total: matrículas 1 e 2 no menor período FR/TD. HF não entra.
    assert result["students"].rows[0][3] == 2
    assert result["students"].rows[1][3] == 0
    detail = {(row[0], row[1]): row[2:] for row in result["student_courses"].rows}
    assert detail[("C2", "2024.1")][2] is None  # nenhuma observação nesse curso/ponto
    assert detail[("C2", "2024.2")][2] == 1  # TD de 2; MT de 1 não é formação
    assert detail[("C2", "2025.1")][2] == 0  # segunda ocorrência TD não repete evento
    for course in ("C1", "C2"):
        for row in tables(source, replace(FILTERS, courses=(course,)))["students"].rows:
            assert detail[(course, row[0])] == row[1:]
    compare(source)


def test_entry_minimum_uses_loaded_register_before_all_academic_dimensions():
    history = [
        student(1),
        student(1, status="MC"),
        student(1, status="FR"),
        student(None),
        student(2, entry=20262),
        student(3, entry=20242),
    ]
    current = [
        student(1, entry=20262),
        student(
            1,
            entry=20232,
            course="C2",
            qualification="H2",
            shift="N",
            level="PG",
            entry_kind="Outro ingresso",
        ),
        student(2, entry=20262),
        student(3, entry=20242),
    ]
    source = source_for(
        history,
        current,
        [ScholarshipRow(1, 20241)] * 3 + [ScholarshipRow(2, 20241), ScholarshipRow(None, 20241)],
    )
    filters = replace(
        FILTERS,
        courses=("C1",),
        qualifications=("H1",),
        shifts=("D",),
        levels=("GR",),
        entry_kinds=("Ingresso sintético",),
    )
    assert tables(source, filters)["students"].rows[0] == ("2024.1", 1, 1, 0, 1)
    compare(source, filters)
    unknown = replace(source, students=tuple(row for row in current if row.registration != 1))
    assert tables(unknown, filters)["students"].rows[0][1:3] == (None, None)
    assert any(
        "Ingresso desconhecido" in note
        for note in calculate(AnalysisKind.STUDENTS, unknown, filters).notes
    )
    compare(unknown, filters)


def test_literal_double_diploma_and_course_names_do_not_join_populations():
    history = [
        student(1, 20242, entry_kind="Dupla Diplomacao"),
        student(1, 20242, entry_kind="Dupla Diplomacao"),
        student(2, 20242, entry_kind="Dupla Diplomação"),
        student(3, 20242, course="C2"),
        student(4, 20241, course="C2"),
    ]
    source = source_for(history, history)
    result = tables(source)
    assert result["students"].rows[0][4] == 2  # 1 pela exceção literal; 4 no próprio ponto
    assert set(row[0] for row in result["student_courses"].rows) == {"C1", "C2"}
    compare(source)
    compare(source, replace(FILTERS, courses=("C1", "C2")))


def test_zero_missing_period_missing_entry_and_missing_current_have_distinct_effects():
    history = [student(1, status="HF"), student(1, 20251), student(2, 20252, entry=None)]
    source = source_for(history, [student(1), student(2, entry=None)])
    result = tables(source)
    assert result["students"].rows[0] == ("2024.1", 0, 0, 0, 1)
    assert result["students"].rows[1] == ("2024.2", None, None, None, None)
    assert result["enrollment_change"].rows[0][4:] == (None, None, "Ausência de dado")
    assert result["students"].rows[3][1:3] == (None, None)
    compare(source)
    without_current = replace(source, students=(), available=source.available - {"students"})
    assert tables(without_current)["students"].rows[0][1:] == (None, None, None, 1)
    without_bags = replace(source, scholarships=(), available=source.available - {"scholarships"})
    assert tables(without_bags)["students"].rows[0][1:] == (0, None, 0, 1)
    observed_zero = source_for([student(1, status="HF"), student(1, 20242)], [student(1)])
    assert tables(observed_zero)["enrollment_change"].rows[0][4:] == (1, None, "Base zero")
    compare(observed_zero)


def test_fixture_all_individual_and_combined_filters_against_sql(tmp_path):
    records = []
    snapshots = {}
    for department in (ALL_DEPARTMENTS, "SINT-A", "SINT-B", "SINT-VAZIO"):
        source = load_fixture(department)
        snapshots[department] = source.fingerprint
        for scenario, filters in reconciliation.scenarios(source):
            records.extend(compare(source, filters, scenario))
    # Artefato explicitamente offline, reprodutível pelo comando pytest com --basetemp.
    (tmp_path / "conciliacao-offline.json").write_text(
        json.dumps(
            {
                "evidencia": "SQLite em memória / fixture pública; não PostgreSQL",
                "fonte": source.faculty.source,
                "snapshots": snapshots,
                "registros": records,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    assert {r["populacao"] for r in records} >= set(reconciliation.POPULATIONS)


def test_reference_scholarship_failure_is_separate_from_other_populations():
    source = source_for([student(1)], [student(1)], [ScholarshipRow(1, 20241)] * 2)
    source = replace(source, available=source.available - {"scholarships"}, scholarships=())
    reference = OfflineReference(source)
    reference.connection.execute("DROP TABLE vrac_sintetico.analysis_scholarships")
    try:
        records = reconciliation.reconcile_source(
            reference, source, ("SINT-A",), FILTERS, "Sem bolsas"
        )
    finally:
        reference.close()
    dependent = [r for r in records if r["populacao"] == "Bolsistas matriculados"]
    independent = [r for r in records if r["populacao"] != "Bolsistas matriculados"]
    assert all(r["situacao"].startswith("Pendente") and r["obtido"] is None for r in dependent)
    assert all(r["situacao"] in {"Confere", "Ausente em ambas"} for r in independent)


def test_reference_detects_deliberate_divergence_without_accepting_production_as_expected(
    monkeypatch,
):
    source = source_for([student(1)], [student(1)])
    correct = calculate(AnalysisKind.STUDENTS, source, FILTERS)
    wrong = replace(
        correct,
        tables=tuple(
            replace(t, rows=(("2024.1", 999, 0, 0, 1), *t.rows[1:])) if t.key == "students" else t
            for t in correct.tables
        ),
    )
    monkeypatch.setattr(reconciliation, "calculate", lambda *args: wrong)
    reference = OfflineReference(source)
    try:
        records = reconciliation.reconcile_source(
            reference, source, ("SINT-A",), FILTERS, "Mutação"
        )
    finally:
        reference.close()
    mismatch = next(row for row in records if row["populacao"] == "Matriculados")
    assert (
        mismatch["esperado"],
        mismatch["obtido"],
        mismatch["diferenca"],
        mismatch["situacao"],
    ) == (1, 999, 998, "Divergente")


def test_all_series_chart_csv_and_zip_match_values_and_gaps():
    from matplotlib import pyplot as plt

    source = source_for([student(1, status="HF"), student(1, 20251)], [student(1)])
    result = calculate(AnalysisKind.STUDENTS, source, FILTERS)
    series = next(t for t in result.tables if t.key == "students")
    figure = academic_chart(result, result.charts[0], load_branding())
    try:
        for index, line in enumerate(figure.axes[0].lines, 1):
            assert list(line.get_xdata()) == list(range(len(series.rows)))
            for row, actual in zip(series.rows, line.get_ydata(), strict=True):
                assert math.isnan(actual) if row[index] is None else actual == row[index]
        png = figure_png(figure)
        assert b"DADOS TOTALMENTE SINT" in png
        now = datetime(2026, 11, 3, tzinfo=UTC)
        with ZipFile(io.BytesIO(report_zip((result,), now, {"R06/grafico-1.png": png}))) as archive:
            manifest = json.loads(archive.read("manifesto.json"))
            assert (
                manifest["synthetic"]
                and manifest["analyses"][0]["fingerprint"] == source.fingerprint
            )
            assert archive.read("R06/grafico-1.png") == png
            for table in result.tables:
                direct = table_csv(result, table, now)
                assert archive.read(f"R06/{table.key}.csv") == direct
                rows = list(csv.reader(io.StringIO(direct.decode("utf-8-sig")), delimiter=";"))
                data = rows[rows.index(list(table.columns)) + 1 :]
                assert data == [[reconciliation.safe_cell(v) for v in row] for row in table.rows]
                assert ["Snapshot", source.fingerprint] in rows
                assert any("vigência por período" in cell for row in rows for cell in row)
    finally:
        plt.close(figure)


def test_manual_routine_requires_execute_and_failure_is_pending_sanitized(tmp_path, monkeypatch):
    calls = []

    def fail():
        calls.append(True)
        raise DemoDataError("password=ficticio-nao-exportar")

    monkeypatch.setattr(reconciliation, "run_postgres", fail)
    output = tmp_path / "leitura"
    assert reconciliation.main(["--output", str(output)]) == 2
    assert not calls and not output.exists()
    assert reconciliation.main(["--execute", "--output", str(output)]) == 1
    report = json.loads((output / "conciliacao.json").read_text(encoding="utf-8"))
    assert report["evidencia"] == "PostgreSQL pendente" and not report["conciliacao_concluida"]
    assert "ficticio-nao-exportar" not in json.dumps(report)
    assert reconciliation.main(["--execute", "--output", str(output)]) == 2
    assert len(calls) == 1  # não sobrescreve evidências


def test_manual_routine_shares_one_connection_with_reader_and_references(monkeypatch):
    opens, reads, comparisons = [], [], []

    class SnapshotConnection:
        def cursor(self):
            return nullcontext(self)

        def execute(self, sql):
            assert "txid_current_snapshot()" in sql

        def fetchone(self):
            return {"snapshot": "fixture-offline", "isolation": "repeatable read"}

    connection = SnapshotConnection()

    @contextmanager
    def open_snapshot(settings):
        opens.append(settings)
        yield connection, "fixture-offline"

    def read(received, version, *, department):
        assert received is connection and version == "fixture-offline"
        reads.append(department)
        return load_fixture(department)

    def reconcile(received, source, departments, filters, scenario):
        assert received is connection
        comparisons.append((source.department, departments))
        return [{"situacao": "Confere"}]

    monkeypatch.setattr(reconciliation, "_connection", open_snapshot)
    monkeypatch.setattr(reconciliation, "_read_academic_source", read)
    monkeypatch.setattr(reconciliation, "reconcile_source", reconcile)
    monkeypatch.setattr(
        reconciliation,
        "_options",
        lambda c: DemoOptions(("SINT-A", "SINT-VAZIO"), ("2024.1",), "2024.1", "Fixture offline"),
    )
    report = reconciliation.run_postgres()
    assert len(opens) == 1
    assert reads == [ALL_DEPARTMENTS, "SINT-A", "SINT-VAZIO"]
    assert {depts for dept, depts in comparisons if dept == ALL_DEPARTMENTS} == {
        ("SINT-A", "SINT-VAZIO")
    }
    assert report["snapshot_postgres"]["isolation"] == "repeatable read"


def test_evidence_csv_preserves_line_endings_null_and_formula_protection(tmp_path, monkeypatch):
    monkeypatch.setattr(
        reconciliation,
        "run_postgres",
        lambda: {
            "registros": [
                {
                    "cenario": "=Cenario sintetico",
                    "esperado": None,
                    "obtido": None,
                    "diferenca": None,
                    "situacao": "Ausente em ambas",
                    "filtros": {"courses": ["C1"]},
                }
            ]
        },
    )
    output = tmp_path / "csv"
    assert reconciliation.main(["--execute", "--output", str(output)]) == 0
    data = (output / "conciliacao.csv").read_bytes()
    assert data.startswith(b"\xef\xbb\xbf") and b"\r\r\n" not in data
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig")), delimiter=";"))
    assert len(rows) == 1
    assert rows[0]["cenario"].startswith("'=")
    assert rows[0]["esperado"] == rows[0]["obtido"] == rows[0]["diferenca"] == "ausente"
    assert json.loads(rows[0]["filtros"]) == {"courses": ["C1"]}
