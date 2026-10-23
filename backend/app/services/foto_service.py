from datetime import datetime
from pathlib import PurePosixPath, PureWindowsPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import clock
from app.domain import imagem
from app.domain.texto import sanear
from app.domain.transicoes import exigir_editavel
from app.errors import ErroNegocio, erro_campo
from app.models import FotoVistoria, Inspecao
from app.schemas.foto import FotoPatch
from app.services import inspecao_service
from app.storage.arquivos import ArmazenamentoArquivos

MAX_FOTOS = 20
MAX_ANOTACAO = 1000
MAX_LEGENDA = 200
MAX_NOME = 200


def foto_dict(f: FotoVistoria) -> dict:
    base = f"/api/v1/inspecoes/{f.inspecao_id}/fotos/{f.id}/arquivo"
    return {
        "id": f.id, "inspecao_id": f.inspecao_id, "item_id": f.item_inspecao_id,
        "nome_original": f.nome_original, "mime_type": f.mime_type, "tamanho_bytes": f.tamanho_bytes,
        "largura": f.largura, "altura": f.altura, "legenda": f.legenda, "anotacao": f.anotacao,
        "data_captura": f.data_captura, "ordem": f.ordem, "criado_em": f.criado_em,
        "url_miniatura": f"{base}?versao=miniatura", "url_original": f"{base}?versao=original",
    }


def _nome_seguro(nome: str | None) -> str:
    """Só para exibição: o nome do usuário nunca compõe caminho em disco."""
    bruto = (nome or "").replace("\x00", "")
    base = PurePosixPath(PureWindowsPath(bruto).name).name.strip()
    return (base or "foto")[:MAX_NOME]


def _item_valido(inspecao: Inspecao, item_id: int | None) -> int | None:
    if item_id is None:
        return None
    if not any(i.id == item_id for i in inspecao.itens):
        raise ErroNegocio(
            "ITEM_NAO_PERTENCE_A_INSPECAO", "O item informado não pertence a esta inspeção.", 422,
            [{"campo": "item_id", "mensagem": "Item de outra inspeção."}],
        )
    return item_id


def listar(db: Session, inspecao_id: int) -> list[FotoVistoria]:
    return list(inspecao_service.obter(db, inspecao_id).fotos)


def obter(db: Session, inspecao_id: int, foto_id: int) -> FotoVistoria:
    inspecao = inspecao_service.obter(db, inspecao_id)
    for f in inspecao.fotos:
        if f.id == foto_id:
            return f
    raise ErroNegocio("NAO_ENCONTRADO", "Foto não encontrada.", 404)


def enviar(
    db: Session,
    storage: ArmazenamentoArquivos,
    inspecao_id: int,
    conteudo: bytes | None,
    nome_original: str | None,
    anotacao: str | None,
    legenda: str | None = None,
    item_id: int | None = None,
    data_captura: datetime | None = None,
) -> FotoVistoria:
    # 1) estado da inspeção (409)
    inspecao = inspecao_service.obter(db, inspecao_id)
    exigir_editavel(inspecao.status)
    # 2) campos e arquivo (422/413/415) — tudo validado antes de gravar em disco
    anotacao = sanear(anotacao, "anotacao", MAX_ANOTACAO, obrigatorio=True)
    legenda = sanear(legenda, "legenda", MAX_LEGENDA)
    item_id = _item_valido(inspecao, item_id)
    if conteudo is None:
        raise erro_campo("arquivo", "Campo obrigatório.")
    processada = imagem.processar(conteudo)
    # 3) limite e duplicidade (409)
    if len(inspecao.fotos) >= MAX_FOTOS:
        raise ErroNegocio("LIMITE_FOTOS_EXCEDIDO", f"Limite de {MAX_FOTOS} fotos por inspeção.", 409)
    if any(f.hash_sha256 == processada.hash_sha256 for f in inspecao.fotos):
        raise ErroNegocio("FOTO_DUPLICADA", "Esta imagem já foi anexada nesta inspeção.", 409)
    # 4) gravar: arquivo antes do registro; compensar se o registro falhar (RN28)
    caminhos: list[str] = []
    try:
        orig = storage.salvar(inspecao_id, "original", processada.extensao, processada.original)
        caminhos.append(orig)
        mini = storage.salvar(inspecao_id, "miniatura", processada.extensao, processada.miniatura)
        caminhos.append(mini)
        foto = FotoVistoria(
            inspecao_id=inspecao_id, item_inspecao_id=item_id, nome_original=_nome_seguro(nome_original),
            arquivo_path=orig, miniatura_path=mini, mime_type=processada.mime_type,
            tamanho_bytes=len(processada.original), largura=processada.largura, altura=processada.altura,
            hash_sha256=processada.hash_sha256, legenda=legenda, anotacao=anotacao,
            data_captura=data_captura, ordem=max((f.ordem for f in inspecao.fotos), default=0) + 1,
            criado_em=clock.agora(),
        )
        inspecao.fotos.append(foto)  # RN24: não muda o status
        db.commit()
    except Exception:
        db.rollback()
        for c in caminhos:
            storage.remover(c)
        raise
    return foto


def atualizar(db: Session, inspecao_id: int, foto_id: int, dados: FotoPatch) -> FotoVistoria:
    inspecao = inspecao_service.obter(db, inspecao_id)
    foto = obter(db, inspecao_id, foto_id)
    exigir_editavel(inspecao.status)  # RN23
    enviados = dados.model_fields_set
    novos: dict = {}
    if "anotacao" in enviados:
        novos["anotacao"] = sanear(dados.anotacao, "anotacao", MAX_ANOTACAO, obrigatorio=True)  # RN33
    if "legenda" in enviados:
        novos["legenda"] = sanear(dados.legenda, "legenda", MAX_LEGENDA)
    if "item_id" in enviados:
        novos["item_inspecao_id"] = _item_valido(inspecao, dados.item_id)
    if "ordem" in enviados:
        if dados.ordem is None or dados.ordem < 1:
            raise erro_campo("ordem", "Deve ser um inteiro maior ou igual a 1.")
        novos["ordem"] = dados.ordem
    for campo, valor in novos.items():
        setattr(foto, campo, valor)
    if novos:
        db.commit()
    return foto


def excluir(db: Session, storage: ArmazenamentoArquivos, inspecao_id: int, foto_id: int) -> None:
    inspecao = inspecao_service.obter(db, inspecao_id)
    foto = obter(db, inspecao_id, foto_id)
    exigir_editavel(inspecao.status)
    caminhos = [foto.arquivo_path, foto.miniatura_path]
    inspecao.fotos.remove(foto)
    db.commit()  # registro primeiro; depois os arquivos (RN28, RN30)
    for c in caminhos:
        storage.remover(c)


def conteudo_arquivo(
    db: Session, storage: ArmazenamentoArquivos, inspecao_id: int, foto_id: int, versao: str
) -> tuple[bytes, str]:
    foto = obter(db, inspecao_id, foto_id)
    caminho = foto.miniatura_path if versao == "miniatura" else foto.arquivo_path
    dados = storage.ler(caminho)
    if dados is None:
        raise ErroNegocio("FOTO_ARQUIVO_AUSENTE", "Arquivo da foto ausente em disco.", 404)
    return dados, foto.mime_type


def verificar(db: Session, storage: ArmazenamentoArquivos) -> dict:
    registrados: set[str] = set()
    sem_arquivo: list[str] = []
    for f in db.scalars(select(FotoVistoria)):
        for caminho in (f.arquivo_path, f.miniatura_path):
            registrados.add(caminho)
            if not storage.existe(caminho):
                sem_arquivo.append(caminho)
    soltos = [c for c in storage.listar() if c not in registrados]
    return {
        "registros_sem_arquivo": sorted(sem_arquivo),
        "arquivos_sem_registro": soltos,
        "total_inconsistencias": len(sem_arquivo) + len(soltos),
    }
