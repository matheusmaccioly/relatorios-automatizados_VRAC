"""Apresentação executiva local: resultados e gráficos, sem tabelas de registros."""

import csv
import io
from datetime import datetime
from xml.sax.saxutils import escape
from zipfile import ZipFile
from zoneinfo import ZoneInfo

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from vrac.analyses.academic_export import FILTER_LABELS
from vrac.branding import Branding


def render_slides(
    archive: ZipFile,
    manifest: dict,
    analyses: dict,
    included: tuple[str, ...],
    branding: Branding,
    applicable: dict,
) -> bytes:
    """Composição editorial 16:9; conteúdo exclusivamente dos resultados existentes."""
    for font in branding.tokens["fonts"]:
        name = f"{font['family']}-{font['weight']}"
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(branding.root / font["file"])))
    family = branding.tokens["typography"]["body_family"]
    editorial = branding.tokens["typography"]["editorial_family"]
    palette = branding.tokens["colors"]
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(960, 540))
    canvas.setTitle("Análises acadêmicas | Síntese visual")
    page_count = 0

    def color(key: str):
        return HexColor(palette[key])

    def para(
        value: object,
        x: float,
        top: float,
        width: float,
        size: int = 14,
        bold: bool = False,
        ink: str = "black",
        serif: bool = False,
    ) -> float:
        style = ParagraphStyle(
            "text",
            fontName=f"{editorial if serif else family}-{700 if bold else 400}",
            fontSize=size,
            leading=size * 1.3,
            textColor=color(ink),
        )
        p = Paragraph(escape(str(value)).replace("\n", "<br/>"), style)
        _, height = p.wrap(width, 2000)
        p.drawOn(canvas, x, top - height)
        return top - height

    def page(kicker: str, title: str) -> None:
        nonlocal page_count
        if page_count:
            canvas.showPage()
        page_count += 1
        canvas.setFillColor(color("background"))
        canvas.rect(0, 0, 960, 540, fill=1, stroke=0)
        canvas.setFillColor(color("yellow"))
        canvas.rect(36, 455, 46, 5, fill=1, stroke=0)
        para(kicker.upper(), 36, 512, 780, 11, serif=True)
        para(title, 36, 490, 880, 25, True)
        canvas.setStrokeColor(color("line"))
        canvas.line(36, 33, 924, 33)
        para(
            "INSTITUCIONAL PSEUDONIMIZADA · Acesso restrito · Validação pendente"
            if manifest.get("synthetic") is False
            else "DEMONSTRAÇÃO · DADOS SINTÉTICOS · Sem validade institucional",
            36,
            24,
            820,
            9,
        )
        para(f"{page_count:02}", 889, 24, 35, 10, True)

    def paragraphs(values: list[str], heading: str, kicker: str, top: float = 430) -> None:
        # Quebra por linhas pelo próprio motor tipográfico, sem truncar textos extensos.
        style = ParagraphStyle("flow", fontName=f"{family}-400", fontSize=14, leading=19)
        y = top
        for value in values:
            pending = [Paragraph(escape(value), style)]
            while pending:
                p = pending.pop(0)
                _, height = p.wrap(880, 20000)
                if height > y - 55:
                    pieces = p.split(880, y - 55)
                    if not pieces:
                        page(kicker, heading + " · continuação")
                        y = 430
                        pending.insert(0, p)
                        continue
                    first, *rest = pieces
                    _, height = first.wrap(880, 20000)
                    first.drawOn(canvas, 36, y - height)
                    page(kicker, heading + " · continuação")
                    y = 430
                    pending = rest + pending
                else:
                    p.drawOn(canvas, 36, y - height)
                    y -= height + 12

    context = manifest.get("context", {})
    page("PUC-Rio · Análises acadêmicas", "Síntese visual dos resultados")
    canvas.setFillColor(color("yellow"))
    canvas.roundRect(36, 75, 555, 345, 4, fill=1, stroke=0)
    para("Docentes, carga horária\ne matrículas", 60, 385, 490, 38, True)
    para("Resultados consolidados e gráficos", 60, 230, 490, 20, serif=True)
    para("Análises selecionadas: " + ", ".join(included), 60, 173, 490, 16, True)
    para("Tabelas detalhadas disponíveis na aplicação e no ZIP.", 60, 126, 490, 14)
    canvas.drawImage(
        str(branding.logo),
        640,
        314,
        width=220,
        height=105,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )
    para("Recorte", 630, 280, 285, 13, serif=True)
    para(
        context.get(
            "Departamentos efetivos", context.get("Departamento", "Conforme filtros das análises")
        ),
        630,
        252,
        285,
        18,
        True,
    )
    generated = datetime.fromisoformat(manifest["generated_at_utc"]).astimezone(
        ZoneInfo("America/Sao_Paulo")
    )
    para("Gerado em\n" + generated.strftime("%d/%m/%Y às %Hh%M") + " (Brasília)", 630, 170, 285, 12)
    para("Aplicação visual sujeita à revisão institucional.", 630, 100, 285, 11)

    page("Roteiro de leitura", "Análises deste relatório")
    for index, kind in enumerate(included):
        y = 420 - index * 58
        canvas.setFillColor(color("yellow"))
        canvas.roundRect(36, y - 38, 62, 38, 3, fill=1, stroke=0)
        para(kind, 48, y - 7, 55, 17, True)
        para(analyses[kind].get("title", "Situação geral do departamento"), 118, y - 5, 790, 19)

    appendices = []
    for kind in included:
        result = analyses[kind]
        title = result.get("title", "Situação geral do departamento")
        metrics = list(result.get("metrics", []))
        narrative = result.get("narrative", "")
        notes = list(result.get("notes", []))
        filters = []
        provenance = []
        if kind == "R01":
            filename = "R01/resumo.csv"
            if filename in archive.namelist():
                rows = csv.reader(
                    io.StringIO(archive.read(filename).decode("utf-8-sig")), delimiter=";"
                )
                for row in rows:
                    if len(row) < 3:
                        continue
                    group, label, value = row[:3]
                    if group == "Resultado" and label == "Total":
                        metrics.append(
                            {
                                "label": "Total de docentes",
                                "value": value,
                                "unit": "matrículas funcionais distintas",
                                "status": "Cadastro atual",
                            }
                        )
                    elif group == "Texto" or (group == "Resultado" and label == "Situação"):
                        narrative = value
                    elif group == "Filtro":
                        filters.append((label, value))
                    elif group == "Aviso":
                        notes.append(value)
                    elif group == "Identificação" and label in {
                        "Origem",
                        "Versão dos dados",
                        "Snapshot",
                        "Departamento",
                    }:
                        provenance.append(f"{label}: {value}")
            else:
                for name in archive.namelist():
                    if name.startswith("R01/") and name.endswith(".txt"):
                        notes.append(archive.read(name).decode("utf-8-sig"))
        else:
            for key, value in result["filters"].items():
                label = FILTER_LABELS[key]
                if label in applicable[kind]:
                    shown = ", ".join(value) if isinstance(value, list) else str(value)
                    filters.append((label, shown or "Todos (sem restrição)"))
            provenance = [
                f"{label}: {result.get(key, 'Não disponível')}"
                for label, key in (
                    ("Origem", "source"),
                    ("Versão dos dados", "version"),
                    ("Versão do cálculo", "calculation_version"),
                    ("Snapshot", "fingerprint"),
                    ("Departamento", "department"),
                )
            ]
            notes += [m["note"] for m in metrics if m.get("note")]
            notes += [t["note"] for t in result.get("tables", []) if t.get("note")]

        page(f"{kind} · Resultados calculados", title)
        status = {"valid": "Calculado", "partial": "Parcial", "empty": "Sem dados"}.get(
            result["status"], result["status"]
        )
        para("Situação: " + status, 36, 433, 880, 13, serif=True)
        # Resultados existentes, sem médias ou totais novos.
        for start in range(0, max(1, len(metrics)), 6):
            if start:
                page(f"{kind} · Resultados", title)
            batch = metrics[start : start + 6]
            count = min(3, max(1, len(batch)))
            width = (888 - (count - 1) * 16) / count
            for i, metric in enumerate(batch):
                x = 36 + (i % 3) * (width + 16)
                y = 393 - (i // 3) * 130
                canvas.setFillColor(color("yellow" if i == 0 else "white"))
                canvas.roundRect(x, y - 120, width, 120, 4, fill=1, stroke=0)
                value = metric["value"]
                shown = (
                    "Ausente"
                    if value is None
                    else (
                        f"{value:.2f}".rstrip("0").rstrip(".")
                        if isinstance(value, float)
                        else str(value)
                    ).replace(".", ",")
                )
                para(shown, x + 14, y - 12, width - 28, 31, True)
                para(metric["label"], x + 14, y - 58, width - 28, 15, True)
                para(
                    metric["unit"] + " · " + metric.get("status", ""),
                    x + 14,
                    y - 102,
                    width - 28,
                    10,
                )
            top = 240 if len(batch) <= 3 else 120
            if narrative and start == 0:
                # Textos extensos continuam em páginas próprias, nunca são reduzidos ou cortados.
                paragraphs([narrative], title, kind, top)
            if not batch and not narrative:
                para(
                    "Sem resultados disponíveis. Consulte a situação "
                    "e as limitações deste recorte.",
                    36,
                    360,
                    850,
                    20,
                )

        charts = [n for n in archive.namelist() if n.startswith(kind + "/") and n.endswith(".png")]
        for index, name in enumerate(charts):
            page(f"{kind} · Gráfico {index + 1} de {len(charts)}", title)
            canvas.setFillColor(color("white"))
            canvas.roundRect(36, 53, 888, 382, 4, fill=1, stroke=0)
            image = ImageReader(io.BytesIO(archive.read(name)))
            w, h = image.getSize()
            ratio = min(860 / w, 354 / h)
            canvas.drawImage(
                image,
                480 - w * ratio / 2,
                244 - h * ratio / 2,
                width=w * ratio,
                height=h * ratio,
                mask="auto",
            )
        if not charts:
            notes.append("Sem gráfico disponível para este recorte; ausência não representa zero.")
        appendices.append((kind, filters, provenance, list(dict.fromkeys(notes))))

    # Filtros em tabela; referências e avisos preservados fora da sequência visual principal.
    for kind, filters, _provenance, _notes in appendices:
        page(f"{kind} · Contexto de leitura", "Filtros e referências")
        y = 430
        for label, value in [("Filtro aplicável", "Valor efetivo"), *filters]:
            style = ParagraphStyle("cell", fontName=f"{family}-400", fontSize=13, leading=17)
            cells = [Paragraph(escape(str(v)), style) for v in (label, value)]
            heights = [p.wrap(w, 20000)[1] for p, w in zip(cells, (260, 580), strict=True)]
            height = max(heights) + 16
            if height > 350:
                paragraphs([f"{label}: {value}"], "Filtros e referências", kind, y)
                page(kind, "Filtros e referências · continuação")
                y = 430
                continue
            if y - height < 65:
                page(kind, "Filtros e referências · continuação")
                y = 430
            canvas.setFillColor(color("white"))
            canvas.rect(36, y - height, 888, height - 2, fill=1, stroke=0)
            for p, x, h in zip(cells, (48, 324), heights, strict=True):
                p.drawOn(canvas, x, y - 8 - h)
            y -= height
        # Identificadores técnicos e notas integrais permanecem no pacote ZIP.
        if kind == "R02":
            paragraphs(
                [
                    "O grupo QP deste exemplo é definido pelos quadros selecionados acima. "
                    "Sua composição institucional permanece pendente."
                ],
                "Filtros e referências",
                kind,
                y - 12,
            )
        if analyses[kind].get("status") in {"Parcial", "Bloqueado", "Sem dados", "indisponível"}:
            paragraphs(
                [
                    "Há resultados indisponíveis neste recorte. Ausência não significa zero. "
                    "Consulte os avisos da análise na aplicação."
                ],
                "Filtros e referências",
                kind,
                y - 75,
            )
    canvas.save()
    return output.getvalue()
