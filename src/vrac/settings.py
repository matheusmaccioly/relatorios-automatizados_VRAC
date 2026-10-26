"""Configuração não sigilosa, explícita e validada antes de acessar dados."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class ConfigurationError(ValueError):
    """Configuração inválida; não incluir o valor recebido na mensagem."""


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class DataMode(StrEnum):
    SYNTHETIC = "synthetic"
    REAL = "real"


@dataclass(frozen=True)
class Settings:
    environment: Environment = Environment.DEVELOPMENT
    data_mode: DataMode = DataMode.SYNTHETIC

    def __post_init__(self) -> None:
        if not isinstance(self.environment, Environment) or not isinstance(
            self.data_mode, DataMode
        ):
            raise ConfigurationError("Ambiente ou modo de dados inválido.")
        if self.environment == Environment.PRODUCTION and self.data_mode == DataMode.SYNTHETIC:
            raise ConfigurationError(
                "A demonstração sintética só está disponível em ambiente local."
            )


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Ler somente duas variáveis públicas, sem carregar .env ou secrets.toml."""
    source = os.environ if environ is None else environ
    try:
        environment = Environment(source.get("VRAC_ENVIRONMENT", "development"))
        data_mode = DataMode(source.get("VRAC_DATA_MODE", "synthetic"))
    except ValueError:
        raise ConfigurationError(
            "Configuração inválida. Confira VRAC_ENVIRONMENT e VRAC_DATA_MODE."
        ) from None
    return Settings(environment=environment, data_mode=data_mode)
