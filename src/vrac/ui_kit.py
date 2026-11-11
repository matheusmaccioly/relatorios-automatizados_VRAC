"""Peças visuais compartilhadas pelas telas; sem cálculo nem acesso a dados."""

import base64
import json
from collections.abc import Callable, Collection, Iterator, Mapping
from contextlib import contextmanager
from functools import cache
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from vrac.branding import load_branding
from vrac.indicators import ABSENT, INDICATORS, indicator_label
from vrac.settings import DemoSource, load_settings

ARTIFACT_CACHE = "vrac_artifact_cache"
ARTIFACT_CACHE_LIMIT = 96


def download_button(label: str, data: Any, *, file_name: str, mime: str, **kwargs: Any) -> Any:
    """Supabase entrega bytes só à sessão autorizada, sem URL pública de mídia.

    O clique prepara o arquivo e o entrega na própria página já autenticada, sem segundo
    clique; o link fica visível caso o navegador bloqueie a transferência automática.
    A transferência é local ao navegador; não cria arquivo no servidor nem endpoint que
    sobreviva ao logout.
    """
    if load_settings().demo_source != DemoSource.SUPABASE:
        return st.download_button(label, data, file_name=file_name, mime=mime, **kwargs)
    from vrac.supabase_auth import current_session

    current_session()
    if st.button(
        label,
        key=kwargs.get("key"),
        type=kwargs.get("type", "secondary"),
        icon=kwargs.get("icon"),
        help=kwargs.get("help"),
        width=kwargs.get("width", "content"),
        disabled=kwargs.get("disabled", False),
    ):
        from vrac.demo_data import DemoDataError

        try:
            with st.spinner("Preparando o arquivo..."):
                content = data() if callable(data) else data
        except (DemoDataError, ValueError) as error:
            st.error(f"Não foi possível preparar o arquivo: {error}")
            return False
        content = content.encode("utf-8") if isinstance(content, str) else content
        if not isinstance(content, bytes) or len(content) > 25 * 1024 * 1024:
            st.error("O arquivo excede o limite de exportação desta demonstração.")
            return False
        current_session()  # Revalidar após gerar, antes de entregar os bytes.
        encoded = base64.b64encode(content).decode("ascii")
        # Iframe isolado: script fixo que só aciona o link; sem token nem armazenamento.
        from streamlit.components.v1 import html

        branding = load_branding()
        font = next(f for f in branding.tokens["fonts"] if str(f["weight"]) == "400")
        font_bytes = base64.b64encode((branding.root / font["file"]).read_bytes()).decode("ascii")
        family = escape(branding.tokens["typography"]["body_family"], quote=True)
        color = branding.tokens["colors"]["black"]
        html(
            f'<style>@font-face {{font-family:"{family}";src:url(data:font/ttf;base64,'
            f'{font_bytes}) format("truetype");}} '
            f'a {{font-family:"{family}";color:{color};}}</style>'
            f'<a id="arquivo" href="data:{escape(mime, quote=True)};base64,{encoded}" '
            f'download="{escape(file_name, quote=True)}" '
            ">Download não começou? Clique aqui.</a>"
            '<script>document.getElementById("arquivo").click()</script>',
            height=35,
        )
        return True
    return False


ROW_HEIGHT = 38
# Nas listas por docente, o que se quer ler vem logo depois do nome.
FIRST_COLUMNS = (
    "Nome fictício",
    "Resultado de carga (regra do painel)",
    "Resultado do painel",
    "Horas Reais (semestre atual)",
    "Horas Reais",
    "CH contratada",
    "Carga contratada",
)
TONE_TOKENS = {"attention": "yellow_soft", "strong": "yellow", "neutral": "surface_hover"}


def info_button(notes: Collection[str], *, key: str, title: str = "Regras e limitações") -> None:
    """Regras, avisos e limitações num ícone discreto; o texto continua acessível no clique."""
    if not notes:
        return
    with st.popover(
        "", icon=":material/info:", type="tertiary", help=title, key=f"vrac-info-{key}"
    ):
        items = "".join(f"<li>{escape(note)}</li>" for note in notes)
        st.html(f'<div class="vrac-info"><b>{escape(title)}</b><ul>{items}</ul></div>')


def titled_row(title: Callable[[], None], notes: Collection[str], *, key: str) -> None:
    """Título à esquerda e o ícone de informação no canto direito da mesma linha."""
    with st.container(horizontal=True, vertical_alignment="center", key=f"vrac-titulo-{key}"):
        title()
        info_button(notes, key=key)


def filter_review(descriptions: Mapping[str, str]) -> None:
    """Tabela Filtro | Valor do recorte ainda não calculado, igual em todas as telas."""
    st.markdown(
        "| Filtro | Valor |\n|---|---|\n"
        + "\n".join(
            f"| {name} | {str(value).replace('|', ' / ').replace(chr(10), ' ')} |"
            for name, value in descriptions.items()
        )
    )


def used_filters(descriptions: Mapping[str, str], caption: str) -> None:
    """Filtros do último cálculo, com versão e horários; mesmo bloco em todas as telas."""
    with st.expander("Filtros usados neste resultado", expanded=False):
        st.table(
            pd.DataFrame([{"Filtro": name, "Valor": value} for name, value in descriptions.items()])
        )
        st.caption(caption)


def step(number: int, title: str) -> None:
    """Etapa numerada de um formulário, como as seções do portal de referência."""
    st.html(f'<div class="vrac-step"><span class="vrac-n">{number}</span>{escape(title)}</div>')


def scroll_to(panel: str) -> None:
    """Leva a tela ao painel recém-calculado; o script é fixo e não recebe dados."""
    st.html(
        "<script>setTimeout(() => window.parent.document"
        f".querySelector('.st-key-{panel}')?.scrollIntoView(), 400)</script>",
        unsafe_allow_javascript=True,
    )


def card_title(title: str, subtitle: str | None = None) -> None:
    detail = f"<small>{escape(subtitle)}</small>" if subtitle else ""
    st.html(f'<div class="vrac-card-title">{escape(title)}{detail}</div>')


@contextmanager
def card_header(title: str, subtitle: str | None = None, *, key: str) -> Iterator[None]:
    """Cabeçalho de cartão: título à esquerda; ícone e ações à direita, sem quebrar a linha."""
    with st.container(horizontal=True, vertical_alignment="center", key=f"vrac-card-head-{key}"):
        card_title(title, subtitle)
        yield


def single_value(value: object, label: str) -> None:
    """Uma categoria só: o número é a resposta, sem gráfico de uma barra."""
    st.html(
        f'<div class="vrac-single"><b>{escape(str(value))}</b><span>{escape(label)}</span></div>'
    )


@cache
def _indicator_styles() -> dict[str, str]:
    """Fundo de cada estado, somente com tokens; o que está no esperado fica sem destaque."""
    colors = load_branding().tokens["colors"]
    styles = {
        indicator_label(name): f"background-color: {colors[TONE_TOKENS[tone]]}"
        for name, (_, tone) in INDICATORS.items()
        if tone in TONE_TOKENS
    }
    return styles | {ABSENT: f"background-color: {colors[TONE_TOKENS['neutral']]}"}


def data_table(frame: pd.DataFrame, *, numeric: Collection[str] = ()) -> None:
    """Tabela padrão da aplicação: mesma altura de linha, colunas úteis antes e resultado visual.

    Só muda o que se vê. Os valores calculados e os arquivos exportados não passam por aqui.
    """
    indicators = [name for name in frame.columns if str(name).startswith("Resultado")]
    shown = frame.assign(**{name: frame[name].map(indicator_label) for name in indicators})
    first = [name for name in FIRST_COLUMNS if name in shown.columns]
    st.dataframe(
        shown.style.map(lambda value: _indicator_styles().get(value, ""), subset=indicators)
        if indicators
        else shown,
        hide_index=True,
        width="stretch",
        row_height=ROW_HEIGHT,
        column_order=[*first, *(name for name in shown.columns if name not in first)],
        column_config={name: st.column_config.TextColumn(alignment="right") for name in numeric},
    )


def session_cached[T](name: str, context: Mapping[str, str] | None, build: Callable[[], T]) -> T:
    """Reaproveita o que já foi montado nesta execução, para reruns não refazerem gráficos.

    A chave inclui todo o contexto exportado, com identificador de execução e filtros;
    um novo cálculo sempre monta tudo de novo. Sem contexto, nada é reaproveitado.
    """
    if not context:
        return build()
    cache = st.session_state.setdefault(ARTIFACT_CACHE, {})
    key = (name, json.dumps(dict(context), sort_keys=True, ensure_ascii=False))
    if key not in cache:
        if len(cache) >= ARTIFACT_CACHE_LIMIT:
            cache.clear()
        cache[key] = build()
    return cache[key]


def show_chart(
    name: str,
    context: Mapping[str, str] | None,
    build: Callable[[], Any],
    *,
    key: str,
) -> None:
    """Valida o gráfico uma vez; a especificação estável evita remontá-lo a cada rerun."""
    specification = session_cached(f"{name}-spec", context, lambda: build().to_dict())
    st.vega_lite_chart(spec=specification, width="stretch", theme=None, key=key)
