from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.inspecao import Pagina
from app.schemas.local import LocalIn, LocalOut
from app.services import local_service

router = APIRouter(prefix="/locais", tags=["locais"])


@router.get("", response_model=Pagina[LocalOut])
def listar(db: Session = Depends(get_db)):
    locais = local_service.listar(db)
    return {"dados": locais, "total": len(locais), "pagina": 1, "tamanho": len(locais)}


@router.get("/{local_id}", response_model=LocalOut)
def detalhar(local_id: int, db: Session = Depends(get_db)):
    return local_service.obter(db, local_id)


@router.post("", response_model=LocalOut, status_code=201)
def criar(dados: LocalIn, db: Session = Depends(get_db)):
    return local_service.criar(db, dados)


@router.put("/{local_id}", response_model=LocalOut)
def atualizar(local_id: int, dados: LocalIn, db: Session = Depends(get_db)):
    return local_service.atualizar(db, local_id, dados)
