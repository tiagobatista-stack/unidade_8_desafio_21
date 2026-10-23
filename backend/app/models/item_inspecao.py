from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ItemInspecao(Base):
    __tablename__ = "item_inspecao"
    __table_args__ = (
        CheckConstraint(
            "situacao IN ('NAO_RESPONDIDO','CONFORME','NAO_CONFORME','NAO_SE_APLICA')",
            name="ck_item_situacao",
        ),
        CheckConstraint("origem IN ('MODELO','AVULSO')", name="ck_item_origem"),
        CheckConstraint(
            "(origem = 'MODELO') = (modelo_item_id IS NOT NULL)", name="ck_item_origem_modelo"
        ),
        CheckConstraint("length(descricao) > 0 AND length(descricao) <= 200", name="ck_item_descricao"),
        Index("ix_item_inspecao_inspecao_id", "inspecao_id"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inspecao_id: Mapped[int] = mapped_column(ForeignKey("inspecao.id", ondelete="CASCADE"), nullable=False)
    modelo_item_id: Mapped[int | None] = mapped_column(ForeignKey("modelo_item.id"))
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    critico: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    situacao: Mapped[str] = mapped_column(String(20), nullable=False, default="NAO_RESPONDIDO")
    observacao: Mapped[str | None] = mapped_column(Text)
    origem: Mapped[str] = mapped_column(String(10), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)

    inspecao = relationship("Inspecao", back_populates="itens")
