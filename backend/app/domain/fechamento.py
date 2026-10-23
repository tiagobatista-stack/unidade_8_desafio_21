from collections.abc import Iterable
from typing import Protocol

from app.domain.constantes import Situacao


class ItemFechamento(Protocol):
    id: int
    descricao: str
    situacao: str
    observacao: str | None


def problemas_fechamento(itens: Iterable[ItemFechamento]) -> list[dict]:
    """RN04 e RN05: um detalhe por item que impede o fechamento."""
    detalhes = []
    for item in itens:
        if item.situacao == Situacao.NAO_RESPONDIDO:
            detalhes.append(
                {"campo": f"itens.{item.id}", "mensagem": f"Item não respondido: {item.descricao}"}
            )
        elif item.situacao == Situacao.NAO_CONFORME and not (item.observacao or "").strip():
            detalhes.append(
                {"campo": f"itens.{item.id}", "mensagem": f"Item não conforme exige observação: {item.descricao}"}
            )
    return detalhes
