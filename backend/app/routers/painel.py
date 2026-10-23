from datetime import datetime

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import export_service, indicador_service, seed_service
from app.storage.arquivos import ArmazenamentoArquivos, get_storage

router = APIRouter(tags=["painel"])


class IndicadoresOut(BaseModel):
    inspecoes: int
    pendencias: int
    finalizadas: int
    gerado_em: datetime


class ExemplosOut(BaseModel):
    locais: int
    inspecoes: int
    fotos: int


@router.get("/indicadores", response_model=IndicadoresOut)
def indicadores(db: Session = Depends(get_db)):
    return indicador_service.indicadores(db)


@router.post("/utilitarios/carregar-exemplos", response_model=ExemplosOut, status_code=201)
def carregar_exemplos(db: Session = Depends(get_db), storage: ArmazenamentoArquivos = Depends(get_storage)):
    return seed_service.carregar_exemplos(db, storage)


@router.get("/exportacao/inspecoes.csv")
def exportar_csv(db: Session = Depends(get_db)):
    conteudo = "﻿" + export_service.gerar_csv(db)  # BOM: Excel reconhece UTF-8
    return Response(
        content=conteudo.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="inspecoes.csv"'},
    )
