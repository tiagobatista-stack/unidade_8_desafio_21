from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app import clock
from app.domain.constantes import Status
from app.models import Inspecao


def indicadores(db: Session) -> dict:
    """Uma única consulta de agregação condicional (portátil para PostgreSQL)."""
    linha = db.execute(
        select(
            func.coalesce(func.sum(case((Inspecao.status != Status.CANCELADA, 1), else_=0)), 0),
            func.coalesce(
                func.sum(case((Inspecao.status.in_([Status.ABERTA, Status.EM_ANDAMENTO]), 1), else_=0)), 0
            ),
            func.coalesce(func.sum(case((Inspecao.status == Status.FINALIZADA, 1), else_=0)), 0),
        )
    ).one()
    return {
        "inspecoes": int(linha[0]), "pendencias": int(linha[1]), "finalizadas": int(linha[2]),
        "gerado_em": clock.agora(),
    }
