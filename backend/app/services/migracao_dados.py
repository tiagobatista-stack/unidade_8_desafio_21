"""Preenchimento do legado, uma vez e de forma idempotente, na inicialização da API."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Inspecao
from app.services import empreendimento_service, numeracao_service


def preencher_legado(db: Session) -> dict:
    """Finalizadas anteriores à cópia do fechamento e à numeração recebem os dois, uma única vez.

    - Cópia: dados do Local ATUAL (limitação conhecida: para esses registros antigos reflete o Local de hoje).
    - Número do relatório: na ordem do fechamento (`fechado_em`, `id`), no ano de `fechado_em`.
    """
    copias = numeros = 0
    consulta = select(Inspecao).where(Inspecao.status == "FINALIZADA", Inspecao.empreendimento_json.is_(None))
    for inspecao in db.scalars(consulta).unique():
        empreendimento_service.copiar_no_fechamento(inspecao)
        copias += 1
    consulta = (
        select(Inspecao)
        .where(Inspecao.status == "FINALIZADA", Inspecao.numero_relatorio.is_(None))
        .order_by(Inspecao.fechado_em, Inspecao.id)
    )
    for inspecao in db.scalars(consulta).unique():
        ano = inspecao.fechado_em.year if inspecao.fechado_em else inspecao.data_agendamento.year
        numeracao_service.atribuir_numero(db, inspecao, ano)
        numeros += 1
    if copias or numeros:
        db.commit()
    return {"copias": copias, "numeros": numeros}
