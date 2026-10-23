from collections.abc import Iterable
from typing import Protocol

from app.domain.constantes import Resultado, Situacao


class ItemLike(Protocol):
    critico: bool
    situacao: str


def calcular_resultado(itens: Iterable[ItemLike]) -> str:
    """RN06: crítico NC -> REPROVADA; senão algum NC -> COM_RESSALVAS; senão APROVADA."""
    nao_conformes = [i for i in itens if i.situacao == Situacao.NAO_CONFORME]
    if any(i.critico for i in nao_conformes):
        return Resultado.REPROVADA
    if nao_conformes:
        return Resultado.APROVADA_COM_RESSALVAS
    return Resultado.APROVADA
