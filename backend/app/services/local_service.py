from sqlalchemy.orm import Session

from app.domain.constantes import (
    MAX_ENDERECO_CAMPO,
    MAX_LOGRADOURO,
    MAX_MUNICIPIO,
    MAX_NOME_LOCAL,
    MAX_NUMERO_ENDERECO,
    MAX_TIPO_LOCAL,
)
from app.domain.contato import (
    MAX_NOME_PROPRIETARIO,
    MAX_PROPRIETARIOS,
    normalizar_car,
    normalizar_telefone,
)
from app.domain.coordenadas import validar_coordenadas
from app.domain.documento import normalizar_cep, normalizar_cpf_cnpj, normalizar_uf
from app.domain.texto import sanear
from app.errors import ErroNegocio, erro_campo
from app.models import Local, Proprietario
from app.repositories import local_repository as repo
from app.schemas.local import LocalIn


def listar(db: Session) -> list[Local]:
    return repo.listar(db)


def obter(db: Session, local_id: int) -> Local:
    local = repo.obter(db, local_id)
    if local is None:
        raise ErroNegocio("NAO_ENCONTRADO", "Local não encontrado.", 404)
    return local


def _tentar(detalhes: list[dict], funcao, *args, **kwargs):
    """Executa a validação e acumula o erro (em vez de interromper) para apontar todos os campos de uma vez."""
    try:
        return funcao(*args, **kwargs)
    except ErroNegocio as e:
        detalhes += e.detalhes
        return None


def _validar_proprietarios(dados: LocalIn, endereco: dict) -> list[dict]:
    """Nome obrigatório (até 120), telefone (10/11 dígitos), CPF/CNPJ com verificadores e endereço para
    correspondência; aponta o erro de cada linha. `endereco` é o do empreendimento (atalho 'mesmo endereço')."""
    if len(dados.proprietarios) > MAX_PROPRIETARIOS:
        raise erro_campo("proprietarios", f"Máximo de {MAX_PROPRIETARIOS} proprietários.")
    saida: list[dict] = []
    detalhes: list[dict] = []
    for i, p in enumerate(dados.proprietarios):
        c = f"proprietarios.{i}."
        item = {
            "nome": _tentar(detalhes, sanear, p.nome, c + "nome", MAX_NOME_PROPRIETARIO, obrigatorio=True),
            "telefone": _tentar(detalhes, normalizar_telefone, p.telefone, c + "telefone"),
            "cpf_cnpj": _tentar(detalhes, normalizar_cpf_cnpj, p.cpf_cnpj, c + "cpf_cnpj"),
            "corr_numero": _tentar(detalhes, sanear, p.corr_numero, c + "corr_numero", MAX_NUMERO_ENDERECO),
            "corr_complemento": _tentar(detalhes, sanear, p.corr_complemento, c + "corr_complemento", MAX_ENDERECO_CAMPO),
            "corr_bairro": _tentar(detalhes, sanear, p.corr_bairro, c + "corr_bairro", MAX_ENDERECO_CAMPO),
            "ordem": i,
        }
        if p.correspondencia_mesmo_endereco:
            item.update(
                corr_logradouro=endereco["logradouro"], corr_municipio=endereco["municipio"],
                corr_uf=endereco["uf"], corr_cep=endereco["cep"],
            )
        else:
            item.update(
                corr_logradouro=_tentar(detalhes, sanear, p.corr_logradouro, c + "corr_logradouro", MAX_LOGRADOURO),
                corr_municipio=_tentar(detalhes, sanear, p.corr_municipio, c + "corr_municipio", MAX_MUNICIPIO),
                corr_uf=_tentar(detalhes, normalizar_uf, p.corr_uf, c + "corr_uf", padrao=None),
                corr_cep=_tentar(detalhes, normalizar_cep, p.corr_cep, c + "corr_cep"),
            )
        saida.append(item)
    if detalhes:
        raise ErroNegocio("VALIDACAO_CAMPO", "Dados inválidos.", 422, detalhes)
    return saida


def _validar(db: Session, dados: LocalIn, ignorar_id: int | None = None) -> dict:
    nome = sanear(dados.nome, "nome", MAX_NOME_LOCAL, obrigatorio=True)
    municipio = sanear(dados.municipio, "municipio", MAX_MUNICIPIO, obrigatorio=True)
    tipo = sanear(dados.tipo, "tipo", MAX_TIPO_LOCAL, obrigatorio=True)
    validar_coordenadas(dados.latitude, dados.longitude)
    numero_car = normalizar_car(dados.numero_car)
    erros_endereco: list[dict] = []
    logradouro = _tentar(erros_endereco, sanear, dados.logradouro, "logradouro", MAX_LOGRADOURO)
    uf = _tentar(erros_endereco, normalizar_uf, dados.uf)  # padrão MT
    cep = _tentar(erros_endereco, normalizar_cep, dados.cep)
    if erros_endereco:
        raise ErroNegocio("VALIDACAO_CAMPO", "Dados inválidos.", 422, erros_endereco)
    endereco = {"logradouro": logradouro, "municipio": municipio, "uf": uf, "cep": cep}
    proprietarios = _validar_proprietarios(dados, endereco)
    existente = repo.obter_por_nome(db, nome)
    if existente and existente.id != ignorar_id:
        raise erro_campo("nome", "Já existe um local com este nome.")
    return dict(
        nome=nome, municipio=municipio, tipo=tipo, latitude=dados.latitude, longitude=dados.longitude,
        ativo=dados.ativo, numero_car=numero_car, logradouro=logradouro, uf=uf, cep=cep,
        proprietarios=proprietarios,
    )


def _como_modelos(proprietarios: list[dict]) -> list[Proprietario]:
    return [Proprietario(**p) for p in proprietarios]


def criar(db: Session, dados: LocalIn) -> Local:
    valores = _validar(db, dados)
    proprietarios = valores.pop("proprietarios")
    local = repo.adicionar(db, Local(**valores, proprietarios=_como_modelos(proprietarios)))
    db.commit()
    return local


def atualizar(db: Session, local_id: int, dados: LocalIn) -> Local:
    local = obter(db, local_id)
    valores = _validar(db, dados, ignorar_id=local.id)
    proprietarios = valores.pop("proprietarios")
    for campo, valor in valores.items():
        setattr(local, campo, valor)
    local.proprietarios = _como_modelos(proprietarios)  # a lista enviada substitui a anterior
    db.commit()
    return local
