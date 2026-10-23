from datetime import date

import pytest

from app.errors import ErroNegocio
from app.models import Inspecao
from app.schemas.inspecao import InspecaoIn, InspecaoPatch, ItemIn, ItemPatch
from app.services import inspecao_service as svc
from app.services import item_service as itens


def nova(db, **kw):
    base = dict(numero_processo="SEMA-PRO-2026/12345", local_id=1, data_agendamento=date(2026, 10, 20), objetivo="Vistoria")
    base.update(kw)
    return svc.criar(db, InspecaoIn(**base))


def responder(db, insp, situacoes: dict[int, str], obs: dict[int, str] | None = None):
    for item in list(insp.itens):
        sit = situacoes.get(item.ordem, "CONFORME")
        dados = {"situacao": sit}
        if obs and item.ordem in obs:
            dados["observacao"] = obs[item.ordem]
        itens.atualizar(db, insp.id, item.id, ItemPatch(**dados))


def codigo_de_erro(fn, *a, **kw):
    with pytest.raises(ErroNegocio) as e:
        fn(*a, **kw)
    return e.value


# ---------- cadastro ----------
def test_cadastro_valido(exemplos):  # CA01, CA04
    a = nova(exemplos)
    b = nova(exemplos)
    assert a.status == "ABERTA" and a.data_realizacao is None
    assert a.codigo == "INS-006" and b.codigo == "INS-007"  # sequencial após as 5 do exemplo
    assert len(a.itens) == 6 and all(i.situacao == "NAO_RESPONDIDO" for i in a.itens)


def test_cadastro_sem_local_valido(exemplos):  # CA02, RN01
    e = codigo_de_erro(nova, exemplos, local_id=999)
    assert e.codigo == "VALIDACAO_CAMPO" and e.detalhes[0]["campo"] == "local_id"


def test_cadastro_realizacao_futura(exemplos):  # CA03
    e = codigo_de_erro(nova, exemplos, data_realizacao=date(2026, 10, 24))
    assert e.codigo == "DATA_REALIZACAO_FUTURA"


def test_cadastro_realizacao_anterior_ao_agendamento(exemplos):  # CA32
    e = codigo_de_erro(nova, exemplos, data_realizacao=date(2026, 10, 19))
    assert e.codigo == "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO"


def test_cadastro_agendamento_futuro_aceito(exemplos):  # CA03, CA30
    insp = nova(exemplos, data_agendamento=date(2026, 10, 28))
    assert insp.status == "ABERTA"


def test_cadastro_objetivo_obrigatorio(exemplos):
    assert codigo_de_erro(nova, exemplos, objetivo="   ").codigo == "VALIDACAO_CAMPO"


# ---------- itens ----------
def test_primeiro_item_inicia_inspecao(exemplos):  # CA05, CA06, CA31
    insp = nova(exemplos)
    itens.atualizar(exemplos, insp.id, insp.itens[0].id, ItemPatch(situacao="CONFORME"))
    exemplos.refresh(insp)
    assert insp.status == "EM_ANDAMENTO"
    assert insp.data_realizacao == date(2026, 10, 23)
    assert insp.itens[0].situacao == "CONFORME"


def test_primeiro_item_em_agendada_futura_e_bloqueado(exemplos):  # P1 / CA32
    insp = exemplos.query(Inspecao).filter_by(codigo="INS-005").one()
    e = codigo_de_erro(itens.atualizar, exemplos, insp.id, insp.itens[0].id, ItemPatch(situacao="CONFORME"))
    assert e.codigo == "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO" and e.status == 422
    assert "28/10/2026" in e.mensagem
    exemplos.refresh(insp)
    assert insp.status == "ABERTA" and insp.data_realizacao is None
    assert insp.itens[0].situacao == "NAO_RESPONDIDO"


def test_so_observacao_nao_inicia(exemplos):
    insp = nova(exemplos)
    itens.atualizar(exemplos, insp.id, insp.itens[0].id, ItemPatch(observacao="nota"))
    exemplos.refresh(insp)
    assert insp.status == "ABERTA"


def test_item_avulso_so_na_propria_inspecao(exemplos):  # CA07
    a, b = nova(exemplos), nova(exemplos)
    itens.adicionar_avulso(exemplos, a.id, ItemIn(descricao="Cerca perimetral"))
    exemplos.refresh(a), exemplos.refresh(b)
    assert len(a.itens) == 7 and len(b.itens) == 6
    assert a.itens[-1].origem == "AVULSO" and a.itens[-1].ordem == 7


def test_item_de_modelo_nao_removivel(exemplos):  # RN09
    insp = nova(exemplos)
    e = codigo_de_erro(itens.remover, exemplos, insp.id, insp.itens[0].id)
    assert e.codigo == "ITEM_DE_MODELO_NAO_REMOVIVEL"


def test_remover_item_avulso(exemplos):
    insp = nova(exemplos)
    av = itens.adicionar_avulso(exemplos, insp.id, ItemIn(descricao="x"))
    itens.remover(exemplos, insp.id, av.id)
    exemplos.refresh(insp)
    assert len(insp.itens) == 6


def test_itens_de_finalizada_nao_alteraveis(exemplos):  # CA08
    insp = exemplos.query(Inspecao).filter_by(codigo="INS-001").one()
    e = codigo_de_erro(itens.atualizar, exemplos, insp.id, insp.itens[0].id, ItemPatch(situacao="NAO_CONFORME"))
    assert e.codigo == "INSPECAO_IMUTAVEL" and e.status == 409
    assert codigo_de_erro(itens.adicionar_avulso, exemplos, insp.id, ItemIn(descricao="x")).status == 409


def test_item_de_outra_inspecao_404(exemplos):
    a, b = nova(exemplos), nova(exemplos)
    e = codigo_de_erro(itens.atualizar, exemplos, a.id, b.itens[0].id, ItemPatch(situacao="CONFORME"))
    assert e.status == 404


def test_voltar_para_nao_respondido_permitido(exemplos):  # P4
    insp = nova(exemplos)
    itens.atualizar(exemplos, insp.id, insp.itens[0].id, ItemPatch(situacao="CONFORME"))
    itens.atualizar(exemplos, insp.id, insp.itens[0].id, ItemPatch(situacao="NAO_RESPONDIDO"))
    exemplos.refresh(insp)
    assert insp.itens[0].situacao == "NAO_RESPONDIDO"


# ---------- fechamento ----------
def test_fechar_com_pendentes_lista_cada_item(exemplos):  # CA09
    ins4 = exemplos.query(Inspecao).filter_by(codigo="INS-004").one()
    e = codigo_de_erro(svc.fechar, exemplos, ins4.id)
    assert e.codigo == "FECHAMENTO_BLOQUEADO" and e.status == 422
    assert len(e.detalhes) == 3
    assert {d["campo"] for d in e.detalhes} == {f"itens.{i.id}" for i in ins4.itens if i.ordem >= 4}


def test_fechar_nc_sem_observacao_bloqueia(exemplos):  # CA10
    insp = nova(exemplos)
    responder(exemplos, insp, {4: "NAO_CONFORME"})
    e = codigo_de_erro(svc.fechar, exemplos, insp.id)
    assert e.codigo == "FECHAMENTO_BLOQUEADO" and len(e.detalhes) == 1
    assert "observação" in e.detalhes[0]["mensagem"]


@pytest.mark.parametrize(
    "situacoes,obs,esperado",
    [
        ({}, None, "APROVADA"),  # CA11
        ({4: "NAO_CONFORME"}, {4: "placa gasta"}, "APROVADA_COM_RESSALVAS"),  # CA12
        ({6: "NAO_CONFORME", 4: "NAO_SE_APLICA"}, {6: "efluente irregular"}, "REPROVADA"),  # CA13
    ],
)
def test_fechar_resultado(exemplos, situacoes, obs, esperado):
    insp = nova(exemplos)
    responder(exemplos, insp, situacoes, obs)
    fechada = svc.fechar(exemplos, insp.id)
    assert fechada.resultado == esperado
    assert fechada.status == "FINALIZADA" and fechada.fechado_em is not None  # CA14
    assert codigo_de_erro(svc.editar, exemplos, insp.id, InspecaoPatch(observacoes="x")).status == 409


def test_fechar_inspecao_aberta_nao_permitido(exemplos):  # P3
    insp = nova(exemplos)
    e = codigo_de_erro(svc.fechar, exemplos, insp.id)
    assert e.codigo == "TRANSICAO_INVALIDA" and e.status == 409


def test_fechar_sem_observacoes_vistoria_permitido(exemplos):  # CA40
    insp = nova(exemplos)
    responder(exemplos, insp, {})
    assert insp.observacoes_vistoria is None
    assert svc.fechar(exemplos, insp.id).status == "FINALIZADA"


def test_codigo_nunca_reutilizado_apos_cancelar(exemplos):  # RN03
    a = nova(exemplos)
    svc.cancelar(exemplos, a.id, "Responsável ausente")
    assert nova(exemplos).codigo == "INS-007"


# ---------- cancelamento ----------
def test_cancelar_aberta_com_motivo(exemplos):  # CA20 (efeito nos indicadores é da S3)
    insp = exemplos.query(Inspecao).filter_by(codigo="INS-005").one()
    c = svc.cancelar(exemplos, insp.id, "  Local inacessível  ")
    assert c.status == "CANCELADA" and c.motivo_cancelamento == "Local inacessível"
    assert c.data_realizacao is None and c.data_agendamento == date(2026, 10, 28)  # RN15


def test_cancelar_exige_motivo(exemplos):
    insp = nova(exemplos)
    assert codigo_de_erro(svc.cancelar, exemplos, insp.id, "  ").codigo == "VALIDACAO_CAMPO"
    exemplos.refresh(insp)
    assert insp.status == "ABERTA"


def test_cancelar_em_andamento_nao_permitido(exemplos):  # P5
    ins4 = exemplos.query(Inspecao).filter_by(codigo="INS-004").one()
    assert codigo_de_erro(svc.cancelar, exemplos, ins4.id, "x").codigo == "TRANSICAO_INVALIDA"


def test_cancelar_finalizada_nao_permitido(exemplos):
    ins1 = exemplos.query(Inspecao).filter_by(codigo="INS-001").one()
    assert codigo_de_erro(svc.cancelar, exemplos, ins1.id, "x").status == 409


# ---------- edição por status (RN14) ----------
def test_editar_agendamento_so_em_aberta(exemplos):  # CA33
    ins4 = exemplos.query(Inspecao).filter_by(codigo="INS-004").one()
    e = codigo_de_erro(svc.editar, exemplos, ins4.id, InspecaoPatch(data_agendamento=date(2026, 10, 21)))
    assert e.codigo == "CAMPO_NAO_EDITAVEL_NO_STATUS"
    ins5 = exemplos.query(Inspecao).filter_by(codigo="INS-005").one()
    svc.editar(exemplos, ins5.id, InspecaoPatch(data_agendamento=date(2026, 10, 22)))
    exemplos.refresh(ins5)
    assert ins5.data_agendamento == date(2026, 10, 22)


def test_editar_realizacao_nao_editavel_em_aberta(exemplos):
    ins5 = exemplos.query(Inspecao).filter_by(codigo="INS-005").one()
    e = codigo_de_erro(svc.editar, exemplos, ins5.id, InspecaoPatch(data_realizacao=date(2026, 10, 23)))
    assert e.codigo == "CAMPO_NAO_EDITAVEL_NO_STATUS"


def test_editar_realizacao_em_andamento_valida_datas(exemplos):
    ins4 = exemplos.query(Inspecao).filter_by(codigo="INS-004").one()
    assert codigo_de_erro(svc.editar, exemplos, ins4.id, InspecaoPatch(data_realizacao=date(2026, 10, 24))).codigo == "DATA_REALIZACAO_FUTURA"
    assert codigo_de_erro(svc.editar, exemplos, ins4.id, InspecaoPatch(data_realizacao=date(2026, 10, 19))).codigo == "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO"
    svc.editar(exemplos, ins4.id, InspecaoPatch(data_realizacao=date(2026, 10, 22)))
    exemplos.refresh(ins4)
    assert ins4.data_realizacao == date(2026, 10, 22)


def test_editar_finalizada_imutavel(exemplos):  # CA14
    ins1 = exemplos.query(Inspecao).filter_by(codigo="INS-001").one()
    e = codigo_de_erro(svc.editar, exemplos, ins1.id, InspecaoPatch(observacoes="x"))
    assert e.codigo == "INSPECAO_IMUTAVEL"


# ---------- observações da vistoria (RN16–RN19) ----------
def test_observacoes_vistoria_grava_sem_mudar_status(exemplos):  # CA35, CA36
    insp = nova(exemplos)
    texto = "x" * 500
    svc.editar(exemplos, insp.id, InspecaoPatch(observacoes_vistoria=texto))
    exemplos.refresh(insp)
    assert insp.observacoes_vistoria == texto and insp.status == "ABERTA"


def test_observacoes_vistoria_limites(exemplos):  # CA37
    insp = nova(exemplos)
    svc.editar(exemplos, insp.id, InspecaoPatch(observacoes_vistoria="a" * 2000))
    e = codigo_de_erro(svc.editar, exemplos, insp.id, InspecaoPatch(observacoes_vistoria="a" * 2001))
    assert e.codigo == "VALIDACAO_CAMPO"
    exemplos.refresh(insp)
    assert len(insp.observacoes_vistoria) == 2000


def test_observacoes_vistoria_so_espacos_vira_nulo(exemplos):  # CA38
    insp = nova(exemplos, observacoes_vistoria="algo")
    svc.editar(exemplos, insp.id, InspecaoPatch(observacoes_vistoria="   \n "))
    exemplos.refresh(insp)
    assert insp.observacoes_vistoria is None


def test_observacoes_vistoria_imutavel_em_finalizada_e_cancelada(exemplos):  # CA39
    ins1 = exemplos.query(Inspecao).filter_by(codigo="INS-001").one()
    assert codigo_de_erro(svc.editar, exemplos, ins1.id, InspecaoPatch(observacoes_vistoria="x")).status == 409
    insp = nova(exemplos)
    svc.cancelar(exemplos, insp.id, "motivo")
    assert codigo_de_erro(svc.editar, exemplos, insp.id, InspecaoPatch(observacoes_vistoria="x")).status == 409


def test_observacoes_vistoria_texto_puro_com_quebras(exemplos):  # CA41 (backend: sem transformação)
    insp = nova(exemplos)
    texto = "<script>alert(1)</script>\nsegunda linha"
    svc.editar(exemplos, insp.id, InspecaoPatch(observacoes_vistoria=texto))
    exemplos.refresh(insp)
    assert insp.observacoes_vistoria == texto


def test_observacoes_vistoria_aceita_em_andamento(exemplos):
    ins4 = exemplos.query(Inspecao).filter_by(codigo="INS-004").one()
    svc.editar(exemplos, ins4.id, InspecaoPatch(observacoes_vistoria="Trecho sul percorrido."))
    exemplos.refresh(ins4)
    assert ins4.observacoes_vistoria == "Trecho sul percorrido." and ins4.status == "EM_ANDAMENTO"


# ---------- seed reproduz resultados esperados ----------
def test_fechamento_dos_exemplos_coerente_com_dominio(exemplos):
    from app.domain.resultado import calcular_resultado

    for insp in exemplos.query(Inspecao).filter(Inspecao.status == "FINALIZADA"):
        assert insp.resultado == calcular_resultado(insp.itens)
