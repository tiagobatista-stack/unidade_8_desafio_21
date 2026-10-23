from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from sqlalchemy.orm import Session

from app import database
from app.errors import registrar_handlers
from app.routers import fotos, inspecoes, itens, locais
from app.seed.modelo import garantir_modelo


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.criar_tabelas()
    with Session(database.get_engine()) as db:
        garantir_modelo(db)
    yield


def criar_app() -> FastAPI:
    app = FastAPI(title="Inspeções Simuladas", lifespan=lifespan)
    registrar_handlers(app)
    api = APIRouter(prefix="/api/v1")

    @api.get("/health")
    def health():
        return {"status": "ok"}

    api.include_router(locais.router)
    api.include_router(inspecoes.router)
    api.include_router(itens.router)
    api.include_router(fotos.router)
    app.include_router(api)
    return app


app = criar_app()
