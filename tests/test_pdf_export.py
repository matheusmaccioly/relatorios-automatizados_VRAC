"""Conciliação offline do PDF com os mesmos CSVs usados pelo ZIP."""

import io
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZipFile

import pytest
from pypdf import PdfReader
from streamlit.testing.v1 import AppTest

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_export import report_zip
from vrac.analyses.academic_fixture import load_fixture
from vrac.analyses.export import detail_csv, summary_csv
from vrac.analyses.faculty_overview import OverviewFilters, compute_overview
from vrac.analyses.pdf_export import report_pdf
from vrac.branding import load_branding
from vrac.charts import academic_chart, render_png


@pytest.mark.parametrize(
    "department,missing", [("SINT-A", False), ("SINT-VAZIO", False), ("SINT-A", True)]
)
def test_pdf_preserves_consolidated_values_and_omits_detail(department, missing):
    source = load_fixture(department)
    if missing:
        source = replace(source, available=frozenset(), errors=("Fontes indisponíveis",))
    filters = AnalysisFilters("2024.1", "2026.2", "2026.1")
    results = tuple(calculate(k, source, filters) for k in AnalysisKind)
    now = datetime(2026, 11, 9, tzinfo=UTC)
    overview = compute_overview(source.faculty, OverviewFilters())
    files = (
        {"R01/resumo.csv": summary_csv(overview, now), "R01/lista.csv": detail_csv(overview, now)}
        if not missing
        else {"R01/indisponivel.txt": b"Cadastro indisponivel; sem resultado."}
    )
    package = report_zip(
        results,
        now,
        additional_files=files,
        additional_analyses=(
            {"kind": "R01", "status": "indisponível" if missing else overview.status},
        ),
    )
    reader = PdfReader(io.BytesIO(report_pdf(package, load_branding())))
    text = " ".join(p.extract_text() for p in reader.pages)
    normalized = " ".join(text.split())
    # Departamento de ensino pode diferir da lotação autorizada; não é outro docente.
    forbidden = set(
        r.registration
        for r in compute_overview(load_fixture("SINT-B").faculty, OverviewFilters()).detail
    )
    assert not any(str(registration) in text for registration in forbidden)
    for kind in ("R01", "R02", "R03", "R04", "R05", "R06"):
        assert kind in text
    for page in reader.pages:
        assert "DADOS SINTÉTICOS" in page.extract_text()
    for result in results:
        assert result.status in text
        for metric in result.metrics:
            assert " ".join(metric.label.split()) in normalized
            expected = (
                "Ausente"
                if metric.value is None
                else (
                    f"{metric.value:.2f}".rstrip("0").rstrip(".")
                    if isinstance(metric.value, float)
                    else str(metric.value)
                ).replace(".", ",")
            )
            assert expected in text
            assert metric.unit in normalized
    assert "Lista de conferência" not in text
    assert "Registros históricos elegíveis" not in text
    assert "88000001" not in text
    assert all(
        float(p.mediabox.width) / float(p.mediabox.height) == pytest.approx(16 / 9)
        for p in reader.pages
    )


def test_partial_package_is_rejected():
    with pytest.raises(ValueError, match="R01"):
        report_pdf(report_zip((), datetime(2026, 11, 9, tzinfo=UTC)), load_branding())


@pytest.mark.parametrize("selected", [("R01",), ("R06",), ("R06", "R02")])
def test_selected_report_contains_only_requested_sections(selected):
    source = load_fixture("SINT-A")
    filters = AnalysisFilters("2024.1", "2026.2", "2026.1")
    now = datetime(2026, 11, 9, tzinfo=UTC)
    results = tuple(calculate(k, source, filters) for k in AnalysisKind)
    overview = compute_overview(source.faculty, OverviewFilters())
    package = report_zip(
        results,
        now,
        additional_files={"R01/resumo.csv": summary_csv(overview, now)},
        additional_analyses=({"kind": "R01", "status": overview.status},),
    )
    text = " ".join(
        p.extract_text()
        for p in PdfReader(
            io.BytesIO(report_pdf(package, load_branding(), selected=selected))
        ).pages
    )
    assert "Síntese visual" in text
    for kind in ("R01", "R02", "R03", "R04", "R05", "R06"):
        assert (f"{kind} ·" in text) == (kind in selected)
    if "R01" in selected:
        assert "Total de docentes" in text
    # A escolha não altera os dados nem o conteúdo original do ZIP.
    with ZipFile(io.BytesIO(package)) as archive:
        assert "R01/resumo.csv" in archive.namelist()


@pytest.mark.parametrize("selected", [(), ("R99",), ("R02", "R02"), ("R01",)])
def test_invalid_or_unavailable_selection_is_rejected(selected):
    package = report_zip((), datetime(2026, 11, 9, tzinfo=UTC))
    with pytest.raises(ValueError, match="Selecione"):
        report_pdf(package, load_branding(), selected=selected)


def test_download_revalidates_after_generation_before_exposing_bytes(monkeypatch):
    from vrac.ui_kit import download_button

    monkeypatch.setenv("VRAC_DEMO_SOURCE", "supabase")
    monkeypatch.setattr("vrac.ui_kit.st.button", lambda *args, **kwargs: True)
    rendered = []
    monkeypatch.setattr("streamlit.components.v1.html", lambda *a, **k: rendered.append(a))
    generated = False

    def verify():
        if generated:
            raise ValueError("Sessão expirada durante a geração")

    def build():
        nonlocal generated
        generated = True
        return b"%PDF-test"

    monkeypatch.setattr("vrac.supabase_auth.current_session", verify)
    with pytest.raises(ValueError, match="Sessão expirada"):
        download_button("PDF", build, file_name="test.pdf", mime="application/pdf")
    assert not rendered


def test_long_text_and_many_categories_preserve_chart_and_text():
    source = load_fixture("SINT-A")
    filters = AnalysisFilters("2024.1", "2026.2", "2026.1")
    results = tuple(calculate(k, source, filters) for k in AnalysisKind)
    marker = "Texto extenso de conferência com acentuação. " * 300
    results = (replace(results[0], narrative=marker), *results[1:])
    history = results[1]
    spec = history.charts[0]
    branding = load_branding()
    png = render_png(lambda: academic_chart(history, spec, branding))
    package = report_zip(
        results,
        datetime(2026, 11, 9, tzinfo=UTC),
        images={"R03/mensal.png": png},
        additional_files={"R01/indisponivel.txt": b"Cadastro indisponivel"},
        additional_analyses=({"kind": "R01", "status": "indisponível"},),
    )
    reader = PdfReader(io.BytesIO(report_pdf(package, branding)))
    assert len([im for p in reader.pages for im in p.images]) == 2  # marca e gráfico
    text = " ".join(" ".join(p.extract_text().split()) for p in reader.pages)
    # Rodapés entram na extração entre páginas; não podem apagar palavras do parágrafo.
    for word in ("Texto", "extenso", "conferência", "acentuação."):
        assert text.split().count(word) == 300


def test_single_analysis_offers_one_click_pdf_and_complete_report():
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=90
    ).run()
    app.button(key="home_open_R06").click().run()
    app.button(key="alunos_run").click().run()
    assert not app.exception
    # Uma análise só: sem seleção, o PDF sai direto, e o completo fica ao lado.
    assert not any(g.key == "alunos_pdf_analyses" for g in app.get("button_group"))
    assert pdf_labels(app, "alunos") == ["Baixar PDF"]
    keys = {d.key for d in app.get("download_button")}
    assert {"alunos_download_all", "alunos_complete_report"} <= keys


def test_pdf_selection_by_pills_and_invalidation():
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=90
    ).run()
    app.button(key="home_open_todas").click().run()
    app.button(key="suite_run").click().run()
    assert not app.exception
    assert len(app.button_group(key="suite_pdf_analyses").value) == 6
    assert pdf_labels(app, "suite") == ["Baixar PDF"]
    app.button_group(key="suite_pdf_analyses").set_value(["R01", "R06"]).run()
    assert not app.exception
    assert [d.key for d in app.get("download_button") if "_download_pdf" in d.key] == [
        "suite_download_pdf_R01_R06"
    ]
    app.button_group(key="suite_pdf_analyses").set_value([]).run()
    assert pdf_labels(app, "suite") == []
    assert any(d.key == "suite_download_all" for d in app.get("download_button"))
    # Com as seis análises calculadas, o atalho do relatório completo não se repete.
    assert not any(d.key == "suite_complete_report" for d in app.get("download_button"))
    app.selectbox(key="suite_last").select("2026.1").run()
    assert not any(d.key.startswith("suite_") for d in app.get("download_button"))


def test_home_complete_report_is_a_direct_download_of_all_six():
    from vrac.academic_ui import complete_report_pdf
    from vrac.department_hierarchy import ALL_CENTERS
    from vrac.organisation_ui import OrganisationScope
    from vrac.settings import load_settings

    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=90
    ).run()
    app.selectbox(key="home_department").select("SINT-B").run()
    # O botão do Início já é o download: não troca de aba nem calcula na tela.
    assert [d.key for d in app.get("download_button")] == ["home_complete"]
    assert app.session_state["vrac-view"] == "Início"
    assert "suite_results" not in app.session_state
    pdf = complete_report_pdf(
        load_settings(), load_branding(), OrganisationScope(ALL_CENTERS, "SINT-B", ("SINT-B",))
    )
    text = " ".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)
    for code in ("R01", "R02", "R03", "R04", "R05", "R06"):
        assert code in text
    assert "SINT-B" in text and "DADOS SINTÉTICOS" in text


def pdf_labels(app, prefix):
    return [
        d.label for d in app.get("download_button") if d.key.startswith(f"{prefix}_download_pdf")
    ]


def test_faculty_panorama_offers_the_same_pdf_block(monkeypatch):
    from vrac import academic_ui

    produced = {}
    original = academic_ui.download_button

    def click(label, data, **kwargs):
        """Gera o arquivo como no clique, para conferir o PDF real do panorama."""
        if kwargs.get("key", "").startswith("overview_download_pdf"):
            produced["pdf"] = data()
        return original(label, data, **kwargs)

    monkeypatch.setattr(academic_ui, "download_button", click)
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=90
    ).run()
    app.button(key="home_open_panorama").click().run()
    app.button(key="overview_run").click().run()
    assert not app.exception and not app.error
    assert app.button_group(key="overview_pdf_analyses").value == ["R01", "R03"]
    assert pdf_labels(app, "overview") == ["Baixar PDF"]
    assert any(d.key == "overview_download_all" for d in app.get("download_button"))
    reader = PdfReader(io.BytesIO(produced["pdf"]))
    text = " ".join(page.extract_text() for page in reader.pages)
    assert "R01" in text and "R03" in text and "DADOS SINTÉTICOS" in text
