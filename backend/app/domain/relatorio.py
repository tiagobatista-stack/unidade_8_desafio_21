"""Regras puras do relatório de vistoria (numeração, totais e explicação do resultado)."""
from collections.abc import Iterable
from typing import Protocol

from app.domain.constantes import Resultado, Situacao


class ItemRelatorio(Protocol):
    critico: bool
    situacao: str


def formatar_numero(sequencial: int, ano: int) -> str:
    """Relatório de Vistoria nº 0001/2026 -> '0001/2026'."""
    return f"{sequencial:04d}/{ano}"


def totais(itens: Iterable[ItemRelatorio]) -> dict:
    itens = list(itens)
    contagem = {s: sum(1 for i in itens if i.situacao == s) for s in Situacao.TODOS}
    return {
        "total": len(itens),
        "respondidos": len(itens) - contagem[Situacao.NAO_RESPONDIDO],
        "conformes": contagem[Situacao.CONFORME],
        "nao_conformes": contagem[Situacao.NAO_CONFORME],
        "nao_aplicaveis": contagem[Situacao.NAO_SE_APLICA],
        "nao_respondidos": contagem[Situacao.NAO_RESPONDIDO],
    }


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def explicar_resultado(itens: Iterable[ItemRelatorio], resultado: str | None) -> str:
    """A regra que levou ao resultado (RN06), em linguagem do relatório."""
    itens = list(itens)
    nc = [i for i in itens if i.situacao == Situacao.NAO_CONFORME]
    criticos = [i for i in nc if i.critico]
    if resultado is None:  # prévia: o resultado só existe depois do fechamento (RN10)
        pendentes = sum(1 for i in itens if i.situacao == Situacao.NAO_RESPONDIDO)
        if pendentes:
            return f"Resultado ainda não calculado: {_plural(pendentes, 'item não respondido', 'itens não respondidos')}."
        return "Todos os itens foram respondidos; o resultado será calculado quando a inspeção for fechada."
    if resultado == Resultado.REPROVADA:
        return _plural(len(criticos), "item crítico não conforme", "itens críticos não conformes")
    if resultado == Resultado.APROVADA_COM_RESSALVAS:
        return f"Nenhum item crítico não conforme; {_plural(len(nc), 'item não conforme', 'itens não conformes')}"
    return "Nenhum item não conforme"
