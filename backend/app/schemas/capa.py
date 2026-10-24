from pydantic import BaseModel


class CampoCapaOut(BaseModel):
    rotulo: str
    valor: str  # o valor ou "Não informado"
    copiar: str  # o que o botão Copiar leva (vazio quando não há valor)
    ausente: bool  # sem valor
    faltando: bool  # sem valor e obrigatório para a SEMA (destacado na tela)


class BlocoCapaOut(BaseModel):
    chave: str
    titulo: str
    texto: str  # texto simples do bloco, no formato do modelo
    campos: list[CampoCapaOut]


class DadosCapaOut(BaseModel):
    codigo: str
    protocolo: str | None
    blocos: list[BlocoCapaOut]
    texto_completo: str
    campos_faltando: int
