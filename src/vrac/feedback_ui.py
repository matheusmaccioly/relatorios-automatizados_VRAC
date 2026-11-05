"""Formulário e exportação explícita do feedback da demonstração."""

from datetime import UTC, datetime

import streamlit as st

from vrac.feedback import CATEGORIES, create_feedback, feedback_csv
from vrac.ui_kit import download_button


def render_feedback(
    execution_id: str, analysis: str, status: str, generated_at: datetime, *, prefix: str = "suite"
) -> None:
    with st.expander("Registrar feedback desta execução"):
        st.caption(
            f"Execução {execution_id}. Não inclua dados pessoais, nomes, matrículas, "
            "resultados ou outros dados acadêmicos no comentário."
        )
        st.info(
            "Registro temporário nesta sessão. Baixe o CSV antes de encerrar; "
            "o armazenamento operacional e o destino do feedback ainda serão definidos pelo time."
        )
        with st.form(f"{prefix}_feedback_form", clear_on_submit=True):
            category = st.selectbox(
                "Tipo de feedback", CATEGORIES, key=f"{prefix}_feedback_category"
            )
            comment = st.text_area(
                "Comentário breve", max_chars=1000, key=f"{prefix}_feedback_comment"
            )
            submitted = st.form_submit_button("Registrar feedback", key=f"{prefix}_feedback_submit")
        if submitted:
            try:
                record = create_feedback(
                    execution_id,
                    analysis,
                    status,
                    generated_at,
                    category,
                    comment,
                    datetime.now(UTC),
                )
                st.session_state.setdefault("feedback_records", []).append(record)
                st.success("Feedback registrado nesta sessão.")
            except ValueError as error:
                st.error(str(error))
        records = st.session_state.get("feedback_records", [])
        if records:
            st.caption(f"Registros temporários na sessão: {len(records)}.")
            download_button(
                "Baixar feedback da sessão (CSV)",
                feedback_csv(records),
                file_name="vrac-feedback-sintetico.csv",
                mime="text/csv",
                key=f"{prefix}_feedback_download",
            )
