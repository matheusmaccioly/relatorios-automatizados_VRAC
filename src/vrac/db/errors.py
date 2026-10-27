"""Classificação local de falhas sem divulgar mensagens, consultas ou identidades."""

import errno
import re
from dataclasses import dataclass

_MESSAGES = {
    "configuration": "Configuração do banco ausente, inválida ou ainda não aprovada.",
    "dependency": "Dependências do adaptador SQL Server indisponíveis. Confira a instalação local.",
    "driver": "Driver ODBC ausente ou incompatível. Confira o driver aprovado para este ambiente.",
    "network": "Origem indisponível. Confira nome, rede, VPN e porta com a DSI.",
    "certificate": (
        "Falha na validação TLS. Confira o certificado e a cadeia de confiança com a DSI."
    ),
    "authentication": (
        "Autenticação recusada. Confira o método e a credencial no ambiente autorizado."
    ),
    "permission": "Acesso à fonte recusado. Solicite ao DBA a revisão do escopo de leitura.",
    "timeout": (
        "O limite de tempo da operação foi atingido. Revise o acesso e o orçamento da consulta."
    ),
    "unknown": "Falha não classificada. O operador deve investigar no ambiente privado autorizado.",
}
_STAGES = {
    "configuration",
    "dependency",
    "driver",
    "connection",
    "query",
    "inventory",
    "diagnosis",
    "output",
    "operation",
}


@dataclass(frozen=True, slots=True)
class DatabaseIssue:
    category: str
    message: str
    stage: str


class DatabaseConfigurationError(ValueError):
    """Não aceitar valores ou mensagens externas em erros de configuração."""

    def __init__(self) -> None:
        super().__init__(_MESSAGES["configuration"])


class DatabaseOperationError(RuntimeError):
    """Transportar apenas uma classificação sanitizada entre as camadas."""

    def __init__(self, issue: DatabaseIssue) -> None:
        self.issue = issue
        super().__init__(issue.message)


def _diagnostics(error: Exception) -> tuple[set[str], set[int], str]:
    """Examinar argumentos somente em memória; nunca formatar a exceção."""
    states: set[str] = set()
    numbers: set[int] = set()
    messages: list[str] = []
    current = error
    seen: set[int] = set()
    for _ in range(8):
        if id(current) in seen:
            break
        seen.add(id(current))
        for arg in current.args:
            if type(arg) is int:
                numbers.add(arg)
            elif isinstance(arg, str):
                if re.fullmatch(r"[A-Z0-9]{5}", arg):
                    states.add(arg)
                states.update(re.findall(r"\[([A-Z0-9]{5})\]", arg))
                numbers.update(int(item) for item in re.findall(r"\((-?\d{1,10})\)", arg))
                messages.append(arg.casefold())
        original = getattr(current, "orig", None)
        if not isinstance(original, Exception):
            break
        current = original
    return states, numbers, " ".join(messages)


def classify_database_error(error: Exception, *, stage: str) -> DatabaseIssue:
    """Categorias são pistas de diagnóstico, não prova de causa ou de privilégios."""
    safe_stage = stage if stage in _STAGES else "operation"
    if isinstance(error, DatabaseOperationError):
        category = error.issue.category if error.issue.category in _MESSAGES else "unknown"
    elif isinstance(error, DatabaseConfigurationError):
        category = "configuration"
    elif isinstance(error, ImportError):
        category = "dependency"
    elif isinstance(error, TimeoutError):
        category = "timeout"
    else:
        states, numbers, text = _diagnostics(error)
        if numbers & {-2146893019, -2146893022, -2146762487} or any(
            term in text
            for term in (
                "certificate",
                "certificado",
                "certificat",
                "ssl provider",
                "tls handshake",
            )
        ):
            category = "certificate"
        elif states & {"IM002", "IM003", "IM004", "IM014"} or any(
            term in text
            for term in (
                "can't open lib",
                "data source name not found",
                "driver could not be loaded",
            )
        ):
            category = "driver"
        elif states & {"HYT00", "HYT01", "S1T00"} or numbers & {258}:
            category = "timeout"
        elif "28000" in states or numbers & {18452, 18456}:
            category = "authentication"
        elif "42501" in states or numbers & {229, 230, 262, 297, 916, 4060, 4064}:
            category = "permission"
        elif (
            states & {"08001", "08003", "08004", "08006", "08S01"}
            or numbers & {17, 53, 64, 10053, 10054, 10060, 10061, 11001}
            or isinstance(error, ConnectionError)
            or (
                isinstance(error, OSError)
                and error.errno
                in {
                    errno.ECONNREFUSED,
                    errno.ECONNRESET,
                    errno.EHOSTUNREACH,
                    errno.ENETUNREACH,
                    errno.ETIMEDOUT,
                }
            )
        ):
            category = "network"
        else:
            category = "unknown"
    return DatabaseIssue(category=category, message=_MESSAGES[category], stage=safe_stage)
