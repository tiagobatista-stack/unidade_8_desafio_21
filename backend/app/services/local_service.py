from sqlalchemy.orm import Session

from app.domain.constantes import MAX_MUNICIPIO, MAX_NOME_LOCAL, MAX_TIPO_LOCAL
from app.domain.contato import (
    MAX_NOME_PROPRIETARIO,
    MAX_PROPRIETARIOS,
    normalizar_car,
    normalizar_telefone,
)
from app.domain.coordenadas import validar_coordenadas
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


def _validar_proprietarios(dados: LocalIn) -> list[dict]:
    """Nome obrigatório (≤120) e telefone opcional (10/11 dígitos); aponta o erro de cada linha."""
    if len(dados.proprietarios) > MAX_PROPRIETARIOS:
        raise erro_campo("proprietarios", f"Máximo de {MAX_PROPRIETARIOS} proprietários.")
    saida: list[dict] = []
    detalhes: list[dict] = []
    for i, p in enumerate(dados.proprietarios):
        nome = telefone = None
        try:
            nome = sanear(p.nome, f"proprietarios.{i}.nome", MAX_NOME_PROPRIETARIO, obrigatorio=True)
        except ErroNegocio as e:
            detalhes += e.detalhes
        try:
            telefone = normalizar_telefone(p.telefone, f"proprietarios.{i}.telefone")
        except ErroNegocio as e:
            detalhes += e.detalhes
        saida.append({"nome": nome, "telefone": telefone, "ordem": i})
    if detalhes:
        raise ErroNegocio("VALIDACAO_CAMPO", "Dados inválidos.", 422, detalhes)
    return saida


def _validar(db: Session, dados: LocalIn, ignorar_id: int | None = None) -> dict:
    nome = sanear(dados.nome, "nome", MAX_NOME_LOCAL, obrigatorio=True)
    municipio = sanear(dados.municipio, "municipio", MAX_MUNICIPIO, obrigatorio=True)
    tipo = sanear(dados.tipo, "tipo", MAX_TIPO_LOCAL, obrigatorio=True)
    validar_coordenadas(dados.latitude, dados.longitude)
    numero_car = normalizar_car(dados.numero_car)
    proprietarios = _validar_proprietarios(dados)
    existente = repo.obter_por_nome(db, nome)
    if existente and existente.id != ignorar_id:
        raise erro_campo("nome", "Já existe um local com este nome.")
    return dict(
        nome=nome, municipio=municipio, tipo=tipo, latitude=dados.latitude, longitude=dados.longitude,
        ativo=dados.ativo, numero_car=numero_car, proprietarios=proprietarios,
    )


def _como_modelos(proprietarios: list[dict]) -> list[Proprietario]:
    return [Proprietario(nome=p["nome"], telefone=p["telefone"], ordem=p["ordem"]) for p in proprietarios]


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
