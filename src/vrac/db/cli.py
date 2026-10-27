"""Comandos do operador: nenhum acesso ou leitura de configuração sem --execute."""

import argparse
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from vrac.db.config import DatabaseConfig, assert_ready, load_database_config
from vrac.db.errors import (
    DatabaseConfigurationError,
    DatabaseOperationError,
    classify_database_error,
)
from vrac.db.private_io import (
    PrivateOutputError,
    create_private_run_directory,
    write_private_report,
)


class UsageError(ValueError):
    """Não repetir valores arbitrários de argumentos em mensagens de uso."""


class SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UsageError(
            "Argumentos inválidos. Consulte --help; não passe credenciais na linha de comando."
        )


def _parser() -> argparse.ArgumentParser:
    parser = SafeParser(
        prog="vrac-db",
        description=(
            "Descoberta manual autorizada. Conexão e inventário institucionais NÃO VALIDADOS "
            "nesta entrega. Sem --execute nenhum arquivo de configuração é lido."
        ),
        allow_abbrev=False,
    )
    subcommands = parser.add_subparsers(dest="command", required=True, parser_class=SafeParser)
    for command, help_text in (
        ("diagnose", "Provar conexão com SELECT 1, sem dados ou identidade."),
        ("inventory", "Inventariar somente o banco e os schemas aprovados, sem linhas pessoais."),
    ):
        sub = subcommands.add_parser(command, help=help_text, allow_abbrev=False)
        sub.add_argument("--config", type=Path, help="Arquivo TOML externo, privado e absoluto.")
        sub.add_argument(
            "--output-dir",
            type=Path,
            help="Diretório externo local. Padrão: vrac-discovery-private ao lado da configuração.",
        )
        sub.add_argument(
            "--execute",
            action="store_true",
            help="Executar manualmente no ambiente autorizado, fora da sessão do agente.",
        )
    return parser


def _workspace() -> Path:
    # Comandos são executados a partir do repositório. Não procurar configuração privada.
    source_root = Path(__file__).resolve().parents[3]
    return source_root if (source_root / "pyproject.toml").is_file() else Path.cwd().resolve()


def _inventory(config: DatabaseConfig) -> dict[str, object]:
    from vrac.db.connection import database_session
    from vrac.db.inventory import collect_inventory

    with database_session(config) as connection:
        return collect_inventory(connection, config)


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if not args.execute:
            print(
                "Execução bloqueada. Use --execute somente no ambiente autorizado, fora do agente."
            )
            return 2
        if args.config is None:
            raise UsageError("Informe --config com um arquivo externo privado e absoluto.")
        config = load_database_config(args.config, workspace=_workspace())
        assert_ready(config)
        execution_id = str(uuid4())
        base = args.output_dir or args.config.resolve().parent / "vrac-discovery-private"
        run_directory = create_private_run_directory(base, execution_id, workspace=_workspace())
        extracted_at = datetime.now(UTC).isoformat()
        try:
            if args.command == "diagnose":
                from vrac.db.diagnostic import diagnose_database

                result = diagnose_database(config)
            else:
                result = _inventory(config)
        except DatabaseOperationError as error:
            result = {"status": "failed", **asdict(error.issue)}
        except Exception as error:
            result = {
                "status": "failed",
                **asdict(classify_database_error(error, stage=args.command)),
            }
        report = {
            "execution_id": execution_id,
            "started_at": extracted_at,
            "finished_at": datetime.now(UTC).isoformat(),
            "command": args.command,
            "format_version": "discovery-v1",
            "read_privileges_validated_by_code": False,
            "result": result,
        }
        write_private_report(run_directory, args.command, report)
        print(f"Execução {execution_id}: saída privada gravada no diretório configurado.")
        if result["status"] in {"passed", "valid"}:
            print("Etapa técnica concluída. Confirme limites e privilégios com o DBA.")
            return 0
        if result["status"] == "partial":
            print("Inventário parcial. Consulte os avisos no arquivo privado.")
            return 3
        print("Etapa não concluída. Consulte a categoria sanitizada no arquivo privado.")
        return 1
    except (UsageError, DatabaseConfigurationError) as error:
        print(str(error), file=sys.stderr)
        return 2
    except PrivateOutputError as error:
        print(str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Execução cancelada pelo operador.", file=sys.stderr)
        return 130
    except Exception:
        print("Falha na ferramenta. Nenhum detalhe privado foi exibido.", file=sys.stderr)
        return 1
