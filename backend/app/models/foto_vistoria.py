from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FotoVistoria(Base):
    __tablename__ = "foto_vistoria"
    __table_args__ = (
        UniqueConstraint("inspecao_id", "hash_sha256", name="uq_foto_inspecao_hash"),
        CheckConstraint("mime_type IN ('image/jpeg','image/png','image/webp')", name="ck_foto_mime"),
        CheckConstraint("tamanho_bytes > 0 AND tamanho_bytes <= 5242880", name="ck_foto_tamanho"),
        CheckConstraint("length(anotacao) >= 1 AND length(anotacao) <= 1000", name="ck_foto_anotacao"),
        CheckConstraint("legenda IS NULL OR length(legenda) <= 200", name="ck_foto_legenda"),
        Index("ix_foto_vistoria_inspecao_id", "inspecao_id"),
        Index("ix_foto_vistoria_item_inspecao_id", "item_inspecao_id"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inspecao_id: Mapped[int] = mapped_column(ForeignKey("inspecao.id", ondelete="CASCADE"), nullable=False)
    item_inspecao_id: Mapped[int | None] = mapped_column(ForeignKey("item_inspecao.id", ondelete="SET NULL"))
    nome_original: Mapped[str] = mapped_column(String(200), nullable=False)
    arquivo_path: Mapped[str] = mapped_column(String(300), unique=True, nullable=False)
    miniatura_path: Mapped[str] = mapped_column(String(300), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(20), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    largura: Mapped[int] = mapped_column(Integer, nullable=False)
    altura: Mapped[int] = mapped_column(Integer, nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    legenda: Mapped[str | None] = mapped_column(String(200))
    anotacao: Mapped[str] = mapped_column(Text, nullable=False)
    data_captura: Mapped[datetime | None] = mapped_column(DateTime)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)
