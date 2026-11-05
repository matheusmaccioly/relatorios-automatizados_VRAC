"""Supabase Auth: cliente exclusivo de cada sessão e autorização verificada no servidor."""

import os
import time
import tomllib
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from vrac.authorization import AccessDenied
from vrac.settings import ConfigurationError

if TYPE_CHECKING:
    from supabase import Client


class AuthenticationError(RuntimeError):
    """Erro público: nunca propagar resposta, senha, JWT ou refresh token."""


@dataclass(frozen=True)
class SupabaseConfig:
    url: str
    publishable_key: str = field(repr=False)

    def __post_init__(self) -> None:
        parsed = urlsplit(self.url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or not parsed.hostname.endswith(".supabase.co")
            or parsed.username
            or parsed.password
            or parsed.port
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
            or not self.publishable_key.startswith("sb_publishable_")
        ):
            raise ConfigurationError("Confira a URL HTTPS e a chave pública do Supabase.")


def load_supabase_config(environ: Mapping[str, str] | None = None) -> SupabaseConfig:
    """Ler só configuração pública; nunca carregar .env, secrets ou chave administrativa."""
    source = os.environ if environ is None else environ
    packaged = files("vrac").joinpath("supabase.public.toml")
    path = (
        packaged
        if packaged.is_file()
        else (Path(__file__).resolve().parents[2] / "config/supabase.public.toml")
    )
    try:
        public = tomllib.loads(path.read_text(encoding="utf-8"))
        return SupabaseConfig(
            source.get("VRAC_SUPABASE_URL", public["url"]),
            source.get("VRAC_SUPABASE_PUBLISHABLE_KEY", public["publishable_key"]),
        )
    except (OSError, KeyError, ValueError):
        raise ConfigurationError(
            "Configuração pública do Supabase indisponível ou inválida."
        ) from None


@dataclass(repr=False)
class SupabaseSession:
    client: "Client"
    user_id: str
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    expires_at: float
    departments: tuple[str, ...] = ()
    verified_until: float = 0
    project_url: str = ""


_SESSION: ContextVar[SupabaseSession | None] = ContextVar("vrac_supabase_session", default=None)


def current_session() -> SupabaseSession:
    session = _SESSION.get()
    if (
        session is None
        or not session.departments
        or min(session.expires_at, session.verified_until) <= time.time()
    ):
        raise AccessDenied("Sessão ausente ou expirada. Entre novamente.")
    return session


@contextmanager
def session_scope(session: SupabaseSession) -> Iterator[None]:
    """Contexto por execução/thread; jamais compartilhar cliente ou JWT entre usuários."""
    token = _SESSION.set(session)
    try:
        current_session()
        yield
    finally:
        _SESSION.reset(token)


def _client(config: SupabaseConfig) -> "Client":
    try:
        import httpx

        from supabase import ClientOptions, create_client

        return create_client(
            config.url,
            config.publishable_key,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False,
                postgrest_client_retry=False,
                httpx_client=httpx.Client(timeout=15, verify=True, trust_env=False),
            ),
        )
    except Exception:
        raise AuthenticationError("Não foi possível iniciar o acesso seguro ao Supabase.") from None


def sign_in(config: SupabaseConfig, email: str, password: str) -> SupabaseSession:
    if not email.strip() or not password:
        raise AuthenticationError("Informe seu e-mail e sua senha.")
    client = _client(config)
    try:
        response = client.auth.sign_in_with_password({"email": email.strip(), "password": password})
        if response.user is None or response.session is None:
            raise ValueError
        session = SupabaseSession(
            client,
            str(response.user.id),
            response.session.access_token,
            response.session.refresh_token,
            response.session.expires_at or 0,
            project_url=config.url,
        )
        verify_session(session)
        return session
    except AuthenticationError:
        raise
    except Exception:
        raise AuthenticationError(
            "Não foi possível entrar. Confira suas credenciais ou tente novamente."
        ) from None


def verify_session(session: SupabaseSession) -> None:
    """Verificar Auth e ACL a cada rerun, inclusive antes de reutilizar resultados/exportações."""
    session.verified_until = 0
    session.departments = ()
    try:
        if session.expires_at <= time.time() + 60:
            refreshed = session.client.auth.refresh_session(session.refresh_token)
            if refreshed.session is None:
                raise ValueError
            session.access_token = refreshed.session.access_token
            session.refresh_token = refreshed.session.refresh_token
            session.expires_at = refreshed.session.expires_at or 0
        response = session.client.auth.get_user(session.access_token)
        if response is None or response.user is None or str(response.user.id) != session.user_id:
            raise ValueError
        if getattr(response.user, "is_anonymous", False):
            raise ValueError
        session.client.postgrest.auth(session.access_token)
        options = session.client.rpc("vrac_options").execute().data
        if not isinstance(options, dict) or options.get("synthetic") is not True:
            raise ValueError
        departments = options.get("departments")
        if (
            not isinstance(departments, list)
            or not departments
            or any(not isinstance(d, str) or not d for d in departments)
        ):
            raise AuthenticationError(
                "Conta autenticada sem departamentos liberados. Solicite acesso ao responsável."
            )
        session.departments = tuple(departments)
        session.verified_until = min(time.time() + 900, session.expires_at)
    except AuthenticationError:
        raise
    except Exception:
        raise AuthenticationError(
            "Não foi possível validar seu acesso. Entre novamente ou tente mais tarde."
        ) from None


def sign_out(session: SupabaseSession) -> None:
    try:
        session.client.auth.sign_out({"scope": "local"})
    except Exception:
        pass  # A sessão local é eliminada mesmo se o provedor estiver indisponível.
    finally:
        session.departments = ()
        session.verified_until = 0
        session.access_token = session.refresh_token = ""
