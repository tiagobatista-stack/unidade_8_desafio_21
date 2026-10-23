from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.local import EmpreendimentoOut


class IdentificacaoRel(BaseModel):
    codigo: str
    numero_processo: str | None
    status: str
    resultado: str | None
    data_agendamento: date
    data_realizacao: date | None
    fechado_em: datetime | None


class ObjetivoRel(BaseModel):
    objetivo: str
    observacoes: str | None
    observacoes_vistoria: str | None


class ItemRel(BaseModel):
    numero: int
    descricao: str
    critico: bool
    situacao: str
    observacao: str | None
    critico_nao_conforme: bool


class TotaisRel(BaseModel):
    total: int
    respondidos: int
    conformes: int
    nao_conformes: int
    nao_aplicaveis: int
    nao_respondidos: int


class ChecklistRel(BaseModel):
    itens: list[ItemRel]
    totais: TotaisRel


class FotoRel(BaseModel):
    numero: int
    url_original: str
    nome_original: str
    legenda: str | None
    anotacao: str
    item_numero: int | None
    item_descricao: str | None
    data_captura: datetime | None


class ConclusaoRel(BaseModel):
    resultado: str | None
    regra: str


class RelatorioOut(BaseModel):
    previa: bool
    marca_dagua: str | None
    numero_relatorio: str | None
    titulo: str
    identificacao: IdentificacaoRel
    empreendimento: EmpreendimentoOut
    objetivo: ObjetivoRel
    checklist: ChecklistRel
    fotos: list[FotoRel]
    conclusao: ConclusaoRel
