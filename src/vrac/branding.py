"""Recursos locais de identidade; nenhum arquivo ou serviço externo é consultado."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Branding:
    root: Path
    tokens: dict

    @property
    def logo(self) -> Path:
        return self.root / self.tokens["marks"]["primary_logo"]

    @property
    def styles(self) -> str:
        # A cor azul fornecida tem contraste insuficiente com branco em texto pequeno.
        # Usar preto sobre o azul no botão, sem inventar uma variante escurecida.
        colors = self.tokens["colors"]
        return (
            "<style>"
            f'button[kind="primary"] {{color: {colors["black"]};}}'
            f"h1, h2, h3 {{color: {colors['blue']};}}"
            "</style>"
        )


def load_branding() -> Branding:
    checkout = Path(__file__).resolve().parents[2] / "assets" / "branding"
    root = checkout if checkout.is_dir() else Path(__file__).parent / "branding_assets"
    with (root / "tokens.toml").open("rb") as stream:
        return Branding(root, tomllib.load(stream))


def streamlit_theme(tokens: dict) -> dict:
    """Valores derivados apenas dos tokens, para o gerador e verificação offline."""
    colors = tokens["colors"]
    typography = tokens["typography"]
    theme = {
        "base": "light",
        "primaryColor": colors["blue"],
        "backgroundColor": colors["white"],
        "secondaryBackgroundColor": colors["white"],
        "textColor": colors["black"],
        "borderColor": colors["blue"],
        "dataframeBorderColor": colors["blue"],
        "dataframeHeaderBackgroundColor": colors["cyan"],
        "dataframeHeaderTextColor": colors["black"],
        "linkColor": colors["black"],
        "font": typography["body_family"],
        "headingFont": typography["heading_family"],
        "headingFontWeights": [600, 600, 600, 600, 600, 600],
        "chartCategoricalColors": [colors["blue"], colors["cyan"], colors["black"]],
        "baseRadius": "small",
        "paddingTop": "2rem",
        "paddingBottom": "3rem",
        "showWidgetBorder": True,
        "showSidebarBorder": True,
    }
    # Estados se distinguem por seu texto, sem criar cores semânticas institucionais.
    for name in ("red", "orange", "yellow", "blue", "green", "violet", "gray"):
        theme[f"{name}Color"] = colors["blue"]
        theme[f"{name}BackgroundColor"] = colors["white"]
        theme[f"{name}TextColor"] = colors["black"]
    theme["fontFaces"] = [
        {
            "family": font["family"],
            "url": f"app/static/branding/{Path(font['file']).name}",
            "weight": font["weight"],
            "style": font["style"],
        }
        for font in tokens["fonts"]
    ]
    return theme
