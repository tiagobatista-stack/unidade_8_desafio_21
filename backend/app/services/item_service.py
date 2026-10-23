from sqlalchemy.orm import Session

from app import clock
from app.domain.constantes import MAX_DESCRICAO_ITEM, MAX_OBSERVACAO_ITEM, Origem, Situacao, Status
from app.domain.datas import realizacao_do_primeiro_item
from app.domain.texto import sanear
from app.domain.transicoes import exigir_editavel, validar_transicao
from app.errors import ErroNegocio, erro_campo
from app.models import Inspecao, ItemInspecao
from app.schemas.inspecao import ItemIn, ItemPatch
from app.services import inspecao_service


def _item(inspecao: Inspecao, item_id: int) -> ItemInspecao:
    for item in inspecao.itens:
        if item.id == item_id:
            return item
    raise ErroNegocio("NAO_ENCONTRADO", "Item não encontrado nesta inspeção.", 404)


def listar(db: Session, inspecao_id: int) -> list[ItemInspecao]:
    return list(inspecao_service.obter(db, inspecao_id).itens)


def adicionar_avulso(db: Session, inspecao_id: int, dados: ItemIn) -> ItemInspecao:
    inspecao = inspecao_service.obter(db, inspecao_id)
    exigir_editavel(inspecao.status)
    descricao = sanear(dados.descricao, "descricao", MAX_DESCRICAO_ITEM, obrigatorio=True)
    ordem = max((i.ordem for i in inspecao.itens), default=0) + 1
    item = ItemInspecao(
        descricao=descricao, critico=dados.critico, origem=Origem.AVULSO, ordem=ordem,
        situacao=Situacao.NAO_RESPONDIDO,
    )
    inspecao.itens.append(item)  # RN09: vale só nesta inspeção
    inspecao.atualizado_em = clock.agora()
    db.commit()
    return item


def atualizar(db: Session, inspecao_id: int, item_id: int, dados: ItemPatch) -> ItemInspecao:
    inspecao = inspecao_service.obter(db, inspecao_id)
    item = _item(inspecao, item_id)
    exigir_editavel(inspecao.status)  # RN07
    enviados = dados.model_fields_set

    nova_observacao = item.observacao
    if "observacao" in enviados:
        nova_observacao = sanear(dados.observacao, "observacao", MAX_OBSERVACAO_ITEM)
    nova_situacao = None
    if "situacao" in enviados:
        if dados.situacao is None:
            raise erro_campo("situacao", "Valor inválido.")
        nova_situacao = dados.situacao

    # 1º item registrado em inspeção ABERTA: vira EM_ANDAMENTO (P1 aplicado em realizacao_do_primeiro_item)
    iniciar = (
        nova_situacao is not None
        and nova_situacao != Situacao.NAO_RESPONDIDO
        and inspecao.status == Status.ABERTA
    )
    realizacao = None
    if iniciar:
        realizacao = realizacao_do_primeiro_item(inspecao.data_agendamento, clock.hoje())
        validar_transicao(Status.ABERTA, Status.EM_ANDAMENTO)

    if iniciar:
        inspecao.status = Status.EM_ANDAMENTO
        if inspecao.data_realizacao is None:
            inspecao.data_realizacao = realizacao
    if nova_situacao is not None:
        item.situacao = nova_situacao
    if "observacao" in enviados:
        item.observacao = nova_observacao
    inspecao.atualizado_em = clock.agora()
    db.commit()
    return item


def remover(db: Session, inspecao_id: int, item_id: int) -> None:
    inspecao = inspecao_service.obter(db, inspecao_id)
    item = _item(inspecao, item_id)
    exigir_editavel(inspecao.status)
    if item.origem == Origem.MODELO:  # RN09
        raise ErroNegocio(
            "ITEM_DE_MODELO_NAO_REMOVIVEL", "Item do modelo não pode ser removido.", 409
        )
    for foto in inspecao.fotos:  # RN29: a foto permanece, sem vínculo
        if foto.item_inspecao_id == item.id:
            foto.item_inspecao_id = None
    inspecao.itens.remove(item)
    inspecao.atualizado_em = clock.agora()
    db.commit()
