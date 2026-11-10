"""PDF local a partir do mesmo pacote CSV/PNG do ZIP; sem persistência ou cache."""

import io
import json
from zipfile import ZipFile

from vrac.branding import Branding

# Mesmos domínios aplicáveis do formulário; os demais não são filtros desta análise.
APPLICABLE = {
    "R01": {"Quadros", "Categorias"},
    "R02": {"Categorias", "Grupo QP selecionado"},
    "R03": {"Quadros", "Categorias", "Semestre inicial", "Semestre final"},
    "R04": {"Quadros", "Categorias", "Semestre da carga"},
    "R05": {"Quadros", "Categorias", "Semestre inicial", "Semestre final"},
    "R06": {
        "Semestre inicial",
        "Semestre final",
        "Cursos",
        "Habilitações",
        "Turnos",
        "Níveis",
        "Formas de ingresso",
    },
}


def report_pdf(
    package: bytes, branding: Branding, *, selected: tuple[str, ...] | None = None
) -> bytes:
    """Exporta a seleção explícita; sem seleção, exige o conjunto completo R01–R06."""
    archive = ZipFile(io.BytesIO(package))
    manifest = json.loads(archive.read("manifesto.json"))
    analyses = {r["kind"]: r for r in manifest["analyses"]}
    analyses.update({r["kind"]: r for r in manifest["additional_analyses"]})
    requested = tuple(APPLICABLE) if selected is None else selected
    if (
        not requested
        or len(set(requested)) != len(requested)
        or not set(requested) <= set(APPLICABLE)
        or not set(requested) <= set(analyses)
        or not manifest.get("synthetic")
    ):
        raise ValueError("Selecione análises disponíveis de R01–R06, com identificação sintética.")
    included = tuple(kind for kind in APPLICABLE if kind in requested)
    from vrac.analyses.pdf_slides import render_slides

    try:
        return render_slides(archive, manifest, analyses, included, branding, APPLICABLE)
    finally:
        archive.close()
