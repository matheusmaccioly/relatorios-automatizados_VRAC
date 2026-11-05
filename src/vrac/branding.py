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
    def logo_url(self) -> str:
        """Cópia idêntica servida localmente; evita reprocessar a imagem a cada interação."""
        return f"app/static/branding/{self.logo.name}"

    @property
    def series(self) -> tuple[str, ...]:
        """Ordem fixa das séries dos gráficos, igual na tela e nas exportações."""
        return tuple(self.tokens["charts"]["series"])

    @property
    def styles(self) -> str:
        values = self.tokens["colors"] | self.tokens["typography"]
        return "<style>" + Template(_STYLES).substitute(values) + "</style>"


# Somente cores dos tokens, sem variantes clareadas, escurecidas ou transparências.
# Componentes reproduzem os padrões observados no site público e no portal fornecido:
# fundo off-white, títulos e ações em preto, acento amarelo, raio de 3 px, rótulos em
# Literata e rodapé preto. É aproximação de referência, não homologação institucional.
# Seletores por data-testid/st-key: o tema nativo sobrepõe regras genéricas de h1-h3.
_STYLES = """
html {scroll-behavior: smooth;}
[data-testid="stHeader"] {background: transparent; height: 0 !important;
  min-height: 0 !important;}
[data-testid="stMain"] {overflow-x: clip;}
[data-testid="stMainBlockContainer"] {max-width: 1320px; padding: 0 2rem !important;}

/* Tipografia */
[data-testid="stHeading"] h1, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {
  color: $black; font-family: "$heading_family", sans-serif; font-weight: 700;
  line-height: 1.15; letter-spacing: -.01em;}
[data-testid="stHeading"] h2 {font-size: clamp(1.6rem, 2.6vw, 2rem); padding: .1rem 0 .5rem;}
[data-testid="stHeading"] h3 {font-size: clamp(1.25rem, 2vw, 1.5rem); padding: .1rem 0;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {color: $ink_soft;
  opacity: 1;}
[data-testid="stWidgetLabel"] p {font-family: "$editorial_family", serif; font-size: .9rem;
  color: $black;}

/* Faixa de aviso e cabeçalho */
.st-key-vrac-aviso {border-bottom: 1px solid $line;}
.st-key-vrac-aviso [data-testid="stAlertContainer"] {background: transparent; border: 0;
  padding: .45rem 0; font-size: .82rem;}
.st-key-vrac-aviso [data-testid="stAlertContainer"] p {font-size: .82rem; color: $ink_soft;}
.st-key-vrac-aviso strong {background: $yellow; color: $black; font-weight: 700;
  padding: 1px 7px; border-radius: 3px;}
.st-key-vrac-header {padding: .35rem 0;}
.vrac-marca img {display: block; height: auto; flex: none;}
.vrac-marca {display: flex; align-items: center; gap: 1rem;}
.vrac-marca .sep {width: 1px; height: 2.5rem; background: $line;}
.vrac-marca .nome {font-weight: 700; font-size: 1.2rem; line-height: 1.15; color: $black;}
.vrac-marca small {display: block; font-family: "$editorial_family", serif; font-weight: 400;
  font-size: .82rem; color: $ink_soft; margin-top: 2px;}

/* Navegação principal, como o menu em caixa alta do site */
.st-key-vrac-view > div:has(> [role="tablist"]) {overflow: visible;}
.st-key-vrac-view > div > [role="tablist"] {position: sticky; top: 0; z-index: 90;
  background: $background;}
[data-testid="stTabs"] [role="tablist"] {border-bottom: 1px solid $line; gap: 1.75rem;
  overflow-x: auto; scrollbar-width: thin;}
[data-testid="stTabs"] [role="tab"] {padding: .7rem 0; color: $black; white-space: nowrap;}
[data-testid="stTabs"] [role="tab"] p {font-weight: 700; font-size: .92rem;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {border-bottom: 3px solid $yellow;}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background: $yellow; height: 3px;}
[data-testid="stTabs"] [data-baseweb="tab-border"] {display: none;}
.st-key-vrac-view > div > [role="tablist"] [role="tab"] p {text-transform: uppercase;
  font-size: .95rem;}
/* Item do menu sem aba por trás: não recebe clique nem foco e não abre conteúdo.
   O Streamlit usa o ::after da lista como linha de base; aqui ele volta ao fluxo. */
.st-key-vrac-view > div > [role="tablist"]::before,
.st-key-vrac-view > div > [role="tablist"]::after {align-self: center; flex: none;
  cursor: not-allowed; white-space: nowrap;}
.st-key-vrac-view > div > [role="tablist"]::before {content: "Análise financeira"; order: 98;
  color: $ink_soft; font-weight: 400; font-size: .95rem; text-transform: uppercase;}
.st-key-vrac-view > div > [role="tablist"]::after {content: "Em breve"; order: 99;
  position: static; width: auto; height: auto; margin-left: -1.1rem;
  background: $yellow_soft; color: $black; font-size: .72rem; font-weight: 700;
  padding: 2px 8px; border-radius: 3px; text-transform: uppercase;}

/* Início */
.vrac-kicker {font-family: "$editorial_family", serif; font-size: 1rem; color: $black;
  margin: 0 0 .4rem;}
.vrac-hero h1 {font-family: "$heading_family", sans-serif; font-weight: 700; color: $black;
  font-size: clamp(2rem, 4.2vw, 3.1rem); line-height: 1.08; letter-spacing: -.01em;
  margin: 0 0 1rem; padding: 0;}
.vrac-hero p.lead {font-size: 1.15rem; color: $ink_soft; max-width: 40rem; margin: 0;}
.st-key-vrac-home-hero {padding: 2rem 0 .5rem;}
.vrac-bloco-num {background: $yellow; border-radius: 3px; padding: 1.4rem 1.75rem;
  height: 100%; min-height: 15rem; display: flex; flex-direction: column;
  justify-content: space-between; position: relative; box-sizing: border-box;}
.vrac-bloco-num .rot {font-family: "$editorial_family", serif; color: $black;}
.vrac-bloco-num dl {display: grid; grid-template-columns: auto 1fr; gap: .55rem .85rem;
  align-items: baseline; margin: 1rem 0 0;}
.vrac-bloco-num dl, .vrac-bloco-num dt, .vrac-bloco-num dd {padding: 0; margin-left: 0;}
.vrac-bloco-num dt {font-size: 2.4rem; line-height: 1; font-weight: 700; color: $black;
  font-variant-numeric: tabular-nums;}
.vrac-bloco-num dd {margin: 0; font-size: 1.05rem; color: $black;}
.vrac-section-title {border-top: 1px solid $black; padding-top: 1rem; margin-top: 1.25rem;}
.vrac-section-title h2 {font-family: "$heading_family", sans-serif; font-weight: 700;
  color: $black; font-size: clamp(1.5rem, 2.6vw, 2rem); margin: 0; padding: 0;}
.vrac-section-title p {font-family: "$editorial_family", serif; color: $ink_soft;
  margin: .25rem 0 0;}
.vrac-capa {border-radius: 3px; height: 8rem; padding: .85rem 1rem; display: flex;
  flex-direction: column; justify-content: space-between; box-sizing: border-box;}
.vrac-capa .selo {align-self: flex-start; background: $white; color: $black; font-size: .75rem;
  font-weight: 700; padding: 3px 9px; border-radius: 3px;}
.vrac-capa .capa-nome {display: flex; justify-content: space-between; align-items: flex-end;
  gap: .5rem; font-size: 1.45rem; font-weight: 700; line-height: 1.1;}
.vrac-capa .seta {flex: none; font-size: 1.4rem; line-height: 1;}
.vrac-capa.amarelo {background: $yellow; color: $black;}
.vrac-capa.azul {background: $blue; color: $white;}
.vrac-capa.preto {background: $black; color: $white;}
.vrac-card-body {min-height: 7.6rem;}
.vrac-card-body h3 {font-family: "$heading_family", sans-serif; color: $black; font-weight: 700;
  font-size: 1.15rem; line-height: 1.25; margin: .75rem 0 .35rem; padding: 0;}
.vrac-card-body p {color: $ink_soft; font-size: .95rem; margin: 0;}
[class*="st-key-vrac-card-"] {justify-content: space-between; height: 100%;}
.vrac-passos {list-style: none; margin: .5rem 0 0; padding: 0; display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.25rem;}
.vrac-passos li {display: flex; gap: .75rem; font-size: .95rem; color: $ink_soft;
  margin: 0; padding: 0;}
.vrac-passos b {display: block; color: $black;}
.vrac-n {flex: none; width: 1.7rem; height: 1.7rem; border-radius: 50%; background: $yellow;
  color: $black; display: inline-grid; place-items: center; font-weight: 700; font-size: .85rem;}

/* Etapas dos formulários */
.vrac-step {display: flex; align-items: center; gap: .6rem; font-weight: 700;
  font-size: 1.05rem; color: $black; border-top: 1px solid $line; padding-top: .9rem;}
.vrac-pergunta {font-weight: 700; font-size: 1.05rem; color: $black;}

/* Ações */
[data-testid="stBaseButton-primary"] {background: $black; border: 1.5px solid $black;
  border-radius: 3px; padding: .55rem 1.25rem;}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] p {color: $white;
  font-weight: 700;}
[data-testid="stBaseButton-primary"]:hover {background: $ink; border-color: $ink;}
[data-testid="stBaseButton-primary"]:hover p {color: $white;}
[data-testid="stBaseButton-secondary"] {background: transparent; border: 1.5px solid $black;
  border-radius: 3px;}
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondary"] p {color: $black;
  font-weight: 700;}
[data-testid="stBaseButton-secondary"]:hover {background: $surface_hover; border-color: $black;}
[data-testid="stBaseButton-secondary"]:hover p {color: $black;}
[data-testid="stBaseButton-tertiary"] p {color: $black; text-decoration: underline;
  font-weight: 600;}
[data-testid="stBaseButton-tertiary"]:hover p {color: $black; text-decoration-thickness: 2px;}
button, input, textarea, [role="combobox"] {border-radius: 3px;}
button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible,
[role="combobox"]:focus-visible, [role="tab"]:focus-visible, summary:focus-visible
  {outline: 3px solid $black !important; outline-offset: 2px;}

/* Campos */
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="textarea"]
  {background: $white; border-color: $line; border-radius: 3px;}
[data-testid="stMultiSelect"] [data-baseweb="tag"] {background: $black; color: $white;
  border-radius: 3px;}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span {color: $white;}
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {fill: $white;}

/* Painéis, resultados e indicadores */
[class*="st-key-vrac-panel"] {background: $white; border: 1px solid $line; border-radius: 3px;
  padding: 1.5rem 1.75rem; scroll-margin-top: 3.5rem;}
[data-testid="stMetric"] {background: $white; border: 1px solid $line; border-radius: 3px;
  padding: .9rem 1.1rem; min-width: 0; height: 100%; box-sizing: border-box;}
[data-testid="stMetricLabel"] p {font-family: "$editorial_family", serif; color: $black;
  white-space: normal;}
[data-testid="stMetricValue"] {font-family: "$body_family", sans-serif; font-weight: 700;
  font-variant-numeric: tabular-nums; color: $black;}
[class*="st-key-vrac-kpi"] [data-testid="stMetric"], [class*="st-key-vrac-metrics"]
  [data-testid="stColumn"]:first-child [data-testid="stVerticalBlock"] > :first-child
  [data-testid="stMetric"] {background: $yellow; border-color: $yellow;}
.vrac-single {display: flex; align-items: baseline; gap: .75rem;}
.vrac-single b {font-size: 2.2rem; line-height: 1.1; font-weight: 700; color: $black;
  font-variant-numeric: tabular-nums;}
.vrac-single span {color: $ink_soft;}
.vrac-subtitle {font-weight: 700; color: $black; font-size: 1.05rem; margin-top: .5rem;}
.vrac-card-title {font-weight: 700; color: $black; font-size: 1rem; line-height: 1.3;}
.vrac-card-title small {display: block; font-family: "$editorial_family", serif;
  font-weight: 400; font-size: .82rem; color: $ink_soft; margin-top: 1px;}
[class*="st-key-vrac-narrative"] {border-left: 3px solid $yellow; padding-left: .9rem;}
[data-testid="stExpander"] details {border: 1px solid $line; border-radius: 3px;
  background: $white;}
[data-testid="stExpander"] summary p {font-weight: 600; color: $black;}

/* Avisos: o estado também é dito em texto, nunca só pela cor */
[data-testid="stAlertContainer"] {background: $white; border: 1px solid $line;
  border-left: 5px solid $blue; border-radius: 3px; color: $black;}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"])
  {border-left-color: $yellow;}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"])
  {border-left-color: $red;}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"])
  {border-left-color: $turquoise;}
[class*="st-key-vrac-empty"] [data-testid="stAlertContainer"] {background: transparent;
  border: 1px dashed $line; text-align: center; padding: 1.5rem;}

/* Gráficos e tabelas */
[data-testid="stVegaLiteChart"] {width: 100%; min-width: 0;}
[data-testid="stElementToolbar"] {top: .35rem !important;}
[data-testid="stTable"] {overflow-x: auto;}
[data-testid="stTable"] th {background: $black; color: $white; font-weight: 600;}
[data-testid="stTable"] td {background: $white; color: $black;}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] table {width: 100%;}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] th {background: $black;
  color: $white; font-weight: 600;}
#vg-tooltip-element {background: $black !important; color: $white !important;
  border: 0 !important; border-radius: 3px !important; padding: .5rem .7rem !important;
  font-family: "$body_family", sans-serif !important; font-size: .82rem !important;
  box-shadow: none !important;}
#vg-tooltip-element table tr td {color: $white !important;}
#vg-tooltip-element table tr td.key {color: $yellow !important; font-weight: 600;
  max-width: 14rem;}

/* Conferência no fim da página: recolhida e sem moldura dentro da moldura */
.st-key-vrac-conferencia {margin-top: 2rem;}
.st-key-vrac-conferencia [class*="st-key-vrac-panel"] {border: 0; padding: 0;}

/* Rodapé preto, como no site */
.vrac-footer {background: $black; color: $white; width: 100vw; margin: 2.5rem 0 0 calc(50% - 50vw);
  padding: 2rem max(2rem, calc(50vw - 628px)); box-sizing: border-box; display: grid;
  grid-template-columns: 1fr 1fr; gap: 1rem 2.5rem; font-size: .85rem;}
.vrac-footer b {display: block; font-weight: 700; margin-bottom: .2rem; color: $white;}
.vrac-footer span {color: $line;}

@media (max-width: 960px) {
  .st-key-vrac-home-cards [data-testid="stColumn"] {min-width: calc(50% - 1rem);}
  .vrac-passos {grid-template-columns: 1fr;}
  .vrac-bloco-num {min-height: 0;}
  .vrac-card-body {min-height: 0;}
}
@media (max-width: 640px) {
  [data-testid="stMainBlockContainer"] {padding: 0 1rem !important;}
  .vrac-marca .sep, .vrac-marca small {display: none;}
  .st-key-vrac-home-cards [data-testid="stColumn"] {min-width: 100%;}
  [class*="st-key-vrac-panel"] {padding: 1rem .9rem;}
  [data-testid="stTabs"] [role="tablist"] {gap: 1.1rem;}
  .st-key-vrac-view > div > [role="tablist"]::after {margin-left: -.6rem;}
  [data-testid="stMetricValue"] {font-size: 1.75rem;}
  .vrac-footer {grid-template-columns: 1fr; padding: 1.5rem 1rem;}
}
@media (prefers-reduced-motion: reduce) {html {scroll-behavior: auto;}}
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
        "primaryColor": colors["black"],
        "backgroundColor": colors["background"],
        "secondaryBackgroundColor": colors["white"],
        "textColor": colors["black"],
        "borderColor": colors["line"],
        "dataframeBorderColor": colors["line"],
        "dataframeHeaderBackgroundColor": colors["black"],
        "dataframeHeaderTextColor": colors["white"],
        "linkColor": colors["black"],
        "font": typography["body_family"],
        "headingFont": typography["heading_family"],
        "headingFontWeights": [700, 700, 700, 700, 700, 700],
        "chartCategoricalColors": list(tokens["charts"]["series"]),
        "baseRadius": "small",
        "paddingTop": "2rem",
        "paddingBottom": "3rem",
        "showWidgetBorder": True,
        "showSidebarBorder": True,
    }
    # Estados são sempre descritos por texto; a cor apenas reforça a mensagem.
    palette = {
        "red": "red",
        "orange": "yellow_dark",
        "yellow": "yellow",
        "blue": "blue",
        "green": "turquoise",
        "violet": "purple",
        "gray": "gray",
    }
    for name, token in palette.items():
        theme[f"{name}Color"] = colors[token]
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
