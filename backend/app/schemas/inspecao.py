from datetime import date, datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

from app.schemas.local import LocalOut, LocalResumo

T = TypeVar("T")

StatusT = Literal["ABERTA", "EM_ANDAMENTO", "FINALIZADA", "CANCELADA"]
SituacaoT = Literal["NAO_RESPONDIDO", "CONFORME", "NAO_CONFORME", "NAO_SE_APLICA"]


class Pagina(BaseModel, Generic[T]):
    dados: list[T]
    total: int
    pagina: int
    tamanho: int


class InspecaoIn(BaseModel):
    local_id: int
    data_agendamento: date
    objetivo: str
    observacoes: str | None = None
    observacoes_vistoria: str | None = None
    data_realizacao: date | None = None


class InspecaoPatch(BaseModel):
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


class ResumoItens(BaseModel):
    total: int
    respondidos: int
    nao_conformes: int


class InspecaoResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    local: LocalResumo
    objetivo: str
    data_agendamento: date
    data_realizacao: date | None
    status: StatusT
    resultado: str | None


class InspecaoDetalhe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
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
    itens: list[ItemOut]
    resumo_itens: ResumoItens
