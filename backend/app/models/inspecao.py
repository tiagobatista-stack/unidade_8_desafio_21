from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Inspecao(Base):
    __tablename__ = "inspecao"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ABERTA','EM_ANDAMENTO','FINALIZADA','CANCELADA')", name="ck_inspecao_status"
        ),
        CheckConstraint(
            "resultado IS NULL OR resultado IN ('APROVADA','APROVADA_COM_RESSALVAS','REPROVADA')",
            name="ck_inspecao_resultado_valido",
        ),
        CheckConstraint(
            "(status = 'FINALIZADA') = (resultado IS NOT NULL)", name="ck_inspecao_resultado_so_finalizada"
        ),
        CheckConstraint(
            "(status = 'FINALIZADA') = (fechado_em IS NOT NULL)", name="ck_inspecao_fechado_em_so_finalizada"
        ),
        CheckConstraint(
            "status <> 'CANCELADA' OR (motivo_cancelamento IS NOT NULL AND length(motivo_cancelamento) > 0)",
            name="ck_inspecao_motivo_cancelamento",
        ),
        CheckConstraint(
            "data_realizacao IS NULL OR data_realizacao >= data_agendamento", name="ck_inspecao_datas"
        ),
        CheckConstraint("length(objetivo) > 0 AND length(objetivo) <= 200", name="ck_inspecao_objetivo"),
        CheckConstraint(
            "observacoes_vistoria IS NULL OR length(observacoes_vistoria) <= 2000",
            name="ck_inspecao_obs_vistoria",
        ),
        Index("ix_inspecao_status", "status"),
        Index("ix_inspecao_data_agendamento", "data_agendamento"),
        Index("ix_inspecao_local_id", "local_id"),
        Index("ux_inspecao_numero_relatorio", "numero_relatorio", unique=True),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    # Obrigatório pela API; nulo só em linhas anteriores à existência do campo.
    numero_processo: Mapped[str | None] = mapped_column(String(60))
    # Cópia (JSON) dos dados do empreendimento gravada no fechamento; o relatório da finalizada usa esta cópia.
    empreendimento_json: Mapped[str | None] = mapped_column(Text)
    # 'NNNN/AAAA', atribuído no fechamento; único e nunca reutilizado (nulo enquanto não finalizada)
    numero_relatorio: Mapped[str | None] = mapped_column(String(20))
    # R4: dados da capa da SEMA (todos opcionais; legado fica nulo). Interessado vazio = demanda interna.
    interessado_orgao: Mapped[str | None] = mapped_column(String(120))
    interessado_unidade: Mapped[str | None] = mapped_column(String(120))
    interessado_comarca: Mapped[str | None] = mapped_column(String(80))
    interessado_requerente: Mapped[str | None] = mapped_column(String(120))
    assunto_tipo: Mapped[str | None] = mapped_column(String(80))
    assunto_outro: Mapped[str | None] = mapped_column(String(120))  # texto livre quando assunto_tipo = 'Outro'
    providencias_texto: Mapped[str | None] = mapped_column(Text)
    numero_relatorio_sema: Mapped[str | None] = mapped_column(String(40))  # número oficial atribuído pela SEMA
    local_id: Mapped[int] = mapped_column(ForeignKey("local.id"), nullable=False)
    objetivo: Mapped[str] = mapped_column(String(200), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text)
    observacoes_vistoria: Mapped[str | None] = mapped_column(Text)
    data_agendamento: Mapped[date] = mapped_column(Date, nullable=False)
    data_realizacao: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ABERTA")
    resultado: Mapped[str | None] = mapped_column(String(30))
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(300))
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fechado_em: Mapped[datetime | None] = mapped_column(DateTime)

    local = relationship("Local", lazy="joined")
    itens = relationship(
        "ItemInspecao",
        back_populates="inspecao",
        cascade="all, delete-orphan",
        order_by="ItemInspecao.ordem, ItemInspecao.id",
    )
    fotos = relationship(
        "FotoVistoria",
        cascade="all, delete-orphan",
        order_by="FotoVistoria.ordem, FotoVistoria.id",
    )
    equipe = relationship(
        "EquipeMembro",
        cascade="all, delete-orphan",
        order_by="EquipeMembro.ordem, EquipeMembro.id",
        lazy="selectin",
    )
    atos = relationship(
        "AtoLavrado",
        cascade="all, delete-orphan",
        order_by="AtoLavrado.ordem, AtoLavrado.id",
        lazy="selectin",
    )
