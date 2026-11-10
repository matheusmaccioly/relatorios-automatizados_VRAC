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
    PSEUDONYMIZED = "pseudonymized"
    REAL = "real"


class DemoSource(StrEnum):
    MEMORY = "memory"
    POSTGRES = "postgres"
    SUPABASE = "supabase"


@dataclass(frozen=True)
class Settings:
    environment: Environment = Environment.DEVELOPMENT
    data_mode: DataMode = DataMode.SYNTHETIC
    demo_source: DemoSource = DemoSource.MEMORY

    def __post_init__(self) -> None:
        if (
            not isinstance(self.environment, Environment)
            or not isinstance(self.data_mode, DataMode)
            or not isinstance(self.demo_source, DemoSource)
        ):
            raise ConfigurationError("Ambiente ou modo de dados inválido.")
        if self.data_mode == DataMode.PSEUDONYMIZED and self.demo_source != DemoSource.SUPABASE:
            raise ConfigurationError("A origem pseudonimizada exige Supabase autenticado.")
        if (
            self.environment == Environment.PRODUCTION
            and self.data_mode == DataMode.SYNTHETIC
            and self.demo_source != DemoSource.SUPABASE
        ):
            raise ConfigurationError(
                "A demonstração sintética só está disponível em ambiente local."
            )


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Ler somente três variáveis públicas, sem carregar .env ou secrets.toml."""
    source = os.environ if environ is None else environ
    try:
        environment = Environment(source.get("VRAC_ENVIRONMENT", "development"))
        data_mode = DataMode(source.get("VRAC_DATA_MODE", "synthetic"))
        demo_source = DemoSource(source.get("VRAC_DEMO_SOURCE", "memory"))
    except ValueError:
        raise ConfigurationError(
            "Configuração inválida. Confira VRAC_ENVIRONMENT, VRAC_DATA_MODE e VRAC_DEMO_SOURCE."
        ) from None
    return Settings(environment=environment, data_mode=data_mode, demo_source=demo_source)
