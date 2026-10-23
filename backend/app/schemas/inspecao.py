from datetime import date, datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

from app.schemas.foto import FotoOut
from app.schemas.local import EmpreendimentoOut, LocalOut, LocalResumo

T = TypeVar("T")

StatusT = Literal["ABERTA", "EM_ANDAMENTO", "FINALIZADA", "CANCELADA"]
SituacaoT = Literal["NAO_RESPONDIDO", "CONFORME", "NAO_CONFORME", "NAO_SE_APLICA"]


class Pagina(BaseModel, Generic[T]):
    dados: list[T]
    total: int
    pagina: int
    tamanho: int


class InspecaoIn(BaseModel):
    numero_processo: str
    local_id: int
    data_agendamento: date
    objetivo: str
    observacoes: str | None = None
    observacoes_vistoria: str | None = None
    data_realizacao: date | None = None


class InspecaoPatch(BaseModel):
    numero_processo: str | None = None
    local_id: int | None = None
    data_agendamento: date | None = None
    objetivo: str | None = None
    observacoes: str | None = None
    observacoes_vistoria: str | None = None
    data_realizacao: date | None = None


class CancelarIn(BaseModel):
    motivo: str


class ItemIn(BaseModel):
    descricao: str
    critico: bool = False


class ItemPatch(BaseModel):
    situacao: SituacaoT | None = None
    observacao: str | None = None


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descricao: str
    critico: bool
    situacao: SituacaoT
    observacao: str | None
    origem: Literal["MODELO", "AVULSO"]
    ordem: int


class ItemDetalheOut(ItemOut):
    qtd_fotos: int


class ResumoItens(BaseModel):
    total: int
    respondidos: int
    nao_conformes: int


class InspecaoResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    numero_processo: str | None
    local: LocalResumo
    objetivo: str
    data_agendamento: date
    data_realizacao: date | None
    status: StatusT
    resultado: str | None
    qtd_fotos: int


class InspecaoDetalhe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    numero_processo: str | None
    local: LocalOut
    objetivo: str
    observacoes: str | None
    observacoes_vistoria: str | None
    data_agendamento: date
    data_realizacao: date | None
    status: StatusT
    resultado: str | None
    motivo_cancelamento: str | None
    criado_em: datetime
    atualizado_em: datetime
    fechado_em: datetime | None
    empreendimento: EmpreendimentoOut
    numero_relatorio: str | None
    campos_editaveis: list[str]
    fechamento_bloqueado_motivo: str | None
    registro_bloqueado_motivo: str | None
    itens: list[ItemDetalheOut]
    fotos: list[FotoOut]
    resumo_itens: ResumoItens
