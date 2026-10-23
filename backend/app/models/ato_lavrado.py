from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AtoLavrado(Base):
    __tablename__ = "ato_lavrado"
    __table_args__ = (
        CheckConstraint("length(tipo) > 0", name="ck_ato_lavrado_tipo"),
        Index("ix_ato_lavrado_inspecao_id", "inspecao_id"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inspecao_id: Mapped[int] = mapped_column(ForeignKey("inspecao.id", ondelete="CASCADE"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    # Nulo até o ato ser lavrado no sistema da SEMA; continua editável depois do fechamento.
    numero: Mapped[str | None] = mapped_column(String(40))
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
