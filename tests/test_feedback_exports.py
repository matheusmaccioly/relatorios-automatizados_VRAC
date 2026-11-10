"""Conferência de arquivos e feedback apenas com dados sintéticos em memória."""

import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pytest
from matplotlib import pyplot as plt
from PIL import Image
from streamlit.testing.v1 import AppTest

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_export import report_zip, table_csv
from vrac.analyses.academic_fixture import load_fixture
from vrac.analyses.export import _write, detail_csv, safe_cell, summary_csv
from vrac.analyses.faculty_overview import OverviewFilters, compute_overview
from vrac.branding import load_branding
from vrac.charts import academic_chart, figure_png
from vrac.feedback import CATEGORIES, create_feedback, feedback_csv

NOW = datetime(2026, 11, 4, 12, 30, tzinfo=UTC)
FILTERS = AnalysisFilters("2024.1", "2026.2", "2026.2")
APP = Path(__file__).resolve().parents[1] / "app.py"


def test_exports_keep_context_values_accents_precision_and_formula_protection():
    source = load_fixture("SINT-A")
    result = calculate(AnalysisKind.STUDENTS, source, FILTERS)
    table = result.tables[0]
    context = {"Execução": str(uuid4()), "Centro": "São José", "Cálculo (UTC)": NOW.isoformat()}
    data = table_csv(result, table, NOW, context)
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig")), delimiter=";"))
    assert ["Contexto: Centro", "São José"] in rows
    assert ["Unidade", table.unit] in rows
    assert ["Gerado em UTC", NOW.isoformat()] in rows
    assert ["Aviso", result.notes[0]] in rows
    assert [safe_cell(value) for value in table.rows[0]] in rows
    assert safe_cell(-12.3456789) == "-12,3456789"
    assert safe_cell(" \t=1+1").startswith("'")
    assert _write([["@fórmula", -1.25, None]]).decode("utf-8-sig") == "'@fórmula;-1,25;ausente\r\n"

    figure = academic_chart(result, result.charts[0], load_branding())
    try:
        png = figure_png(figure, context | {"Unidade": table.unit})
    finally:
        plt.close(figure)
    with Image.open(io.BytesIO(png)) as image:
        assert json.loads(image.info["Contexto"])["Centro"] == "São José"
        assert "SINTÉTICOS" in image.info["Description"]
    package = report_zip((result,), NOW, {"R06/grafico-1.png": png}, context=context)
    with ZipFile(io.BytesIO(package)) as archive:
        manifest = json.loads(archive.read("manifesto.json"))
        assert manifest["context"] == context
        assert archive.read(f"R06/{table.key}.csv") == data
        assert archive.read("R06/grafico-1.png") == png
        assert manifest["analyses"][0]["fingerprint"] == source.fingerprint


def test_feedback_minimal_association_validation_and_csv():
    execution_id = str(uuid4())
    records = [
        create_feedback(
            execution_id,
            "R06",
            "Calculado",
            NOW,
            category,
            "=comentário" if category != "Útil" else "",
            NOW,
        )
        for category in CATEGORIES
    ]
    rows = list(csv.reader(io.StringIO(feedback_csv(records).decode("utf-8-sig")), delimiter=";"))
    assert len(rows) == 5
    assert all(row[0] == execution_id for row in rows[1:])
    assert rows[2][5] == "'=comentário"
    assert len(rows[0]) == 7
    with pytest.raises(ValueError):
        create_feedback(execution_id, "R06", "Calculado", NOW, "Divergência", " ", NOW)
    with pytest.raises(ValueError):
        create_feedback(execution_id, "R06", "Calculado", NOW, "outro", "texto", NOW)


def test_r01_files_keep_effective_context_and_their_own_snapshot():
    source = load_fixture("SINT-A")
    overview = compute_overview(source.faculty, OverviewFilters())
    context = {
        "Centro": "Centro São José",
        "Snapshot": overview.fingerprint,
        "Extração": "horário não registrado nesta tela",
    }
    for data in (summary_csv(overview, NOW, context), detail_csv(overview, NOW, context)):
        text = data.decode("utf-8-sig")
        assert "Centro São José" in text
        assert overview.fingerprint in text
        assert "horário não registrado nesta tela" in text
        assert "DEMONSTRAÇÃO" in text


def test_feedback_is_tied_to_execution_and_survives_rerun_not_filter_change():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="home_open_R06").click().run()
    app.button(key="alunos_run").click().run()
    first = app.session_state["alunos_execution_id"]
    app.selectbox(key="alunos_feedback_category").select("Divergência")
    app.text_area(key="alunos_feedback_comment").input("Conferir informação exibida")
    app.button(key="alunos_feedback_submit").click().run()
    assert not app.exception
    assert len(app.session_state["feedback_records"]) == 1
    assert app.session_state["feedback_records"][0].execution_id == first
    app.button(key="alunos_run").click().run()
    assert app.session_state["alunos_execution_id"] != first
    assert len(app.session_state["feedback_records"]) == 1
    second = app.session_state["alunos_execution_id"]
    app.run()
    assert len(app.session_state["feedback_records"]) == 1
    app.selectbox(key="alunos_last").select("2026.1").run()
    assert "alunos_execution_id" not in app.session_state
    app.button(key="alunos_run").click().run()
    assert app.session_state["alunos_execution_id"] not in (first, second)
    assert app.session_state["feedback_records"][0].execution_id == first


def test_faculty_feedback_is_bound_to_each_calculation_and_retained_in_session():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="overview_run").click().run()
    first = app.session_state["overview_execution_id"]
    assert any(
        "dados pessoais" in item.value and "acadêmicos" in item.value for item in app.caption
    )
    app.selectbox(key="overview_feedback_category").select("Sugestão")
    app.text_area(key="overview_feedback_comment").input("Rever a explicação")
    app.button(key="overview_feedback_submit").click().run()
    record = app.session_state["feedback_records"][0]
    assert record.execution_id == first and record.analysis == "Análise docente"
    app.run()
    assert len(app.session_state["feedback_records"]) == 1
    app.button(key="overview_run").click().run()
    second = app.session_state["overview_execution_id"]
    assert second != first
    app.button(key="overview_feedback_submit").click().run()
    assert app.session_state["feedback_records"][-1].execution_id == second
    assert app.session_state["feedback_records"][-1].category == "Útil"
    app.selectbox(key="overview_feedback_category").select("Dificuldade")
    app.text_area(key="overview_feedback_comment").input("Localizar o filtro")
    app.button(key="overview_feedback_submit").click().run()
    assert app.session_state["feedback_records"][-1].category == "Dificuldade"
    assert app.session_state["feedback_records"][-1].execution_id == second
    app.multiselect(key="overview_cadres").select("PROF PRINCIPAL").run()
    assert "overview_execution_id" not in app.session_state
    assert len(app.session_state["feedback_records"]) == 3


def test_package_manifest_and_files_follow_the_displayed_execution(monkeypatch):
    from vrac import academic_ui

    captured = {}
    original = academic_ui.report_zip

    def capture(*args, **kwargs):
        package = original(*args, **kwargs)
        captured["package"] = package
        return package

    monkeypatch.setattr(academic_ui, "report_zip", capture)
    button = academic_ui.st.download_button

    def click(label, data, *args, **kwargs):
        """O pacote é montado no clique; aqui ele é gerado para conferir o arquivo real."""
        if kwargs.get("key") == "suite_download_all":
            data()
        return button(label, data, *args, **kwargs)

    monkeypatch.setattr(academic_ui.st, "download_button", click)
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.button(key="home_open_todas").click().run()
    app.selectbox(key="suite_last").select("2026.1").run()
    app.multiselect(key="suite_cadres").select("PROF PRINCIPAL").run()
    app.button(key="suite_run").click().run()
    assert not app.exception
    results = app.session_state["suite_results"]
    with ZipFile(io.BytesIO(captured["package"])) as archive:
        manifest = json.loads(archive.read("manifesto.json"))
        assert manifest["synthetic"] is True
        assert manifest["context"]["Execução"] == app.session_state["suite_execution_id"]
        assert manifest["context"]["Referência final"] == "2026.1"
        assert manifest["context"]["Quadros"] == "PROF PRINCIPAL"
        assert manifest["additional_analyses"][0]["kind"] == "R01"
        assert manifest["additional_analyses"][0]["fingerprint"] in archive.read(
            "R01/resumo.csv"
        ).decode("utf-8-sig")
        for result, entry in zip(results, manifest["analyses"], strict=True):
            assert entry["kind"] == result.kind and entry["filters"]["last_period"] == "2026.1"
            for table in result.tables:
                rows = list(
                    csv.reader(
                        io.StringIO(
                            archive.read(f"{result.kind}/{table.key}.csv").decode("utf-8-sig")
                        ),
                        delimiter=";",
                    )
                )
                start = rows.index(list(table.columns)) + 1
                assert rows[start:] == [[safe_cell(value) for value in row] for row in table.rows]
        png_name = next(name for name in archive.namelist() if name.endswith(".png"))
        with Image.open(io.BytesIO(archive.read(png_name))) as image:
            context = json.loads(image.info["Contexto"])
            assert context["Execução"] == manifest["context"]["Execução"]
            assert context["Unidade"] and context["Avisos"]
        with Image.open(io.BytesIO(archive.read("R02/grafico-2.png"))) as image:
            assert json.loads(image.info["Contexto"])["Unidade"] == (
                "matrículas funcionais distintas"
            )
