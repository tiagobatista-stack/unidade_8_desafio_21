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


ROTULOS = {
    "numero_processo": "Número do processo", "local_id": "Local", "data_agendamento": "Data de agendamento",
    "data_realizacao": "Data de realização", "objetivo": "Objetivo", "observacoes": "Observações",
    "observacoes_vistoria": "Observações da vistoria", "motivo": "Motivo", "nome": "Nome", "municipio": "Município",
    "tipo": "Tipo", "latitude": "Latitude", "longitude": "Longitude", "latitude_gms": "Latitude (GMS)",
    "longitude_gms": "Longitude (GMS)", "ativo": "Ativo", "numero_car": "Número do CAR", "logradouro": "Logradouro",
    "uf": "UF", "cep": "CEP", "cpf_cnpj": "CPF/CNPJ", "telefone": "Telefone", "proprietarios": "Proprietários",
    "corr_logradouro": "Logradouro de correspondência", "corr_numero": "Número de correspondência",
    "corr_complemento": "Complemento de correspondência", "corr_bairro": "Bairro de correspondência",
    "corr_municipio": "Município de correspondência", "corr_uf": "UF de correspondência",
    "corr_cep": "CEP de correspondência", "interessado_orgao": "Órgão / entidade", "interessado_unidade": "Unidade",
    "interessado_comarca": "Comarca", "interessado_requerente": "Requerente", "assunto_tipo": "Tipo de vistoria",
    "assunto_outro": "Assunto", "providencias_texto": "Providências", "numero_relatorio_sema": "Nº do relatório na SEMA",
    "equipe": "Equipe técnica", "cargo": "Cargo / função", "orgao": "Órgão / unidade", "atos": "Atos", "id": "Id",
    "situacao": "Situação", "observacao": "Observação", "descricao": "Descrição", "critico": "Crítico",
    "anotacao": "Anotação", "legenda": "Legenda", "item_id": "Item", "status": "Status", "pagina": "Página",
    "tamanho": "Tamanho", "data_inicio": "Data inicial", "data_fim": "Data final", "arquivo": "Arquivo",
}

_TIPOS_ESPERADOS = {
    "string_type": "texto", "int_type": "número inteiro", "float_type": "número", "bool_type": "verdadeiro ou falso",
    "list_type": "lista", "dict_type": "objeto", "model_attributes_type": "objeto",
}


def _rotulo(loc: tuple) -> str:
    """Rótulo do campo (último nome do caminho); em listas acrescenta a linha: 'Nome (linha 2)'."""
    nomes = [p for p in loc if isinstance(p, str) and p not in ("body", "query", "path", "form")]
    linhas = [p for p in loc if isinstance(p, int)]
    nome = nomes[-1] if nomes else "Requisição"
    rotulo = ROTULOS.get(nome, nome.replace("_", " ").capitalize())
    return f"{rotulo} (linha {linhas[-1] + 1})" if linhas else rotulo


def _mensagem_pt(e: dict) -> str:
    """Mensagem do Pydantic em português, com o rótulo do campo: 'Latitude: obrigatória'."""
    tipo, ctx = e.get("type", ""), e.get("ctx") or {}
    if tipo == "missing":
        texto = "obrigatória"
    elif tipo in _TIPOS_ESPERADOS:
        texto = f"tipo inválido, esperado {_TIPOS_ESPERADOS[tipo]}"
    elif tipo in ("int_parsing", "float_parsing", "int_from_float", "decimal_parsing"):
        texto = "deve ser um número"
    elif tipo.startswith("date") or tipo.startswith("time"):
        texto = "data inválida, use AAAA-MM-DD"
    elif tipo == "string_too_long":
        texto = f"máximo de {ctx.get('max_length')} caracteres"
    elif tipo == "string_too_short":
        texto = f"mínimo de {ctx.get('min_length')} caracteres"
    elif tipo in ("too_long", "too_short"):
        texto = "quantidade de itens fora do limite"
    elif tipo in ("greater_than_equal", "greater_than", "less_than_equal", "less_than"):
        limites = {"greater_than_equal": "maior ou igual a", "greater_than": "maior que",
                   "less_than_equal": "menor ou igual a", "less_than": "menor que"}
        chave = {"greater_than_equal": "ge", "greater_than": "gt", "less_than_equal": "le", "less_than": "lt"}[tipo]
        texto = f"deve ser {limites[tipo]} {ctx.get(chave)}"
    elif tipo in ("literal_error", "enum"):
        texto = "valor inválido"
    elif tipo in ("json_invalid", "model_type"):
        texto = "corpo da requisição inválido"
    else:
        texto = "valor inválido"
    return f"{_rotulo(tuple(e.get('loc', ())))}: {texto}"


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
            detalhes.append({"campo": campo, "mensagem": _mensagem_pt(e)})
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


def erro_campo(campo: str, mensagem: str) -> ErroNegocio:
    return ErroNegocio("VALIDACAO_CAMPO", "Dados inválidos.", 422, [{"campo": campo, "mensagem": mensagem}])
