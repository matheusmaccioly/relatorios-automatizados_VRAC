"""Porta de autorização: negar dados reais até integração institucional aprovada."""

from dataclasses import dataclass

from vrac.settings import DataMode, Environment, Settings


class AccessDenied(PermissionError):
    """Acesso bloqueado, sem revelar informações de infraestrutura."""


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str


def authorize_data_access(settings: Settings) -> AccessDecision:
    if settings.data_mode == DataMode.REAL:
        return AccessDecision(
            allowed=False,
            reason=(
                "Dados reais bloqueados. Autenticação, autorização e fontes institucionais "
                "ainda não foram configuradas e validadas."
            ),
        )
    if settings.environment not in (Environment.DEVELOPMENT, Environment.TEST):
        return AccessDecision(allowed=False, reason="Demonstração restrita ao ambiente local.")
    return AccessDecision(
        allowed=True, reason="Demonstração local com dados inteiramente sintéticos."
    )


def require_data_access(settings: Settings) -> None:
    decision = authorize_data_access(settings)
    if not decision.allowed:
        raise AccessDenied(decision.reason)
