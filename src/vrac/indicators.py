"""Símbolos da tela para o indicador de carga e variações; não mudam regra nem arquivos.

A cor marca o que foge do esperado, sem julgamento: o indicador não avalia produtividade,
por isso nenhum estado usa vermelho. A direção é dita pelo símbolo e o estado, pelo texto.
"""

from collections import Counter
from collections.abc import Iterable

ABSENT = "ausente"

# Ordem de leitura, da carga menor para a maior e depois os estados sem classificação.
INDICATORS: dict[str, tuple[str, str]] = {
    "Abaixo do necessário": ("▼", "attention"),
    "Dentro do esperado": ("●", "normal"),
    "Acima do necessário": ("▲", "attention"),
    "Muito acima (verificar coord./múltiplas turmas)": ("▲▲", "strong"),
    "Sem alocação (CH = 0)": ("○", "neutral"),
    "Sem CH (em branco)": ("–", "neutral"),
    "Sem regra definida": ("?", "neutral"),
    "Indicadores distintos": ("≠", "neutral"),
}
_RANK = {name: position for position, name in enumerate(INDICATORS)}


def indicator_label(value: str) -> str:
    """Texto original precedido do símbolo; valores desconhecidos ficam como vieram."""
    return f"{INDICATORS[value][0]} {value}" if value in INDICATORS else value


def indicator_rank(value: str) -> int:
    return _RANK.get(value, len(_RANK))


def indicator_distribution(values: Iterable[str | None]) -> tuple[tuple[str, int], ...]:
    """Contagem por estado na ordem de leitura; sem indicador continua visível como ausente."""
    counts = Counter(ABSENT if value is None else value for value in values)
    return tuple(sorted(counts.items(), key=lambda item: indicator_rank(item[0])))


def change_label(value: int | float | None, text: str) -> str:
    """Direção da variação já calculada; ausente nunca recebe seta nem vira zero."""
    if value is None:
        return text
    return f"{'▲' if value > 0 else '▼' if value < 0 else '●'} {text}"
