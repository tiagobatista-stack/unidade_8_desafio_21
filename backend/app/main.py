from contextlib import asynccontextmanager

import os

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import database
from app.errors import registrar_handlers
from app.routers import fotos, inspecoes, itens, locais, painel
from app.seed.modelo import garantir_modelo
from app.services.migracao_dados import preencher_legado


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.criar_tabelas()
    with Session(database.get_engine()) as db:
        garantir_modelo(db)
        preencher_legado(db)
    yield


def _configurar_cors(app: FastAPI) -> None:
    """CORS só para as origens listadas em CORS_ORIGINS (separadas por vírgula). Padrão: nenhuma."""
    origens = [o.strip().rstrip("/") for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
    if not origens:
        return
    # allow_private_network: navegadores exigem isso quando um site público chama um servidor em 127.0.0.1.
    app.add_middleware(
        CORSMiddleware, allow_origins=origens, allow_methods=["*"], allow_headers=["*"], allow_private_network=True
    )


def criar_app() -> FastAPI:
    app = FastAPI(title="Inspeções Simuladas", lifespan=lifespan)
    registrar_handlers(app)
    _configurar_cors(app)
    api = APIRouter(prefix="/api/v1")

    @api.get("/health")
    def health():
        return {"status": "ok"}

    api.include_router(locais.router)
    api.include_router(inspecoes.router)
    api.include_router(itens.router)
    api.include_router(fotos.router)
    api.include_router(painel.router)
    app.include_router(api)
    return app


app = criar_app()
