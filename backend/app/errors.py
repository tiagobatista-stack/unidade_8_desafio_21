import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("inspecoes")


class ErroNegocio(Exception):
    def __init__(self, codigo: str, mensagem: str, status: int = 422, detalhes: list[dict] | None = None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.status = status
        self.detalhes = detalhes or []


def corpo_erro(codigo: str, mensagem: str, detalhes: list[dict] | None = None) -> dict:
    return {"erro": {"codigo": codigo, "mensagem": mensagem, "detalhes": detalhes or []}}


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(ErroNegocio)
    async def _negocio(_: Request, exc: ErroNegocio):
        return JSONResponse(status_code=exc.status, content=corpo_erro(exc.codigo, exc.mensagem, exc.detalhes))

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, exc: RequestValidationError):
        detalhes = []
        for e in exc.errors():
            campo = ".".join(str(p) for p in e["loc"] if p not in ("body", "query", "path", "form"))
            detalhes.append({"campo": campo, "mensagem": e["msg"]})
        return JSONResponse(
            status_code=422, content=corpo_erro("VALIDACAO_CAMPO", "Dados inválidos.", detalhes)
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return JSONResponse(status_code=404, content=corpo_erro("NAO_ENCONTRADO", "Recurso não encontrado."))
        return JSONResponse(status_code=exc.status_code, content=corpo_erro("ERRO_HTTP", str(exc.detail)))

    @app.exception_handler(Exception)
    async def _interno(_: Request, exc: Exception):
        log.exception("erro interno")
        return JSONResponse(status_code=500, content=corpo_erro("ERRO_INTERNO", "Erro interno."))
