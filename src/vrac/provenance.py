"""Identificação única da origem nas telas e nos arquivos."""

INSTITUTIONAL_SOURCE = "Supabase · origem institucional pseudonimizada"


def is_institutional(source: str) -> bool:
    return source == INSTITUTIONAL_SOURCE


def nature(source: str) -> str:
    if is_institutional(source):
        return "DADOS INSTITUCIONAIS PSEUDONIMIZADOS · acesso restrito · validação pendente"
    return "DEMONSTRAÇÃO — DADOS SINTÉTICOS, sem validade institucional"
