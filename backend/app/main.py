from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app import database
from app.errors import registrar_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.criar_tabelas()
    yield


def criar_app() -> FastAPI:
    app = FastAPI(title="Inspeções Simuladas", lifespan=lifespan)
    registrar_handlers(app)
    api = APIRouter(prefix="/api/v1")

    @api.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(api)
    return app


app = criar_app()
