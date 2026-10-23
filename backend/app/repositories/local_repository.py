from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Local


def obter(db: Session, local_id: int) -> Local | None:
    return db.get(Local, local_id)


def obter_por_nome(db: Session, nome: str) -> Local | None:
    return db.scalar(select(Local).where(Local.nome == nome))


def listar(db: Session) -> list[Local]:
    return list(db.scalars(select(Local).order_by(Local.nome)))


def adicionar(db: Session, local: Local) -> Local:
    db.add(local)
    db.flush()
    return local
