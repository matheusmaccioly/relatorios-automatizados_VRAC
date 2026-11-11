"""Análise temporal de alunos institucionais, com filtros e exportações do mesmo resultado."""

from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from vrac.analyses.academic_export import table_csv
from vrac.branding import Branding
from vrac.charts import academic_chart, render_png
from vrac.db.institutional_students import (
    FILTERS,
    calculate,
    load_filters,
    load_options,
    period_label,
    periods,
)
from vrac.demo_data import DemoDataError
from vrac.department_hierarchy import ALL_DEPARTMENTS
from vrac.web_charts import interactive_chart

PREFIX = "institutional_students_"


def clear() -> None:
    for key in list(st.session_state):
        if key.startswith(PREFIX):
            del st.session_state[key]


def _discard() -> None:
    for name in ("result", "png", "generated"):
        st.session_state.pop(PREFIX + name, None)


def label(value: str | None) -> str:
    if value is None:
        return "Não informado (nulo)"
    if value == "":
        return "Em branco (texto vazio)"
    return value.strip() or "Texto com espaços"


def render(branding: Branding, *, active: bool) -> None:
    st.subheader("Análise temporal")
    st.markdown("### Análise Geral")
    st.info("Direito (DIR/JUR) permanece pendente e não integra estes resultados.")
    if not active:
        return
    try:
        options = load_options()  # ACL/lote revalidados em cada rerun; sem cache global.
        if st.session_state.get(PREFIX + "scope") != options:
            clear()
            st.session_state[PREFIX + "scope"] = options
        autorun = st.session_state.pop("alunos_autorun", False)
        if autorun:
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
        departments = tuple(
            st.multiselect(
                "Departamentos",
                options.departments,
                default=options.departments,
                key=PREFIX + "departments",
            )
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
            for i, (field, title) in enumerate(FILTERS.items()):
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
        context = {
            "Departamentos": ", ".join(departments),
            "Semestre inicial": period_label(start),
            "Semestre final": period_label(end),
            **{
                title: ", ".join(label(v) for v in filters[key]) if key in filters else "Todos"
                for key, title in FILTERS.items()
            },
            "Direito": "Pendente; não incluído",
        }
        st.table(pd.DataFrame(context.items(), columns=["Filtro", "Valor"]))
        signature = (options, departments, start, end, filters)
        if st.session_state.get(PREFIX + "signature") != signature:
            _discard()
            st.session_state[PREFIX + "signature"] = signature
        if start > end:
            _discard()
            st.warning("O semestre inicial deve ser anterior ou igual ao final.")
            return
        run = st.button("Calcular Análise Geral", type="primary", key=PREFIX + "run")
        if run or autorun:
            _discard()
            st.session_state[PREFIX + "result"] = calculate(
                options, departments, start, end, filters
            )
            st.session_state[PREFIX + "generated"] = datetime.now(UTC)
        result = st.session_state.get(PREFIX + "result")
        if result is None:
            return
        st.subheader("Resultados calculados")
        st.caption(f"Dados institucionais pseudonimizados · lote {result.version}")
        st.write(result.narrative)
        table, spec = result.tables[0], result.charts[0]
        if result.status == "Sem eventos no recorte":
            st.info("Nenhum evento encontrado. Isso não comprova uma população igual a zero.")
        else:
            st.altair_chart(interactive_chart(result, spec, branding), width="stretch")
        st.dataframe(
            pd.DataFrame(table.rows, columns=table.columns), hide_index=True, width="stretch"
        )
        with st.expander("Regras e limites"):
            for note in result.notes:
                st.write(note)
        st.download_button(
            "Baixar resultados (CSV)",
            table_csv(result, table, st.session_state[PREFIX + "generated"], context),
            "alunos_analise_geral.csv",
            "text/csv",
            key=PREFIX + "csv",
        )
        if st.button("Preparar gráfico (PNG)", key=PREFIX + "prepare_png"):
            st.session_state[PREFIX + "png"] = render_png(
                lambda: academic_chart(result, spec, branding),
                context | {"Origem": result.source, "Lote": result.version},
            )
        if PREFIX + "png" in st.session_state:
            st.download_button(
                "Baixar gráfico (PNG)",
                st.session_state[PREFIX + "png"],
                "alunos_analise_geral.png",
                "image/png",
                key=PREFIX + "png_download",
            )
    except (DemoDataError, ValueError):
        clear()
        st.error(
            "Análise de alunos indisponível. Confira o acesso e tente novamente; "
            "resultados anteriores removidos."
        )
