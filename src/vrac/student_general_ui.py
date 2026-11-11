"""Análise temporal de alunos institucionais, com filtros e exportações do mesmo resultado.

A tela segue o mesmo esqueleto das análises docentes: etapas numeradas no painel de
filtros, resultados num painel próprio, bloco de exportação no topo, gráficos em cartões
com PNG e tabela recolhida com CSV, e regras e limitações no ícone de informação.
"""

from datetime import UTC, datetime

import streamlit as st

from vrac.academic_ui import _render_result, export_box
from vrac.analyses.academic_export import report_zip
from vrac.branding import Branding
from vrac.db.institutional_students import (
    FILTERS,
    calculate,
    load_filters,
    load_options,
    period_label,
    periods,
)
from vrac.demo_data import DemoDataError
from vrac.department_hierarchy import ALL_CENTERS, ALL_DEPARTMENTS, institutional_hierarchy
from vrac.provenance import INSTITUTIONAL_SOURCE, nature
from vrac.ui_kit import filter_review, info_button, scroll_to, step, used_filters

PREFIX = "institutional_students_"
# Prefixo dos componentes compartilhados (cartões, downloads e ícones de informação).
SHARED = PREFIX.rstrip("_")
QUESTION = "Como evoluíram as matrículas no período?"
DESCRIPTION = (
    "Análise temporal › Análise Geral: matriculados, bolsistas matriculados, formados e "
    "ingressantes por semestre, contados em matrículas distintas."
)
SOURCE_NOTES = (
    "Direito (DIR/JUR) permanece pendente e não integra estes resultados.",
    "Matrículas distintas não equivalem a pessoas únicas.",
    "Os departamentos disponíveis seguem o seu acesso.",
)
FILTER_NOTES = (
    "Seleção vazia inclui todos os valores; “Não informado (nulo)” e “Em branco” são "
    "valores distintos e podem ser escolhidos.",
    "Código e nome do curso são filtros separados; cursos não são unidos pelo nome.",
    "Situação atual é cadastral e não descreve o semestre de cada evento.",
    "Forma de ingresso não substitui o processo seletivo, indisponível nesta fonte.",
)


def clear() -> None:
    for key in list(st.session_state):
        if key.startswith(PREFIX):
            del st.session_state[key]


def _discard() -> None:
    for name in ("result", "generated"):
        st.session_state.pop(PREFIX + name, None)


def _reset_filters() -> None:
    """Executado antes dos widgets: volta ao intervalo completo e aos filtros vazios."""
    _discard()
    for field in (*FILTERS, "start", "end"):
        st.session_state.pop(PREFIX + field, None)


def label(value: str | None) -> str:
    if value is None:
        return "Não informado (nulo)"
    if value == "":
        return "Em branco (texto vazio)"
    return value.strip() or "Texto com espaços"


def render(branding: Branding, *, active: bool) -> None:
    if not active:
        return
    try:
        _render(branding)
    except (DemoDataError, ValueError):
        clear()
        st.error(
            "Análise de alunos indisponível. Confira o acesso e tente novamente; "
            "resultados anteriores removidos."
        )


def _render(branding: Branding) -> None:
    with st.container(key="vrac-panel-alunos-geral-filters"):
        step(1, "Defina o recorte")
        options = load_options()  # ACL/lote revalidados em cada rerun; sem cache global.
        if st.session_state.get(PREFIX + "scope") != options:
            clear()
            st.session_state[PREFIX + "scope"] = options
        hierarchy = institutional_hierarchy(options.departments)
        centers = (ALL_CENTERS, *hierarchy.centers)
        center_key = PREFIX + "center"
        if st.session_state.get(center_key, ALL_CENTERS) not in centers:
            st.session_state[center_key] = ALL_CENTERS
        autorun = st.session_state.pop("alunos_autorun", False)
        if autorun:
            st.session_state[center_key] = ALL_CENTERS
            st.session_state[PREFIX + "center_scope"] = ALL_CENTERS
            requested = st.session_state.get("alunos_department", ALL_DEPARTMENTS)
            if requested == ALL_DEPARTMENTS:
                st.session_state[PREFIX + "departments"] = list(options.departments)
            elif requested in options.departments:
                st.session_state[PREFIX + "departments"] = [requested]
            else:
                _discard()
                st.warning(
                    "O departamento solicitado está pendente ou não está autorizado para alunos."
                )
                return
        first, second = st.columns(2)
        with first:
            center = st.selectbox(
                "Centro", centers, key=center_key, help="Restringe a lista de departamentos."
            )
        available = hierarchy.departments_for(center)
        if st.session_state.get(PREFIX + "center_scope") != center:
            _discard()
            st.session_state[PREFIX + "departments"] = list(available)
            st.session_state[PREFIX + "center_scope"] = center
        with second:
            departments = tuple(
                st.multiselect(
                    "Departamentos",
                    available,
                    default=available,
                    key=PREFIX + "departments",
                )
            )
        with st.container(horizontal=True, vertical_alignment="center"):
            st.caption(f"{hierarchy.note} Lote de dados {options.batch[:8]}.")
            info_button(
                (nature(INSTITUTIONAL_SOURCE), *SOURCE_NOTES),
                key=f"{SHARED}-fonte",
                title="Sobre estes dados",
            )
        if not departments:
            _discard()
            st.info("Selecione ao menos um departamento.")
            return
        facets = load_filters(options, departments)
        if st.session_state.get(PREFIX + "facet_scope") != (departments, facets):
            _discard()
            for field in FILTERS:
                st.session_state.pop(PREFIX + field, None)
            st.session_state[PREFIX + "facet_scope"] = (departments, facets)
        step(2, "Refine os filtros, se precisar, e calcule")
        st.caption(
            "Seleções vazias incluem todos os valores disponíveis. "
            "Ao mudar um filtro, calcule novamente para atualizar resultados e arquivos."
        )
        axis = periods(options.start, options.end)
        left, right = st.columns(2)
        with left:
            start = st.selectbox(
                "Semestre inicial", axis, format_func=period_label, key=PREFIX + "start"
            )
        with right:
            end = st.selectbox(
                "Semestre final",
                axis,
                index=len(axis) - 1,
                format_func=period_label,
                key=PREFIX + "end",
            )
        filters = {}
        with st.expander("Filtros acadêmicos", expanded=True):
            columns = st.columns(3)
            shown = [item for item in FILTERS.items() if item[0] != "sigla_centro"]
            for i, (field, title) in enumerate(shown):
                with columns[i % 3]:
                    # Índices evitam ambiguidades do widget entre None e nenhuma seleção.
                    chosen = st.multiselect(
                        title,
                        range(len(facets[field])),
                        format_func=lambda index, f=field: label(facets[f][index]),
                        key=PREFIX + field,
                        placeholder="Todos",
                    )
                    if chosen:
                        filters[field] = [facets[field][index] for index in chosen]
            with st.container(horizontal=True, horizontal_alignment="right"):
                info_button(
                    FILTER_NOTES, key=f"{SHARED}-filtros", title="Como estes filtros funcionam"
                )
        if center != ALL_CENTERS:
            filters["sigla_centro"] = [center]
        context = {
            "Centro": center,
            "Departamentos": ", ".join(departments),
            "Semestre inicial": period_label(start),
            "Semestre final": period_label(end),
            **{
                title: ", ".join(label(v) for v in filters[key]) if key in filters else "Todos"
                for key, title in FILTERS.items()
                if key != "sigla_centro"
            },
            "Direito": "Pendente; não incluído",
        }
        signature = (options, center, departments, start, end, filters)
        if st.session_state.get(PREFIX + "signature") != signature:
            _discard()
            st.session_state[PREFIX + "signature"] = signature
        if start > end:
            _discard()
            st.warning("O semestre inicial deve ser anterior ou igual ao final.")
            return
        with st.container(horizontal=True, vertical_alignment="center"):
            run = st.button("Calcular resultados", type="primary", key=PREFIX + "run")
            st.button(
                "Limpar filtros",
                key=PREFIX + "reset",
                type="tertiary",
                on_click=_reset_filters,
                help="Restaura o intervalo completo e os filtros vazios, mantendo os "
                "departamentos escolhidos.",
            )
        with st.expander("Conferir filtros selecionados", expanded=False):
            filter_review(context)
    if run or autorun:
        _discard()
        with st.spinner("Calculando a análise..."):
            st.session_state[PREFIX + "result"] = calculate(
                options, departments, start, end, filters
            )
        st.session_state[PREFIX + "generated"] = datetime.now(UTC)
    result = st.session_state.get(PREFIX + "result")
    if result is None:
        with st.container(key="vrac-empty-alunos-geral"):
            st.info(
                "Recorte pronto. Clique em Calcular resultados para ver os gráficos "
                "e liberar os arquivos deste recorte."
            )
        return
    _results(result, context, branding, run=run or autorun)


def _results(result, context: dict[str, str], branding: Branding, *, run: bool) -> None:
    generated_at = st.session_state[PREFIX + "generated"]
    export_context = context | {
        "Origem": result.source,
        "Lote": result.version,
        "Cálculo (UTC)": generated_at.isoformat(),
    }
    with st.container(key="vrac-panel-alunos-geral-results"):
        st.subheader("Resultados calculados")
        st.caption(
            f"Recorte: {context['Departamentos']} · {context['Semestre inicial']} a "
            f"{context['Semestre final']}. Os resultados abaixo correspondem ao último "
            "cálculo com estes filtros."
        )
        used_filters(
            context,
            f"{nature(result.source)} · lote {result.version} · "
            f"cálculo {generated_at:%d/%m/%Y %H:%M:%S} UTC",
        )
        export_slot = st.container()
        if result.status == "Sem eventos no recorte":
            st.info("Nenhum evento encontrado. Isso não comprova uma população igual a zero.")
        images = _render_result(
            result, branding, generated_at, prefix=SHARED, export_context=export_context
        )

    def package(include: tuple[str, ...] | None = None) -> bytes:
        """Montado no clique, com os mesmos CSV e PNG da tela."""
        return report_zip(
            (result,),
            generated_at,
            {name: build() for name, build in images.items()},
            {},
            export_context,
        )

    export_box(
        export_slot,
        prefix=SHARED,
        available=(str(result.kind),),
        package=package,
        branding=branding,
        generated_at=generated_at,
        pdf=False,
    )
    if run:
        scroll_to("vrac-panel-alunos-geral-results")
