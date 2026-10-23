from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ContadorRelatorio(Base):
    """Último número de relatório já emitido em cada ano. Nunca decresce, então números não se repetem."""

    __tablename__ = "contador_relatorio"

    ano: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    ultimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
