"""Exemplo determinístico offline; nunca consulta banco ou configurações privadas."""

from datetime import UTC, datetime
from pathlib import Path

from vrac.analyses.academic import AnalysisFilters, AnalysisKind, calculate
from vrac.analyses.academic_export import report_zip
from vrac.analyses.academic_fixture import load_fixture
from vrac.analyses.export import detail_csv, summary_csv
from vrac.analyses.faculty_overview import OverviewFilters, compute_overview
from vrac.analyses.pdf_export import report_pdf
from vrac.branding import load_branding
from vrac.charts import academic_chart, distribution_bars, render_png
from vrac.indicators import indicator_distribution


def example_package() -> bytes:
    source = load_fixture("DEMO — Departamento exemplo")
    branding = load_branding()
    now = datetime(2026, 11, 9, 15, tzinfo=UTC)
    filters = AnalysisFilters("2024.1", "2026.2", "2026.1", qp_cadres=("PROF PRINCIPAL",))
    results = tuple(calculate(kind, source, filters) for kind in AnalysisKind)
    overview = compute_overview(source.faculty, OverviewFilters())
    context = {
        "Execução": "exemplo-offline-20261109",
        "Origem": source.faculty.source,
        "Departamentos efetivos": ", ".join(
            sorted({r.department for r in source.faculty.register})
        ),
        "Snapshot acadêmico": source.fingerprint,
    }
    files = {
        "R01/resumo.csv": summary_csv(overview, now),
        "R01/lista-conferencia.csv": detail_csv(overview, now),
    }
    images = {}
    for label, items, unit in (
        ("Departamento", overview.by_department, "linhas com matrícula"),
        ("Quadro", overview.by_cadre, "matrículas funcionais distintas"),
        ("Categoria", overview.by_category, "linhas com matrícula"),
        (
            "Resultado de carga",
            indicator_distribution(r.indicator for r in overview.detail),
            "linhas do cadastro",
        ),
    ):
        images[f"R01/{label}.png"] = render_png(
            lambda items=items, label=label, unit=unit: distribution_bars(
                items, title=label, unit=unit, branding=branding
            )
        )
    for result in results:
        for index, spec in enumerate(result.charts):
            table = next(t for t in result.tables if t.key == spec.table)
            if table.rows and any(
                row[table.columns.index(s)] is not None for row in table.rows for s in spec.series
            ):
                images[f"{result.kind}/grafico-{index}.png"] = render_png(
                    lambda result=result, spec=spec: academic_chart(result, spec, branding)
                )
    return report_zip(
        results,
        now,
        images,
        files,
        context,
        additional_analyses=({"kind": "R01", "status": str(overview.status)},),
    )


if __name__ == "__main__":
    destination = Path("output/pdf")
    destination.mkdir(parents=True, exist_ok=True)
    package = example_package()
    (destination / "relatorio-sintetico.zip").write_bytes(package)
    target = destination / "relatorio-sintetico.pdf"
    target.write_bytes(report_pdf(package, load_branding()))
    print(target)
