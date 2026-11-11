"""Legibilidade do PDF: rótulos de dados, meses por semestre, painéis e páginas sem vazio.

Cenários sintéticos em memória, montados a partir das fixtures; sem valor institucional.
"""

import io
from dataclasses import replace
from datetime import UTC, datetime

from matplotlib import pyplot as plt
from PIL import Image
from pypdf import PdfReader

from vrac.analyses.academic import (
    AnalysisFilters,
    AnalysisKind,
    ChartSpec,
    calculate,
    export_folder,
)
from vrac.analyses.academic_export import report_zip
from vrac.analyses.academic_fixture import load_fixture
from vrac.analyses.pdf_export import report_pdf
from vrac.branding import load_branding
from vrac.charts import (
    MAX_MONTHS_PER_PANEL,
    MONTH_NAMES,
    PANELS_KEY,
    academic_chart,
    chart_panels,
    render_png,
)

BRANDING = load_branding()
FILTERS = AnalysisFilters("2024.1", "2026.2", "2026.1")
CADRES = ("PROF HORISTA", "PROF PRINCIPAL")


def _results():
    source = load_fixture("SINT-A")
    return {kind: calculate(kind, source, FILTERS) for kind in AnalysisKind}


def _swap(result, key, columns, rows):
    tables = tuple(
        replace(t, columns=columns, rows=tuple(rows)) if t.key == key else t for t in result.tables
    )
    return replace(result, tables=tables)


def _long_history(years=range(2019, 2027)):
    """Histórico mensal de oito anos (96 competências) com valores de três dígitos."""
    history = _results()[AnalysisKind.HISTORY]
    rows = []
    for year in years:
        for semester, months in ((1, range(1, 8)), (2, range(8, 13))):
            for month in months:
                total = 100 + (year - 2019) * 5 + month
                rows.append(
                    (f"{year}.{semester}", f"{year}-{month:02}", month, total, 20, total - 30)
                )
    history = _swap(
        history, "monthly_history", ("Período", "Competência", "Mês", "Total", *CADRES), rows
    )
    return replace(
        history,
        charts=(
            ChartSpec("monthly_history", "Professores ativos", "Competência", ("Total",)),
            ChartSpec("monthly_history", "Por quadro", "Competência", CADRES, "stacked_bar"),
        ),
    )


def _texts(figure):
    return [t.get_text() for axis in figure.axes for t in axis.texts]


def test_single_series_line_has_marker_and_value_on_every_point():
    history = _results()[AnalysisKind.HISTORY]
    spec = next(s for s in history.charts if s.table == "history" and s.kind == "line")
    figure = academic_chart(history, spec, BRANDING)
    try:
        table = next(t for t in history.tables if t.key == "history")
        line = figure.axes[0].get_lines()[0]
        assert line.get_marker() not in (None, "None", "")
        known = [row[1] for row in table.rows if row[1] is not None]
        assert len(known) > 1
        # Um rótulo por ponto conhecido; ausência não ganha rótulo nem vira zero.
        assert sum(t.isdigit() for t in _texts(figure)) == len(known)
    finally:
        plt.close(figure)


def test_monthly_axis_uses_month_names_and_semester_groups():
    history = _results()[AnalysisKind.HISTORY]
    spec = next(s for s in history.charts if s.table == "monthly_history" and s.kind == "line")
    figure = academic_chart(history, spec, BRANDING)
    try:
        ticks = [t.get_text() for t in figure.axes[0].get_xticklabels()]
        assert ticks[:7] == list(MONTH_NAMES[:7])
        assert {"2024.1", "2024.2", "2026.2"} <= set(_texts(figure))
        assert chart_panels(figure) == 1
    finally:
        plt.close(figure)


def test_long_monthly_series_splits_at_semester_boundaries_with_same_scale():
    history = _long_history()
    png = render_png(lambda: academic_chart(history, history.charts[0], BRANDING))
    image = Image.open(io.BytesIO(png))
    panels = int(image.info[PANELS_KEY])
    assert panels == 2  # 96 meses, no máximo 48 por painel
    assert image.height == panels * 780 and image.width == 1800
    assert MAX_MONTHS_PER_PANEL == 48


def test_stacked_months_label_segments_that_fit():
    history = _long_history(range(2025, 2027))
    figure = academic_chart(history, history.charts[1], BRANDING)
    try:
        values = {t.get_text() for t in figure.axes[0].texts}
        # Segmento grande (≥ 100) e pequeno (20) recebem rótulo; nada de soma de meses.
        assert "20" in values and any(v.isdigit() and int(v) >= 100 for v in values)
    finally:
        plt.close(figure)


def test_long_category_names_become_horizontal_bars():
    functions = _results()[AnalysisKind.FUNCTIONS]
    names = [f"COORDENADOR DE PROGRAMA NÚMERO {i} DE PÓS-GRADUAÇÃO" for i in range(5)]
    functions = _swap(
        functions,
        "by_function",
        ("Gratificação", "Professores"),
        [(n, 5 - i) for i, n in enumerate(names)],
    )
    spec = next(s for s in functions.charts if s.table == "by_function")
    figure = academic_chart(functions, spec, BRANDING)
    try:
        axis = figure.axes[0]
        bars = axis.patches
        # Barras deitadas: largura varia com o valor, altura é fixa.
        assert len({round(b.get_height(), 3) for b in bars}) == 1
        assert sorted(round(b.get_width()) for b in bars) == [1, 2, 3, 4, 5]
        assert all(t.get_rotation() == 0 for t in axis.get_yticklabels())
    finally:
        plt.close(figure)


def _pdf(results, images):
    package = report_zip(
        results,
        datetime(2026, 11, 11, tzinfo=UTC),
        images,
        {},
        {"Origem": results[0].source},
    )
    selected = tuple(str(r.kind) for r in results)
    return PdfReader(io.BytesIO(report_pdf(package, BRANDING, selected=selected)))


def test_pdf_shows_one_panel_per_page():
    history = _long_history()
    images = {
        f"{export_folder('R03')}/grafico-1.png": render_png(
            lambda: academic_chart(history, history.charts[0], BRANDING)
        )
    }
    reader = _pdf((history,), images)
    text = " ".join(" ".join(p.extract_text().split()) for p in reader.pages)
    assert "GRÁFICO 1 DE 1 · PARTE 1 DE 2" in text and "GRÁFICO 1 DE 1 · PARTE 2 DE 2" in text


def test_results_without_cards_share_the_page_with_the_first_chart():
    students = _results()[AnalysisKind.STUDENTS]
    students = replace(students, metrics=(), charts=students.charts[:1])
    images = {
        f"{export_folder('R06')}/grafico-1.png": render_png(
            lambda: academic_chart(students, students.charts[0], BRANDING)
        )
    }
    reader = _pdf((students,), images)
    results_page = next(
        p for p in reader.pages if "RESULTADOS CALCULADOS" in p.extract_text().upper()
    )
    assert len(results_page.images) == 1
    assert not any("GRÁFICO 1 DE" in p.extract_text().upper() for p in reader.pages)


def test_long_filter_list_does_not_open_blank_pages():
    students = _results()[AnalysisKind.STUDENTS]
    courses = tuple(f"CURSO-{i:03} Nome do curso {i}" for i in range(260))
    students = replace(students, filters=replace(students.filters, courses=courses))
    reader = _pdf((students,), {})
    pages = [" ".join(p.extract_text().split()) for p in reader.pages]
    context = [p for p in pages if "Filtros e referências" in p]
    assert len(context) > 1
    # Cada página de contexto traz conteúdo além de cabeçalho e rodapé.
    for page in context:
        body = page
        for frame in (
            "ALUNOS · 01 · CONTEXTO DE LEITURA",
            "ALUNOS · 01",
            "Filtros e referências · Análise Geral dos alunos",
            "· continuação",
            "DEMONSTRAÇÃO · DADOS SINTÉTICOS · Sem validade institucional",
        ):
            body = body.replace(frame, "")
        # Sobra mais que o número da página.
        assert len(body.strip()) > 10, page
    assert "CURSO-259" in " ".join(context) and "Formas de ingresso" in " ".join(context)
