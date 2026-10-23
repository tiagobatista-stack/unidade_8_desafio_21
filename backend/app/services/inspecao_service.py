import uuid

from sqlalchemy.orm import Session

from app import clock
from app.domain.constantes import (
    MAX_MOTIVO_CANCELAMENTO,
    MAX_NUMERO_PROCESSO,
    MAX_OBJETIVO,
    MAX_OBSERVACOES,
    MAX_OBSERVACOES_VISTORIA,
    Origem,
    Situacao,
    Status,
)
from app.domain.datas import validar_realizacao
from app.domain.fechamento import problemas_fechamento
from app.domain.orientacoes import MSG_NAO_INICIADA, motivo_fechamento_bloqueado, motivo_registro_bloqueado
from app.domain.resultado import calcular_resultado
from app.domain.texto import sanear
from app.domain.transicoes import exigir_editavel, validar_transicao
from app.errors import ErroNegocio, erro_campo
from app.models import Inspecao, ItemInspecao
from app.repositories import inspecao_repository as repo
from app.repositories import local_repository
from app.services import empreendimento_service, numeracao_service
from app.schemas.inspecao import InspecaoIn, InspecaoPatch

# RN14: campos editáveis por status
# O número do processo é corrigível enquanto a inspeção não for encerrada (acréscimo ao RN14 original).
CAMPOS_EDITAVEIS = {
    Status.ABERTA: {"numero_processo", "local_id", "data_agendamento", "objetivo", "observacoes", "observacoes_vistoria"},
    Status.EM_ANDAMENTO: {"numero_processo", "data_realizacao", "observacoes", "observacoes_vistoria"},
}


def obter(db: Session, inspecao_id: int) -> Inspecao:
    inspecao = repo.obter(db, inspecao_id)
    if inspecao is None:
        raise ErroNegocio("NAO_ENCONTRADO", "Inspeção não encontrada.", 404)
    return inspecao


def resumo_itens(inspecao: Inspecao) -> dict:
    itens = inspecao.itens
    return {
        "total": len(itens),
        "respondidos": sum(1 for i in itens if i.situacao != Situacao.NAO_RESPONDIDO),
        "nao_conformes": sum(1 for i in itens if i.situacao == Situacao.NAO_CONFORME),
    }


def detalhe(inspecao: Inspecao) -> dict:
    from app.services.foto_service import foto_dict

    por_item: dict[int, int] = {}
    for f in inspecao.fotos:
        if f.item_inspecao_id is not None:
            por_item[f.item_inspecao_id] = por_item.get(f.item_inspecao_id, 0) + 1
    itens = [
        {**{c.key: getattr(i, c.key) for c in ItemInspecao.__table__.columns}, "qtd_fotos": por_item.get(i.id, 0)}
        for i in inspecao.itens
    ]
    return {
        **{c.key: getattr(inspecao, c.key) for c in Inspecao.__table__.columns},
        "local": inspecao.local, "itens": itens, "fotos": [foto_dict(f) for f in inspecao.fotos],
        "empreendimento": empreendimento_service.da_inspecao(inspecao),
        "numero_relatorio": inspecao.numero_relatorio if inspecao.status == Status.FINALIZADA else None,
        "campos_editaveis": sorted(CAMPOS_EDITAVEIS.get(inspecao.status, set())),
        "fechamento_bloqueado_motivo": motivo_fechamento_bloqueado(inspecao.status),
        "registro_bloqueado_motivo": motivo_registro_bloqueado(inspecao.status, inspecao.data_agendamento, clock.hoje()),
        "resumo_itens": resumo_itens(inspecao),
    }


def _local_valido(db: Session, local_id: int):
    local = local_repository.obter(db, local_id)
    if local is None or not local.ativo:
        raise erro_campo("local_id", "Local inexistente ou inativo.")
    return local


def criar(db: Session, dados: InspecaoIn) -> Inspecao:
    _local_valido(db, dados.local_id)
    numero_processo = sanear(dados.numero_processo, "numero_processo", MAX_NUMERO_PROCESSO, obrigatorio=True)
    objetivo = sanear(dados.objetivo, "objetivo", MAX_OBJETIVO, obrigatorio=True)
    observacoes = sanear(dados.observacoes, "observacoes", MAX_OBSERVACOES)
    obs_vistoria = sanear(dados.observacoes_vistoria, "observacoes_vistoria", MAX_OBSERVACOES_VISTORIA)
    if dados.data_realizacao is not None:
        validar_realizacao(dados.data_realizacao, dados.data_agendamento, clock.hoje())

    agora = clock.agora()
    inspecao = Inspecao(
        codigo=f"TMP-{uuid.uuid4().hex[:12]}",
        numero_processo=numero_processo,
        local_id=dados.local_id,
        objetivo=objetivo,
        observacoes=observacoes,
        observacoes_vistoria=obs_vistoria,
        data_agendamento=dados.data_agendamento,
        data_realizacao=dados.data_realizacao,
        status=Status.ABERTA,
        criado_em=agora,
        atualizado_em=agora,
    )
    for modelo in repo.modelo_ativo(db):  # RN09: cópia do modelo
        inspecao.itens.append(
            ItemInspecao(
                modelo_item_id=modelo.id, descricao=modelo.descricao, critico=modelo.critico,
                origem=Origem.MODELO, ordem=modelo.ordem, situacao=Situacao.NAO_RESPONDIDO,
            )
        )
    repo.adicionar(db, inspecao)
    inspecao.codigo = f"INS-{inspecao.id:03d}"  # RN03
    db.commit()
    return inspecao


def listar(db: Session, status, data_inicio, data_fim, local_id, numero_processo, pagina: int, tamanho: int):
    if data_inicio and data_fim and data_inicio > data_fim:
        raise erro_campo("data_inicio", "Deve ser anterior ou igual a data_fim.")
    return repo.listar(db, status, data_inicio, data_fim, local_id, numero_processo, pagina, tamanho)


def editar(db: Session, inspecao_id: int, dados: InspecaoPatch) -> Inspecao:
    inspecao = obter(db, inspecao_id)
    exigir_editavel(inspecao.status)  # RN07
    enviados = dados.model_fields_set
    proibidos = sorted(enviados - CAMPOS_EDITAVEIS[inspecao.status])
    if proibidos:  # RN14
        raise ErroNegocio(
            "CAMPO_NAO_EDITAVEL_NO_STATUS",
            f"Campos não editáveis na inspeção {inspecao.status}: {', '.join(proibidos)}.",
            409,
            [{"campo": c, "mensagem": "Não editável neste status."} for c in proibidos],
        )

    novos: dict = {}
    if "numero_processo" in enviados:
        novos["numero_processo"] = sanear(
            dados.numero_processo, "numero_processo", MAX_NUMERO_PROCESSO, obrigatorio=True
        )
    if "local_id" in enviados:
        if dados.local_id is None:
            raise erro_campo("local_id", "Campo obrigatório.")
        _local_valido(db, dados.local_id)
        novos["local_id"] = dados.local_id
    if "data_agendamento" in enviados:
        if dados.data_agendamento is None:
            raise erro_campo("data_agendamento", "Campo obrigatório.")
        if inspecao.data_realizacao is not None:
            validar_realizacao(inspecao.data_realizacao, dados.data_agendamento, clock.hoje())
        novos["data_agendamento"] = dados.data_agendamento
    if "objetivo" in enviados:
        novos["objetivo"] = sanear(dados.objetivo, "objetivo", MAX_OBJETIVO, obrigatorio=True)
    if "data_realizacao" in enviados:
        if dados.data_realizacao is None:
            raise erro_campo("data_realizacao", "Campo obrigatório.")
        validar_realizacao(dados.data_realizacao, inspecao.data_agendamento, clock.hoje())
        novos["data_realizacao"] = dados.data_realizacao
    if "observacoes" in enviados:
        novos["observacoes"] = sanear(dados.observacoes, "observacoes", MAX_OBSERVACOES)
    if "observacoes_vistoria" in enviados:
        novos["observacoes_vistoria"] = sanear(
            dados.observacoes_vistoria, "observacoes_vistoria", MAX_OBSERVACOES_VISTORIA
        )

    if novos:
        for campo, valor in novos.items():
            setattr(inspecao, campo, valor)
        inspecao.atualizado_em = clock.agora()
        db.commit()
        db.refresh(inspecao)
    return inspecao


def cancelar(db: Session, inspecao_id: int, motivo: str) -> Inspecao:
    inspecao = obter(db, inspecao_id)
    validar_transicao(inspecao.status, Status.CANCELADA)  # RN08, P5
    motivo = sanear(motivo, "motivo", MAX_MOTIVO_CANCELAMENTO, obrigatorio=True)
    inspecao.status = Status.CANCELADA
    inspecao.motivo_cancelamento = motivo
    inspecao.atualizado_em = clock.agora()
    db.commit()
    return inspecao


def fechar(db: Session, inspecao_id: int) -> Inspecao:
    inspecao = obter(db, inspecao_id)
    if inspecao.status == Status.ABERTA:  # P3, com orientação do que fazer (código estável TRANSICAO_INVALIDA)
        raise ErroNegocio("TRANSICAO_INVALIDA", MSG_NAO_INICIADA, 409)
    validar_transicao(inspecao.status, Status.FINALIZADA)  # P3: só fecha EM_ANDAMENTO
    detalhes = problemas_fechamento(inspecao.itens)  # RN04, RN05
    if detalhes:
        raise ErroNegocio(
            "FECHAMENTO_BLOQUEADO", "Há itens pendentes que impedem o fechamento.", 422, detalhes
        )
    agora = clock.agora()
    # Cópia e número primeiro: a reserva do número consulta o banco (autoflush) e a inspeção ainda não pode
    # estar pela metade (resultado sem status FINALIZADA violaria o CHECK). Tudo vai no mesmo commit.
    empreendimento_service.copiar_no_fechamento(inspecao)  # C2: o relatório não muda se o Local for editado depois
    numeracao_service.atribuir_numero(db, inspecao, clock.hoje().year)  # C3: número NNNN/AAAA, nunca reutilizado
    inspecao.resultado = calcular_resultado(inspecao.itens)  # RN06
    inspecao.status = Status.FINALIZADA
    inspecao.fechado_em = agora
    inspecao.atualizado_em = agora
    db.commit()
    return inspecao

