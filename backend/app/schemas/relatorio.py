from datetime import date, datetime

from pydantic import BaseModel


class CabecalhoRel(BaseModel):
    """Cabeçalho mínimo, para casar com a capa gerada no sistema da SEMA (sem título de capa)."""

    protocolo: str | None
    codigo: str
    ref_interna: str | None  # NNNN/AAAA; nulo na prévia
    numero_relatorio_sema: str | None
    linha: str  # Protocolo nº ... | Inspeção INS-xxx | Ref. interna NNNN/AAAA [| Relatório SEMA nº ...]


class RelatoRel(BaseModel):
    """5.1 Relato da vistoria."""

    data_realizacao: date | None
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


class AtoRel(BaseModel):
    tipo: str
    numero: str | None
    rotulo: str  # "Notificação – nº NOT-1" ou "Notificação – nº a definir"


class ProvidenciasRel(BaseModel):
    texto: str | None
    atos: list[AtoRel]


class ConstatacoesRel(BaseModel):
    """Item 5: relato (5.1), checklist (5.2) e registro fotográfico (5.3)."""

    relato: RelatoRel
    checklist: ChecklistRel
    fotos: list[FotoRel]


class ConclusaoRel(BaseModel):
    resultado: str | None
    regra: str


class RelatorioOut(BaseModel):
    """Corpo do relatório técnico, a partir do item 5 (os itens 1 a 4 vão na capa gerada no sistema da SEMA)."""

    previa: bool
    marca_dagua: str | None
    cabecalho: CabecalhoRel
    constatacoes: ConstatacoesRel
    providencias: ProvidenciasRel
    conclusao: ConclusaoRel | None  # nulo quando "Incluir conclusão" está desligado
