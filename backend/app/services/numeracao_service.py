"""Numeração dos relatórios: sequencial por ano, atribuída no fechamento e nunca reutilizada."""
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.relatorio import formatar_numero
from app.models import ContadorRelatorio, Inspecao


def atribuir_numero(db: Session, inspecao: Inspecao, ano: int) -> str:
    """Reserva o próximo número do `ano` para a inspeção, dentro da transação em curso.

    O UPDATE do contador toma o bloqueio de escrita antes da leitura, então fechamentos simultâneos não
    recebem o mesmo número; o índice único em `inspecao.numero_relatorio` é a segunda barreira.
    """
    if db.get(ContadorRelatorio, ano) is None:
        db.add(ContadorRelatorio(ano=ano, ultimo=0))
        db.flush()
    db.execute(
        update(ContadorRelatorio).where(ContadorRelatorio.ano == ano).values(ultimo=ContadorRelatorio.ultimo + 1)
    )
    ultimo = db.scalar(select(ContadorRelatorio.ultimo).where(ContadorRelatorio.ano == ano))
    inspecao.numero_relatorio = formatar_numero(ultimo, ano)
    return inspecao.numero_relatorio
