from sqlalchemy import Boolean, CheckConstraint, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Local(Base):
    __tablename__ = "local"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -18.05 AND -7.35", name="ck_local_latitude_mt"),
        CheckConstraint("longitude BETWEEN -61.65 AND -50.20", name="ck_local_longitude_mt"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    municipio: Mapped[str] = mapped_column(String(80), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(8, 5, asdecimal=False), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(8, 5, asdecimal=False), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
