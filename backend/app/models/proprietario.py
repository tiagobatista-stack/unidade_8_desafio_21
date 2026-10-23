from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Proprietario(Base):
    __tablename__ = "proprietario"
    __table_args__ = (
        CheckConstraint("length(nome) > 0 AND length(nome) <= 120", name="ck_proprietario_nome"),
        CheckConstraint("telefone IS NULL OR length(telefone) IN (10, 11)", name="ck_proprietario_telefone"),
        Index("ix_proprietario_local_id", "local_id"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    local_id: Mapped[int] = mapped_column(ForeignKey("local.id", ondelete="CASCADE"), nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(11))  # só dígitos
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
