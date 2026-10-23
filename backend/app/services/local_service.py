from sqlalchemy.orm import Session

from app.domain.constantes import MAX_MUNICIPIO, MAX_NOME_LOCAL, MAX_TIPO_LOCAL
from app.domain.coordenadas import validar_coordenadas
from app.domain.texto import sanear
from app.errors import ErroNegocio, erro_campo
from app.models import Local
from app.repositories import local_repository as repo
from app.schemas.local import LocalIn


def listar(db: Session) -> list[Local]:
    return repo.listar(db)


def obter(db: Session, local_id: int) -> Local:
    local = repo.obter(db, local_id)
    if local is None:
        raise ErroNegocio("NAO_ENCONTRADO", "Local não encontrado.", 404)
    return local


def _validar(db: Session, dados: LocalIn, ignorar_id: int | None = None) -> dict:
    nome = sanear(dados.nome, "nome", MAX_NOME_LOCAL, obrigatorio=True)
    municipio = sanear(dados.municipio, "municipio", MAX_MUNICIPIO, obrigatorio=True)
    tipo = sanear(dados.tipo, "tipo", MAX_TIPO_LOCAL, obrigatorio=True)
    validar_coordenadas(dados.latitude, dados.longitude)
    existente = repo.obter_por_nome(db, nome)
    if existente and existente.id != ignorar_id:
        raise erro_campo("nome", "Já existe um local com este nome.")
    return dict(
        nome=nome, municipio=municipio, tipo=tipo, latitude=dados.latitude,
        longitude=dados.longitude, ativo=dados.ativo,
    )


def criar(db: Session, dados: LocalIn) -> Local:
    local = repo.adicionar(db, Local(**_validar(db, dados)))
    db.commit()
    return local


def atualizar(db: Session, local_id: int, dados: LocalIn) -> Local:
    local = obter(db, local_id)
    for campo, valor in _validar(db, dados, ignorar_id=local.id).items():
        setattr(local, campo, valor)
    db.commit()
    return local
