from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.inspecao import ItemIn, ItemOut, ItemPatch
from app.services import item_service as service

router = APIRouter(prefix="/inspecoes/{inspecao_id}/itens", tags=["itens"])


@router.get("", response_model=list[ItemOut])
def listar(inspecao_id: int, db: Session = Depends(get_db)):
    return service.listar(db, inspecao_id)


@router.post("", response_model=ItemOut, status_code=201)
def adicionar(inspecao_id: int, dados: ItemIn, db: Session = Depends(get_db)):
    return service.adicionar_avulso(db, inspecao_id, dados)


@router.patch("/{item_id}", response_model=ItemOut)
def atualizar(inspecao_id: int, item_id: int, dados: ItemPatch, db: Session = Depends(get_db)):
    return service.atualizar(db, inspecao_id, item_id, dados)


@router.delete("/{item_id}", status_code=204)
def remover(inspecao_id: int, item_id: int, db: Session = Depends(get_db)):
    service.remover(db, inspecao_id, item_id)
    return Response(status_code=204)
