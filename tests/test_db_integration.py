"""Prova real opt-in. Executar somente pelo operador fora da sessão do agente."""

from pathlib import Path

import pytest

from vrac.db.config import load_database_config


@pytest.mark.integration
def test_authorized_connection_select_one(request: pytest.FixtureRequest) -> None:
    config_path = request.config.getoption("--db-config")
    if not request.config.getoption("--run-db-integration") or not config_path:
        pytest.skip("Exige execução manual autorizada e configuração externa explícita.")
    from vrac.db.diagnostic import diagnose_database

    config = load_database_config(Path(config_path), workspace=Path(__file__).resolve().parents[1])
    result = diagnose_database(config)
    assert result["status"] == "passed", (
        "Diagnóstico não concluído; investigar pelo comando manual."
    )
