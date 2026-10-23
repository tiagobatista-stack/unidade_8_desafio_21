from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Inspecao, ModeloItem


def obter(db: Session, inspecao_id: int) -> Inspecao | None:
    return db.get(Inspecao, inspecao_id)


def adicionar(db: Session, inspecao: Inspecao) -> Inspecao:
    db.add(inspecao)
    db.flush()
    return inspecao


def modelo_ativo(db: Session) -> list[ModeloItem]:
    return list(db.scalars(select(ModeloItem).where(ModeloItem.ativo.is_(True)).order_by(ModeloItem.ordem)))


def listar(
    db: Session,
    status: str | None,
    data_inicio: date | None,
    data_fim: date | None,
    local_id: int | None,
    pagina: int,
    tamanho: int,
) -> tuple[list[Inspecao], int]:
    filtros = []
    if status:
        filtros.append(Inspecao.status == status)
    if data_inicio:
        filtros.append(Inspecao.data_agendamento >= data_inicio)
    if data_fim:
        filtros.append(Inspecao.data_agendamento <= data_fim)
    if local_id:
        filtros.append(Inspecao.local_id == local_id)
    total = db.scalar(select(func.count()).select_from(Inspecao).where(*filtros)) or 0
    consulta = (
        select(Inspecao)
        .where(*filtros)
        .order_by(Inspecao.data_agendamento.desc(), Inspecao.id.desc())
        .offset((pagina - 1) * tamanho)
        .limit(tamanho)
    )
    return list(db.scalars(consulta).unique()), total
