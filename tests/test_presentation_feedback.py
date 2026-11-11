"""Feedback de apresentação: mesma origem, cálculos preservados e saída legível."""

import io
from datetime import UTC, datetime

from pypdf import PdfReader

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_export import report_zip
from vrac.analyses.pdf_export import report_pdf
from vrac.analyses.presentation_fixture import DEPARTMENT, load_presentation
from vrac.branding import load_branding
from vrac.charts import academic_chart
from vrac.demo_data import load_academic_source, load_faculty_source
from vrac.settings import Settings
from vrac.web_charts import interactive_chart


def test_presentation_counts_and_complete_classifications():
    source = load_presentation()
    filters = AnalysisFilters("2024.1", "2026.2", "2026.1", group_a_cadres=("PROF PRINCIPAL",))
    result = calculate(AnalysisKind.QP, source, filters)
    values = {m.label: m.value for m in result.metrics}
    assert (values["Geral"], values["QP"]) == (14, 12)
    assert round(values["QP em % de Geral"], 2) == 85.71
    assert all(r.cadre and r.category for r in source.faculty.register)
    assert not (
        {r.cadre for r in source.faculty.register} & {r.category for r in source.faculty.register}
    )
    assert source.fingerprint == load_presentation().fingerprint
    assert load_academic_source(Settings(), department=DEPARTMENT).faculty == source.faculty
    assert load_faculty_source(Settings(), department=DEPARTMENT) == source.faculty
    for department in (DEPARTMENT, "Todos os departamentos"):
        assert load_academic_source(Settings(), department=department).faculty.register == (
            load_faculty_source(Settings(), department=department).register
        )


def test_funnel_counts_and_pdf_readability():
    from matplotlib import pyplot as plt

    source = load_presentation()
    filters = AnalysisFilters("2024.1", "2026.2", "2026.1", group_a_cadres=("PROF PRINCIPAL",))
    result = calculate(AnalysisKind.WORKLOAD, source, filters)
    for spec in result.charts[1:]:
        table = next(t for t in result.tables if t.key == spec.table)
        figure = academic_chart(result, spec, load_branding())
        assert sorted(p.get_width() for p in figure.axes[0].patches) == sorted(
            row[1] for row in table.rows
        )
        plt.close(figure)
        assert "x2" in str(interactive_chart(result, spec, load_branding()).to_dict())
    qp = calculate(AnalysisKind.QP, source, filters)
    package = report_zip((qp, result), datetime(2026, 11, 9, 15, tzinfo=UTC))
    reader = PdfReader(io.BytesIO(report_pdf(package, load_branding(), selected=("R02", "R04"))))
    text = " ".join(p.extract_text() for p in reader.pages)
    assert "09/11/2026 às 12h00" in text
    assert "85,7%" in text and "85,714285" not in text
    assert "indicador" not in text.lower()
    assert "Snapshot:" not in text and "Origem e limitações" not in text
    assert all("DADOS SINTÉTICOS" in p.extract_text() for p in reader.pages)


def test_presentation_is_selectable_in_application():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=90
    ).run()
    app.button(key="home_open_R02").click().run()
    app.selectbox(key="suite_center").select("Exemplo de apresentação").run()
    app.button(key="suite_run").click().run()
    assert not app.exception and not app.error
    assert [m.value for m in app.metric][:3] == ["12", "14", "85,7"]
