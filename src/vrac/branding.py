"""Recursos locais de identidade; nenhum arquivo ou serviço externo é consultado."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from string import Template


@dataclass(frozen=True, slots=True)
class Branding:
    root: Path
    tokens: dict

    @property
    def logo(self) -> Path:
        return self.root / self.tokens["marks"]["primary_logo"]

    @property
    def styles(self) -> str:
        return "<style>" + Template(_STYLES).substitute(self.tokens["colors"]) + "</style>"


# Somente cores dos tokens, sem variantes clareadas, escurecidas ou transparências.
# Azul e cinza fornecidos têm contraste insuficiente para texto pequeno sobre branco:
# texto pequeno fica preto; azul só em títulos grandes, bordas e realces.
# Sobre o azul, texto branco em negrito: preto sobre #0081AD fica pouco legível
# (APCA ~Lc 37, contra ~Lc 70 do branco), apesar de a razão WCAG 2 favorecer o preto.
# Seletores por data-testid/st-key: o tema nativo sobrepõe regras genéricas de h1-h3.
_STYLES = """
button[kind="primary"], button[kind="primary"] p {color: $white; font-weight: 700;}
[data-testid="stHeader"] {border-top: 6px solid $blue;}
.vrac-stripe {display: flex; height: 6px; margin: .25rem 0 .5rem;}
.vrac-stripe span:nth-child(1) {flex: 6; background: $blue;}
.vrac-stripe span:nth-child(2) {flex: 3; background: $cyan;}
.vrac-stripe span:nth-child(3) {flex: 1; background: $yellow;}
.vrac-eyebrow {color: $black; font-weight: 600; letter-spacing: .12em;
  text-transform: uppercase; font-size: .8rem; margin: 0;}
.st-key-vrac-header h1 {color: $blue; font-weight: 700; padding-top: .25rem;}
[data-testid="stHeading"] h3 {color: $blue;}
[data-testid="stHeading"] h3::after {content: ""; display: block; width: 3rem;
  height: 4px; margin-top: .4rem; background: $yellow;}
.st-key-vrac-header {background: $white; border: 1px solid $gray;
  border-radius: .25rem; padding: 1.25rem 1.25rem .75rem;}
.st-key-vrac-filters, .st-key-vrac-results, .st-key-vrac-overview-filters,
.st-key-vrac-overview-results {background: $white;
  border: 1px solid $gray !important; border-top: 5px solid $blue !important;
  border-radius: .25rem; padding: 1.25rem;}
[data-testid="stAlertContainer"] {background: $white; border: 1px solid $gray;
  border-left: 6px solid $blue;}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"])
  {border-color: $yellow; border-left-color: $yellow;}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"])
  {border-left-color: $black;}
[data-testid="stTab"] p {font-weight: 600;}
[data-testid="stTabs"] [role="tablist"] {border-bottom: 2px solid $cyan;}
.vrac-footer {border-top: 1px solid $gray; margin-top: 2rem; padding-top: .75rem;
  color: $black; font-size: .8rem;}
"""


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
        "backgroundColor": colors["background"],
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
        "chartCategoricalColors": [
            colors["blue"],
            colors["cyan"],
            colors["yellow"],
            colors["gray"],
            colors["black"],
        ],
        "baseRadius": "small",
        "paddingTop": "2rem",
        "paddingBottom": "3rem",
        "showWidgetBorder": True,
        "showSidebarBorder": True,
    }
    # Estados se distinguem por seu texto, sem criar cores semânticas institucionais.
    # Amarelo e cinza só substituem seus homônimos; nenhuma variante clareada é criada.
    for name in ("red", "orange", "yellow", "blue", "green", "violet", "gray"):
        theme[f"{name}Color"] = colors[name] if name in ("yellow", "gray") else colors["blue"]
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
