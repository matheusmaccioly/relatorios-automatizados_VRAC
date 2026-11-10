"""Auth, isolamento, RPCs e contratos Supabase com rede inteiramente simulada."""

import time
from contextvars import copy_context
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from vrac.analyses.academic_fixture import load_fixture
from vrac.authorization import AccessDenied, authorize_data_access
from vrac.db import supabase_reader as reader
from vrac.demo_data import DemoDataError, load_academic_source
from vrac.settings import ConfigurationError, DemoSource, Environment, Settings
from vrac.supabase_auth import (
    AuthenticationError,
    SupabaseConfig,
    SupabaseSession,
    current_session,
    session_scope,
    sign_in,
    sign_out,
    verify_session,
)
from vrac.ui import VIEWS

SETTINGS = Settings(demo_source=DemoSource.SUPABASE)
CONFIG = SupabaseConfig("https://example.supabase.co", "sb_publishable_test")


class Client:
    def __init__(self) -> None:
        self.calls = []
        self.departments = ["SINT-A"]
        self.user_id = "test-user-a"
        self.anonymous = False
        self.fail = False
        self.payload = {}
        self.auth = SimpleNamespace(
            get_user=self.get_user,
            sign_out=self.logout,
            refresh_session=self.refresh,
            sign_in_with_password=self.login,
        )
        self.postgrest = SimpleNamespace(auth=lambda jwt: self.calls.append(("jwt", jwt)))

    def get_user(self, jwt):
        if self.fail:
            raise RuntimeError("password=PRIVATE access_token=PRIVATE")
        self.calls.append(("get_user", jwt))
        return SimpleNamespace(user=SimpleNamespace(id=self.user_id, is_anonymous=self.anonymous))

    def rpc(self, name, params=None):
        self.calls.append((name, params))
        if self.fail:
            raise RuntimeError("refresh_token=PRIVATE")
        data = (
            {
                "synthetic": True,
                "departments": self.departments,
                "periods": ["2026.1"],
                "version": "synthetic-test",
            }
            if name == "vrac_options"
            else self.payload
        )
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=data))

    def login(self, credentials):
        if credentials["password"] == "fail":
            raise RuntimeError("password=PRIVATE")
        return SimpleNamespace(
            user=SimpleNamespace(id=self.user_id),
            session=SimpleNamespace(
                access_token="access-test",
                refresh_token="refresh-test",
                expires_at=time.time() + 3600,
            ),
        )

    def refresh(self, token):
        self.calls.append(("refresh", token))
        return self.login({"password": "ok"})

    def logout(self, options):
        self.calls.append(("logout", options))
        if self.fail:
            raise RuntimeError("PRIVATE")


def session(client=None):
    client = client or Client()
    return SupabaseSession(
        client,
        client.user_id,
        "access-test",
        "refresh-test",
        time.time() + 3600,
        ("SINT-A",),
        time.time() + 900,
        CONFIG.url,
    )


def payload():
    source = load_fixture("SINT-A")
    data = {
        name: [asdict(r) for r in getattr(source, name)]
        for name in (
            "history",
            "workloads",
            "allocations",
            "functions",
            "appointments",
            "students",
            "student_history",
            "scholarships",
        )
    }
    data.update(
        register=[asdict(r) for r in source.faculty.register],
        real_hours=[asdict(r) for r in source.faculty.real_hours],
        synthetic=True,
        version="synthetic-test",
        periods=list(source.periods),
        policy=asdict(source.policy),
        demo_faculty=[],
        demo_allocations=[],
    )
    return data


def test_supabase_requires_verified_identity_including_production():
    assert not authorize_data_access(SETTINGS).allowed
    production = Settings(environment=Environment.PRODUCTION, demo_source=DemoSource.SUPABASE)
    assert not authorize_data_access(production).allowed
    with session_scope(session()):
        assert authorize_data_access(production).allowed
    with pytest.raises(AccessDenied):
        current_session()


def test_context_restores_identity_and_does_not_leak_into_other_context():
    empty_context = copy_context()
    first, second = session(), session()
    second.user_id = "test-user-b"
    with session_scope(first):
        with session_scope(second):
            assert current_session() is second
        assert current_session() is first
        with pytest.raises(AccessDenied):
            empty_context.run(current_session)


@pytest.mark.parametrize("change", ["expired", "unverified", "no_departments"])
def test_invalid_session_cannot_install_context(change):
    identity = session()
    if change == "expired":
        identity.expires_at = 0
    elif change == "unverified":
        identity.verified_until = 0
    else:
        identity.departments = ()
    with pytest.raises(AccessDenied), session_scope(identity):
        pytest.fail("A sessão inválida não pode entrar no contexto.")


@pytest.mark.parametrize(
    "url,key",
    [
        ("http://example.supabase.co", "sb_publishable_test"),
        ("https://example.supabase.co.attacker.invalid", "sb_publishable_test"),
        ("https://example.supabase.co", "sb_secret_test"),
        ("https://example.supabase.co?token=PRIVATE", "sb_publishable_test"),
    ],
)
def test_config_rejects_non_tls_external_hosts_and_administrative_keys(url, key):
    with pytest.raises(ConfigurationError) as error:
        SupabaseConfig(url, key)
    assert "PRIVATE" not in str(error.value)


def test_sign_in_verifies_user_and_database_grants(monkeypatch):
    client = Client()
    monkeypatch.setattr("vrac.supabase_auth._client", lambda _: client)
    identity = sign_in(CONFIG, "test@example.invalid", "not-a-real-password")
    assert identity.user_id == client.user_id and identity.departments == ("SINT-A",)
    assert any(name == "get_user" for name, _ in client.calls)
    assert any(name == "vrac_options" for name, _ in client.calls)
    assert "access-test" not in repr(identity)


@pytest.mark.parametrize("kind", ["revoked", "wrong_user", "anonymous", "no_grants"])
def test_verification_failure_invalidates_previous_authorization(kind):
    identity = session()
    if kind == "revoked":
        identity.client.fail = True
    elif kind == "wrong_user":
        identity.client.user_id = "another-user"
    elif kind == "anonymous":
        identity.client.anonymous = True
    else:
        identity.client.departments = []
    with pytest.raises(AuthenticationError) as error:
        verify_session(identity)
    assert "PRIVATE" not in str(error.value)
    assert identity.departments == () and identity.verified_until == 0


def test_refresh_is_explicit_and_logout_clears_tokens_even_on_failure():
    identity = session()
    identity.expires_at = time.time() + 5
    verify_session(identity)
    assert ("refresh", "refresh-test") in identity.client.calls
    identity.client.fail = True
    sign_out(identity)
    assert not identity.access_token and not identity.refresh_token
    assert identity.departments == ()


def test_reader_preserves_all_contract_values_and_uses_bound_rpc_parameters():
    identity = session()
    identity.client.payload = payload()
    with session_scope(identity):
        source = load_academic_source(SETTINGS, department="SINT-A")
    original = load_fixture("SINT-A")
    assert source.workloads == original.workloads
    assert source.faculty.register == original.faculty.register
    assert source.students == original.students
    assert source.scholarships == original.scholarships
    assert ("vrac_snapshot", {"p_departments": ["SINT-A"]}) in identity.client.calls
    assert any(r.real_hours == 0 for r in source.workloads)
    assert any(r.real_hours is None for r in source.workloads)


def test_reader_rejects_foreign_department_before_snapshot_and_never_falls_back():
    identity = session()
    with session_scope(identity), pytest.raises(DemoDataError):
        load_academic_source(SETTINGS, department="SINT-B")
    assert not any(name == "vrac_snapshot" for name, _ in identity.client.calls)
    identity.client.fail = True
    with session_scope(identity), pytest.raises(DemoDataError) as error:
        load_academic_source(SETTINGS, department="SINT-A")
    assert "PRIVATE" not in str(error.value)


def test_decode_dates_and_reject_incomplete_snapshot():
    data = payload()
    data["history"][0]["reference_date"] = "2026-01-01T00:00:00"
    assert isinstance(reader._decode(data, "history")[0].reference_date, datetime)
    del data["students"]
    with pytest.raises(DemoDataError, match="incompleto"):
        reader._academic(data, "SINT-A")


def test_login_screen_blocks_all_data_before_any_connection(monkeypatch):
    monkeypatch.setenv("VRAC_DEMO_SOURCE", "supabase")

    def forbidden(*args, **kwargs):
        pytest.fail("A tela sem login não pode consultar dados.")

    monkeypatch.setattr("vrac.ui.load_demo_options", forbidden)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    assert not app.exception
    assert [x.label for x in app.text_input] == ["E-mail", "Senha"]
    assert not app.dataframe and not app.tabs


def test_login_and_logout_clear_previous_results_and_files(monkeypatch):
    monkeypatch.setenv("VRAC_DEMO_SOURCE", "supabase")
    identity = session()
    identity.client.payload = payload()
    monkeypatch.setattr("vrac.auth_ui.load_supabase_config", lambda: CONFIG)
    monkeypatch.setattr("vrac.auth_ui.sign_in", lambda *args: identity)
    monkeypatch.setattr("vrac.auth_ui.verify_session", lambda s: None)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    app.text_input(key="vrac_login_email").set_value("test@example.invalid")
    app.text_input(key="vrac_login_password").set_value("synthetic-password")
    app.button[0].click().run()
    assert not app.exception and len(app.tabs) == len(VIEWS)
    app.session_state["vrac_artifact_cache"] = {"previous-file": b"PRIVATE"}
    app.session_state["feedback_records"] = ["PRIVATE"]
    app.button(key="vrac_sign_out").click().run()
    assert not app.exception and not app.tabs
    assert len(app.text_input) == 2
    for key in ("vrac_artifact_cache", "feedback_records", "vrac_auth_session"):
        with pytest.raises(KeyError):
            app.session_state[key]


def test_supabase_download_refuses_unauthenticated_access(monkeypatch):
    from vrac.ui_kit import download_button

    monkeypatch.setenv("VRAC_DEMO_SOURCE", "supabase")
    with pytest.raises(AccessDenied):
        download_button("Baixar", b"PRIVATE", file_name="synthetic.csv", mime="text/csv")


def test_supabase_export_has_exact_bytes_and_no_public_media_endpoint(monkeypatch):
    import base64
    import re

    from vrac.ui_kit import download_button

    monkeypatch.setenv("VRAC_DEMO_SOURCE", "supabase")
    monkeypatch.setattr("vrac.ui_kit.st.button", lambda *args, **kwargs: True)
    monkeypatch.setattr("vrac.ui_kit.st.caption", lambda *args, **kwargs: None)
    rendered = []
    monkeypatch.setattr(
        "streamlit.components.v1.html", lambda content, **kwargs: rendered.append(content)
    )
    content = "DEMONSTRAÇÃO;zero;nulo\r\nSINT-A;0;\r\n".encode()
    with session_scope(session()):
        download_button("Baixar", lambda: content, file_name="synthetic.csv", mime="text/csv")
    uri = re.search('href="data:text/csv;base64,([^"]+)"', rendered[0])
    assert uri and base64.b64decode(uri[1]) == content
    assert "access-test" not in rendered[0] and "/media/" not in rendered[0]
    assert 'download="synthetic.csv"' in rendered[0]
