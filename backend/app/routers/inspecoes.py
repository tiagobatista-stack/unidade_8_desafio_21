from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.inspecao import (
    CancelarIn,
    InspecaoDetalhe,
    InspecaoIn,
    InspecaoPatch,
    InspecaoResumo,
    Pagina,
    StatusT,
)
from app.services import inspecao_service as service

router = APIRouter(prefix="/inspecoes", tags=["inspecoes"])


@router.post("", response_model=InspecaoDetalhe, status_code=201)
def criar(dados: InspecaoIn, db: Session = Depends(get_db)):
    return service.detalhe(service.criar(db, dados))


@router.get("", response_model=Pagina[InspecaoResumo])
def listar(
    status: list[StatusT] | None = Query(None),
    data_inicio: date | None = None,
    data_fim: date | None = None,
    local_id: int | None = None,
    numero_processo: str | None = None,
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    dados, total = service.listar(db, status, data_inicio, data_fim, local_id, numero_processo, pagina, tamanho)
    return {"dados": dados, "total": total, "pagina": pagina, "tamanho": tamanho}


@router.get("/{inspecao_id}", response_model=InspecaoDetalhe)
def detalhar(inspecao_id: int, db: Session = Depends(get_db)):
    return service.detalhe(service.obter(db, inspecao_id))


@router.patch("/{inspecao_id}", response_model=InspecaoDetalhe)
def editar(inspecao_id: int, dados: InspecaoPatch, db: Session = Depends(get_db)):
    return service.detalhe(service.editar(db, inspecao_id, dados))


@router.post("/{inspecao_id}/cancelar", response_model=InspecaoDetalhe)
def cancelar(inspecao_id: int, dados: CancelarIn, db: Session = Depends(get_db)):
    return service.detalhe(service.cancelar(db, inspecao_id, dados.motivo))


@router.post("/{inspecao_id}/fechar", response_model=InspecaoDetalhe)
def fechar(inspecao_id: int, db: Session = Depends(get_db)):
    return service.detalhe(service.fechar(db, inspecao_id))
