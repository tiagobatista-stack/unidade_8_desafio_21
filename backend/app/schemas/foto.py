from datetime import datetime

from pydantic import BaseModel


class FotoOut(BaseModel):
    id: int
    inspecao_id: int
    item_id: int | None
    nome_original: str
    mime_type: str
    tamanho_bytes: int
    largura: int
    altura: int
    legenda: str | None
    anotacao: str
    data_captura: datetime | None
    ordem: int
    criado_em: datetime
    url_miniatura: str
    url_original: str


class FotoPatch(BaseModel):
    anotacao: str | None = None
    legenda: str | None = None
    item_id: int | None = None
    ordem: int | None = None


class VerificacaoFotos(BaseModel):
    registros_sem_arquivo: list[str]
    arquivos_sem_registro: list[str]
    total_inconsistencias: int
