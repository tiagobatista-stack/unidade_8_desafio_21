from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EquipeMembro(Base):
    __tablename__ = "equipe_membro"
    __table_args__ = (
        CheckConstraint("length(nome) > 0", name="ck_equipe_membro_nome"),
        Index("ix_equipe_membro_inspecao_id", "inspecao_id"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inspecao_id: Mapped[int] = mapped_column(ForeignKey("inspecao.id", ondelete="CASCADE"), nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    cargo: Mapped[str | None] = mapped_column(String(120))
    orgao: Mapped[str | None] = mapped_column(String(120))
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
