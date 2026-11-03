"""Diagnóstico manual e sanitizado da conexão PostgreSQL sintética fixa."""

import argparse

from vrac.db import synthetic_postgres as reader


def failure_category(error: Exception) -> str:
    """Classificar localmente, sem retornar mensagem ou parâmetros do driver."""
    message = str(error).lower()
    code = getattr(error, "sqlstate", None) or ""
    if code.startswith("28") or "password authentication failed" in message:
        return "AUTENTICACAO"
    if "no password supplied" in message or "fe_sendauth" in message:
        return "AUTENTICACAO"
    if "certificate" in message or "ssl" in message or "tls" in message:
        return "CERTIFICADO_OU_TLS"
    if code == "3D000":
        return "BANCO_NAO_ENCONTRADO"
    if code == "42501":
        return "PERMISSAO"
    if code == "42P01":
        return "FONTE_SINTETICA_AUSENTE"
    if "connection refused" in message or "timeout expired" in message:
        return "SERVIDOR_INDISPONIVEL"
    return "OUTRA_FALHA"


def diagnose() -> str:
    """Ler apenas metadados e opções fixas; sem criar nem modificar objetos."""
    try:
        from psycopg import IsolationLevel

        with reader._connect() as connection:
            connection.isolation_level = IsolationLevel.REPEATABLE_READ
            records = reader._rows(connection, reader.Query.METADATA)
            if len(records) != 1:
                return "IDENTIDADE_SINTETICA_NAO_CONFIRMADA"
            metadata = records[0]
            if not (
                metadata.get("synthetic") is True
                and metadata.get("version") == reader.VERSION
                and metadata.get("database_name") == reader.DATABASE
                and metadata.get("role_name") == reader.READER
                and metadata.get("transaction_read_only") == "on"
                and metadata.get("ssl") is True
            ):
                return "IDENTIDADE_SINTETICA_NAO_CONFIRMADA"
            reader._options(connection)
            return "CONEXAO_E_OPCOES_OK"
    except Exception as error:
        return failure_category(error)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Consultar a origem sintética local")
    if not parser.parse_args().execute:
        print("Sem conexão. Use --execute para verificar a origem sintética local.")
        return 2
    result = diagnose()
    print(f"Resultado: {result}")
    return 0 if result == "CONEXAO_E_OPCOES_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
