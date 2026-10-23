from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.foto import FotoOut, FotoPatch, VerificacaoFotos
from app.services import foto_service as service
from app.storage.arquivos import ArmazenamentoArquivos, get_storage

router = APIRouter(tags=["fotos"])
MAX_LEITURA = 5_242_880 + 1  # lê 1 byte a mais para detectar excesso sem carregar arquivos enormes


@router.post("/inspecoes/{inspecao_id}/fotos", response_model=FotoOut, status_code=201)
def enviar(
    inspecao_id: int,
    arquivo: UploadFile | None = File(None),
    anotacao: str | None = Form(None),
    legenda: str | None = Form(None),
    item_id: int | None = Form(None),
    data_captura: datetime | None = Form(None),
    db: Session = Depends(get_db),
    storage: ArmazenamentoArquivos = Depends(get_storage),
):
    conteudo = arquivo.file.read(MAX_LEITURA) if arquivo is not None else None
    nome = arquivo.filename if arquivo is not None else None
    foto = service.enviar(db, storage, inspecao_id, conteudo, nome, anotacao, legenda, item_id, data_captura)
    return service.foto_dict(foto)


@router.get("/inspecoes/{inspecao_id}/fotos", response_model=list[FotoOut])
def listar(inspecao_id: int, db: Session = Depends(get_db)):
    return [service.foto_dict(f) for f in service.listar(db, inspecao_id)]


@router.get("/inspecoes/{inspecao_id}/fotos/{foto_id}", response_model=FotoOut)
def detalhar(inspecao_id: int, foto_id: int, db: Session = Depends(get_db)):
    return service.foto_dict(service.obter(db, inspecao_id, foto_id))


@router.get("/inspecoes/{inspecao_id}/fotos/{foto_id}/arquivo")
def arquivo(
    inspecao_id: int,
    foto_id: int,
    versao: Literal["miniatura", "original"] = "miniatura",
    db: Session = Depends(get_db),
    storage: ArmazenamentoArquivos = Depends(get_storage),
):
    dados, mime = service.conteudo_arquivo(db, storage, inspecao_id, foto_id, versao)
    return Response(content=dados, media_type=mime, headers={"X-Content-Type-Options": "nosniff"})


@router.patch("/inspecoes/{inspecao_id}/fotos/{foto_id}", response_model=FotoOut)
def atualizar(inspecao_id: int, foto_id: int, dados: FotoPatch, db: Session = Depends(get_db)):
    return service.foto_dict(service.atualizar(db, inspecao_id, foto_id, dados))


@router.delete("/inspecoes/{inspecao_id}/fotos/{foto_id}", status_code=204)
def excluir(
    inspecao_id: int,
    foto_id: int,
    db: Session = Depends(get_db),
    storage: ArmazenamentoArquivos = Depends(get_storage),
):
    service.excluir(db, storage, inspecao_id, foto_id)
    return Response(status_code=204)


@router.get("/utilitarios/verificar-fotos", response_model=VerificacaoFotos)
def verificar_fotos(db: Session = Depends(get_db), storage: ArmazenamentoArquivos = Depends(get_storage)):
    return service.verificar(db, storage)
