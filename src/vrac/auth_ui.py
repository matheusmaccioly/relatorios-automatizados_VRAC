"""Entrada obrigatória para o Supabase, usando os componentes e o tema institucionais."""

import streamlit as st

from vrac.supabase_auth import (
    AuthenticationError,
    SupabaseSession,
    load_supabase_config,
    sign_in,
    sign_out,
    verify_session,
)

SESSION_KEY = "vrac_auth_session"


def _clear() -> None:
    """Remover dados, arquivos, feedback, widgets e credenciais da sessão anterior."""
    st.session_state.clear()


def require_login() -> SupabaseSession:
    config = load_supabase_config()
    session = st.session_state.get(SESSION_KEY)
    if session is not None and session.project_url != config.url:
        sign_out(session)
        _clear()
        session = None
    if session is not None:
        previous_departments = session.departments
        try:
            verify_session(session)
        except AuthenticationError as error:
            sign_out(session)
            _clear()
            st.error(str(error))
            st.stop()
        if previous_departments != session.departments:
            _clear()
            st.session_state[SESSION_KEY] = session
        with st.container(key="vrac-auth-status"):
            st.caption("Acesso autenticado · somente departamentos autorizados")
            if st.button("Sair", key="vrac_sign_out"):
                sign_out(session)
                _clear()
                st.rerun()
        return session

    st.subheader("Entrar")
    st.write("Use sua conta autorizada para acessar as análises acadêmicas.")
    with st.form("vrac_login", clear_on_submit=True):
        email = st.text_input("E-mail", key="vrac_login_email", max_chars=254)
        password = st.text_input(
            "Senha", type="password", key="vrac_login_password", max_chars=1024
        )
        submitted = st.form_submit_button("Entrar", type="primary")
    if submitted:
        try:
            session = sign_in(config, email, password)
            _clear()
            st.session_state[SESSION_KEY] = session
            st.rerun()
        except AuthenticationError as error:
            st.error(str(error))
    st.caption("O acesso é liberado pelo responsável. Esta tela não permite criar contas.")
    st.stop()
