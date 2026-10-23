import uuid

from sqlalchemy.orm import Session

from app import clock
from app.domain.constantes import (
    ASSUNTO_OUTRO,
    ASSUNTOS,
    MAX_ASSUNTO_OUTRO,
    MAX_ATOS,
    MAX_COMARCA,
    MAX_EQUIPE,
    MAX_INTERESSADO,
    MAX_MEMBRO_CAMPO,
    MAX_MOTIVO_CANCELAMENTO,
    MAX_NUMERO_ATO,
    MAX_NUMERO_RELATORIO_SEMA,
    MAX_PROVIDENCIAS,
    TIPOS_ATO,
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
from app.models import AtoLavrado, EquipeMembro, Inspecao, ItemInspecao
from app.repositories import inspecao_repository as repo
from app.repositories import local_repository
from app.services import empreendimento_service, numeracao_service
from app.schemas.inspecao import AtoIn, InspecaoIn, InspecaoPatch, MembroIn

# RN14: campos editáveis por status
# O número do processo é corrigível enquanto a inspeção não for encerrada (acréscimo ao RN14 original).
# R4: os campos da capa da SEMA (interessado, assunto, equipe, providências) seguem o mesmo critério do processo.
CAMPOS_CAPA = {
    "interessado_orgao", "interessado_unidade", "interessado_comarca", "interessado_requerente",
    "assunto_tipo", "assunto_outro", "providencias_texto", "numero_relatorio_sema", "equipe", "atos",
}
CAMPOS_EDITAVEIS = {
    Status.ABERTA: {
        "numero_processo", "local_id", "data_agendamento", "objetivo", "observacoes", "observacoes_vistoria",
    } | CAMPOS_CAPA,
    Status.EM_ANDAMENTO: {"numero_processo", "data_realizacao", "observacoes", "observacoes_vistoria"} | CAMPOS_CAPA,
    # Depois do fechamento só se registra o que a SEMA atribui: número oficial do relatório e número dos atos.
    Status.FINALIZADA: {"numero_relatorio_sema", "atos"},
}
CAMPOS_TEXTO_CAPA = {  # campo -> máximo
    "interessado_orgao": MAX_INTERESSADO, "interessado_unidade": MAX_INTERESSADO,
    "interessado_comarca": MAX_COMARCA, "interessado_requerente": MAX_INTERESSADO,
    "providencias_texto": MAX_PROVIDENCIAS, "numero_relatorio_sema": MAX_NUMERO_RELATORIO_SEMA,
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
        "equipe": inspecao.equipe, "atos": inspecao.atos,
        "local": inspecao.local, "itens": itens, "fotos": [foto_dict(f) for f in inspecao.fotos],
        "empreendimento": empreendimento_service.da_inspecao(inspecao),
        "numero_relatorio": inspecao.numero_relatorio if inspecao.status == Status.FINALIZADA else None,
        "campos_editaveis": sorted(CAMPOS_EDITAVEIS.get(inspecao.status, set())),
        "fechamento_bloqueado_motivo": motivo_fechamento_bloqueado(inspecao.status),
        "registro_bloqueado_motivo": motivo_registro_bloqueado(inspecao.status, inspecao.data_agendamento, clock.hoje()),
        "resumo_itens": resumo_itens(inspecao),
    }


def _equipe(membros: list[MembroIn] | None) -> list[EquipeMembro]:
    """Lista (0..20) de nome, cargo e órgão; aponta o erro de cada linha."""
    membros = membros or []
    if len(membros) > MAX_EQUIPE:
        raise erro_campo("equipe", f"Máximo de {MAX_EQUIPE} membros.")
    saida, detalhes = [], []
    for i, m in enumerate(membros):
        try:
            saida.append(
                EquipeMembro(
                    nome=sanear(m.nome, f"equipe.{i}.nome", MAX_MEMBRO_CAMPO, obrigatorio=True),
                    cargo=sanear(m.cargo, f"equipe.{i}.cargo", MAX_MEMBRO_CAMPO),
                    orgao=sanear(m.orgao, f"equipe.{i}.orgao", MAX_MEMBRO_CAMPO),
                    ordem=i,
                )
            )
        except ErroNegocio as e:
            detalhes += e.detalhes
    if detalhes:
        raise ErroNegocio("VALIDACAO_CAMPO", "Dados inválidos.", 422, detalhes)
    return saida


def _atos(atos: list[AtoIn] | None) -> list[AtoLavrado]:
    """Atos lavrados: tipo da lista fixa; número opcional (vazio até lavrar no sistema da SEMA)."""
    atos = atos or []
    if len(atos) > MAX_ATOS:
        raise erro_campo("atos", f"Máximo de {MAX_ATOS} atos.")
    saida, detalhes = [], []
    for i, a in enumerate(atos):
        if a.tipo not in TIPOS_ATO:
            detalhes.append({"campo": f"atos.{i}.tipo", "mensagem": f"Tipo inválido. Use: {', '.join(TIPOS_ATO)}."})
            continue
        try:
            saida.append(
                AtoLavrado(tipo=a.tipo, numero=sanear(a.numero, f"atos.{i}.numero", MAX_NUMERO_ATO), ordem=i)
            )
        except ErroNegocio as e:
            detalhes += e.detalhes
    if detalhes:
        raise ErroNegocio("VALIDACAO_CAMPO", "Dados inválidos.", 422, detalhes)
    return saida


def _assunto(tipo: str | None, outro: str | None) -> tuple[str | None, str | None]:
    """Tipo da lista; 'Outro' exige o texto livre, e qualquer outro tipo descarta o texto."""
    tipo = (tipo or "").strip() or None
    if tipo is None:
        return None, None
    if tipo not in ASSUNTOS:
        raise erro_campo("assunto_tipo", f"Assunto inválido. Use um dos: {'; '.join(ASSUNTOS)}.")
    if tipo != ASSUNTO_OUTRO:
        return tipo, None
    return tipo, sanear(outro, "assunto_outro", MAX_ASSUNTO_OUTRO, obrigatorio=True)


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
    capa = {c: sanear(getattr(dados, c), c, m) for c, m in CAMPOS_TEXTO_CAPA.items()}
    assunto_tipo, assunto_outro = _assunto(dados.assunto_tipo, dados.assunto_outro)

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
        **capa,
        assunto_tipo=assunto_tipo,
        assunto_outro=assunto_outro,
        equipe=_equipe(dados.equipe),
        atos=_atos(dados.atos),
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
    if inspecao.status == Status.FINALIZADA:
        return _editar_pos_fechamento(db, inspecao, dados)
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

    for campo, maximo in CAMPOS_TEXTO_CAPA.items():
        if campo in enviados:
            novos[campo] = sanear(getattr(dados, campo), campo, maximo)
    if enviados & {"assunto_tipo", "assunto_outro"}:
        tipo = dados.assunto_tipo if "assunto_tipo" in enviados else inspecao.assunto_tipo
        outro = dados.assunto_outro if "assunto_outro" in enviados else inspecao.assunto_outro
        novos["assunto_tipo"], novos["assunto_outro"] = _assunto(tipo, outro)
    if "equipe" in enviados:
        novos["equipe"] = _equipe(dados.equipe)  # a lista enviada substitui a anterior
    if "atos" in enviados:
        novos["atos"] = _atos(dados.atos)

    if novos:
        for campo, valor in novos.items():
            setattr(inspecao, campo, valor)
        inspecao.atualizado_em = clock.agora()
        db.commit()
        db.refresh(inspecao)
    return inspecao


def _editar_pos_fechamento(db: Session, inspecao: Inspecao, dados: InspecaoPatch) -> Inspecao:
    """Finalizada é imutável (RN07), salvo registrar o que a SEMA atribui depois: o nº oficial do relatório e o
    número de cada ato já listado (tipo e quantidade dos atos não mudam)."""
    enviados = dados.model_fields_set
    if enviados - CAMPOS_EDITAVEIS[Status.FINALIZADA]:
        exigir_editavel(inspecao.status)  # INSPECAO_IMUTAVEL, como antes
    numeros: dict[int, str | None] = {}
    if "atos" in enviados:
        atuais = {a.id: a for a in inspecao.atos}
        recebidos = dados.atos or []
        if len(recebidos) != len(atuais) or sorted(a.id or 0 for a in recebidos) != sorted(atuais):
            raise ErroNegocio(
                "CAMPO_NAO_EDITAVEL_NO_STATUS",
                "Na inspeção finalizada só o número dos atos já listados pode ser alterado.",
                409,
                [{"campo": "atos", "mensagem": "Envie os mesmos atos (com id), alterando apenas o número."}],
            )
        for i, a in enumerate(recebidos):
            if a.tipo != atuais[a.id].tipo:
                raise ErroNegocio(
                    "CAMPO_NAO_EDITAVEL_NO_STATUS", "O tipo do ato não pode ser alterado depois do fechamento.",
                    409, [{"campo": f"atos.{i}.tipo", "mensagem": "Não editável neste status."}],
                )
            numeros[a.id] = sanear(a.numero, f"atos.{i}.numero", MAX_NUMERO_ATO)
    if "numero_relatorio_sema" in enviados:
        inspecao.numero_relatorio_sema = sanear(
            dados.numero_relatorio_sema, "numero_relatorio_sema", MAX_NUMERO_RELATORIO_SEMA
        )
    for ato in inspecao.atos:
        if ato.id in numeros:
            ato.numero = numeros[ato.id]
    if enviados:
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
    mensagem = "Há itens pendentes que impedem o fechamento."
    if not inspecao.equipe:  # R4: a capa da SEMA exige a equipe técnica
        if not detalhes:
            mensagem = "Há pendências que impedem o fechamento."
        detalhes.append({"campo": "equipe", "mensagem": "Informe ao menos um membro da equipe técnica."})
    if detalhes:
        raise ErroNegocio("FECHAMENTO_BLOQUEADO", mensagem, 422, detalhes)
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

