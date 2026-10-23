"""Preenchimento do legado, uma vez e de forma idempotente, na inicialização da API."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Inspecao
from app.services import empreendimento_service


def preencher_legado(db: Session) -> dict:
    """Finalizadas anteriores à cópia do fechamento recebem a cópia do Local ATUAL.

    Limitação conhecida: para esses registros antigos a cópia reflete o Local de hoje, não o do fechamento.
    """
    copiadas = 0
    consulta = select(Inspecao).where(Inspecao.status == "FINALIZADA", Inspecao.empreendimento_json.is_(None))
    for inspecao in db.scalars(consulta).unique():
        empreendimento_service.copiar_no_fechamento(inspecao)
        copiadas += 1
    if copiadas:
        db.commit()
    return {"copias": copiadas}
