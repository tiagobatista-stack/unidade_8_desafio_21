from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import clock
from tests.fixtures import imagens

BASE = "/api/v1"


@pytest.fixture
def api(client, exemplos):
    return client


def nova(api, local_id=1, agendamento="2026-10-20"):
    r = api.post(f"{BASE}/inspecoes", json={"numero_processo": "SEMA-PRO-2026/12345", "local_id": local_id,
                                            "data_agendamento": agendamento, "objetivo": "Objetivo de teste", "equipe": [{"nome": "Analista Fictício"}]})
    assert r.status_code == 201, r.text
    return r.json()


def responder(api, d, situacoes=None, obs=None):
    situacoes, obs = situacoes or {}, obs or {}
    for it in d["itens"]:
        corpo = {"situacao": situacoes.get(it["ordem"], "CONFORME")}
        if it["ordem"] in obs:
            corpo["observacao"] = obs[it["ordem"]]
        assert api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{it['id']}", json=corpo).status_code == 200


def finalizada(api, situacoes=None, obs=None, local_id=1):
    d = nova(api, local_id)
    responder(api, d, situacoes, obs)
    r = api.post(f"{BASE}/inspecoes/{d['id']}/fechar")
    assert r.status_code == 200, r.text
    return r.json()


def relatorio(api, inspecao_id):
    r = api.get(f"{BASE}/inspecoes/{inspecao_id}/relatorio")
    assert r.status_code == 200, r.text
    return r.json()


# ---------- numeração ----------
def test_seed_ja_vem_numerado_na_ordem_do_fechamento(api, engine):
    with engine.connect() as con:
        numeros = dict(con.execute(text("SELECT codigo, numero_relatorio FROM inspecao")).all())
        ultimo = con.execute(text("SELECT ultimo FROM contador_relatorio WHERE ano = 2026")).scalar()
    assert numeros["INS-001"] == "0001/2026" and numeros["INS-002"] == "0002/2026" and numeros["INS-003"] == "0003/2026"
    assert numeros["INS-004"] is None and numeros["INS-005"] is None  # só ao fechar
    assert ultimo == 3


def test_numeros_sequenciais_e_sem_repeticao(api):
    a, b, c = finalizada(api), finalizada(api), finalizada(api)
    assert [x["numero_relatorio"] for x in (a, b, c)] == ["0004/2026", "0005/2026", "0006/2026"]
    assert len({a["numero_relatorio"], b["numero_relatorio"], c["numero_relatorio"]}) == 3


def test_so_a_inspecao_finalizada_tem_numero(api):
    d = nova(api)
    assert d["numero_relatorio"] is None
    responder(api, d)
    assert api.get(f"{BASE}/inspecoes/{d['id']}").json()["numero_relatorio"] is None  # em andamento
    assert api.post(f"{BASE}/inspecoes/{d['id']}/fechar").json()["numero_relatorio"] == "0004/2026"


def test_cancelar_ou_fechamento_bloqueado_nao_consomem_numero(api):
    cancelada = nova(api)
    api.post(f"{BASE}/inspecoes/{cancelada['id']}/cancelar", json={"motivo": "teste"})
    pendente = nova(api)
    api.patch(f"{BASE}/inspecoes/{pendente['id']}/itens/{pendente['itens'][0]['id']}", json={"situacao": "CONFORME"})
    assert api.post(f"{BASE}/inspecoes/{pendente['id']}/fechar").status_code == 422  # itens pendentes
    assert api.post(f"{BASE}/inspecoes/{nova(api)['id']}/fechar").status_code == 409  # aberta
    assert finalizada(api)["numero_relatorio"] == "0004/2026"  # nenhum buraco na sequência


def test_virada_de_ano_reinicia_a_sequencia_e_nao_reutiliza(api):
    clock.fixar_hoje(date(2026, 12, 31))
    antes = finalizada(api)
    clock.fixar_hoje(date(2027, 1, 1))
    depois = finalizada(api)
    outro = finalizada(api)
    clock.fixar_hoje(date(2026, 12, 31))  # voltando no relógio, 2026 continua de onde parou
    volta = finalizada(api)
    assert antes["numero_relatorio"] == "0004/2026"
    assert (depois["numero_relatorio"], outro["numero_relatorio"]) == ("0001/2027", "0002/2027")
    assert volta["numero_relatorio"] == "0005/2026"


def test_indice_unico_impede_numero_repetido(api, engine):
    a, b = finalizada(api), finalizada(api)
    with engine.begin() as con, pytest.raises(IntegrityError):
        con.execute(text("UPDATE inspecao SET numero_relatorio = :n WHERE id = :i"), {"n": a["numero_relatorio"], "i": b["id"]})


def test_numero_aparece_no_detalhe_da_finalizada(api):
    d = finalizada(api)
    assert api.get(f"{BASE}/inspecoes/{d['id']}").json()["numero_relatorio"] == d["numero_relatorio"]


# ---------- estrutura do relatório finalizado ----------
def test_relatorio_finalizado_traz_as_seis_secoes_na_ordem(api):
    d = finalizada(api)
    r = relatorio(api, d["id"])
    assert r["previa"] is False and r["marca_dagua"] is None
    assert r["numero_relatorio"] == "0004/2026" and r["titulo"] == "Relatório de Vistoria nº 0004/2026"
    assert list(r)[4:] == ["identificacao", "empreendimento", "objetivo", "checklist", "fotos", "conclusao"]  # ordem das seções
    ident = r["identificacao"]
    assert (ident["codigo"], ident["numero_processo"], ident["status"], ident["resultado"]) == ("INS-006", "SEMA-PRO-2026/12345", "FINALIZADA", "APROVADA")
    assert ident["data_agendamento"] == "2026-10-20" and ident["data_realizacao"] == "2026-10-23" and ident["fechado_em"].startswith("2026-10-23T")
    assert r["objetivo"]["objetivo"] == "Objetivo de teste"
    assert r["empreendimento"]["nome"] == "Fazenda Horizonte Azul" and r["empreendimento"]["numero_car"].startswith("MT-5107925-")


def test_checklist_numerado_com_totais_e_criticos_destacados(api):
    d = finalizada(api, {2: "NAO_CONFORME", 4: "NAO_CONFORME", 5: "NAO_SE_APLICA"}, {2: "crítico ruim", 4: "placa gasta"})
    c = relatorio(api, d["id"])["checklist"]
    assert [i["numero"] for i in c["itens"]] == [1, 2, 3, 4, 5, 6]
    assert c["totais"] == {"total": 6, "respondidos": 6, "conformes": 3, "nao_conformes": 2, "nao_aplicaveis": 1, "nao_respondidos": 0}
    destaque = {i["numero"]: i["critico_nao_conforme"] for i in c["itens"]}
    assert destaque == {1: False, 2: True, 3: False, 4: False, 5: False, 6: False}  # só o crítico NC (item 2); item 4 NC não é crítico
    item2 = c["itens"][1]
    assert item2["critico"] is True and item2["observacao"] == "crítico ruim"


@pytest.mark.parametrize("situacoes,obs,resultado,regra", [
    ({}, None, "APROVADA", "Nenhum item não conforme"),
    ({4: "NAO_CONFORME"}, {4: "x"}, "APROVADA_COM_RESSALVAS", "Nenhum item crítico não conforme; 1 item não conforme"),
    ({1: "NAO_CONFORME", 6: "NAO_CONFORME"}, {1: "x", 6: "y"}, "REPROVADA", "2 itens críticos não conformes"),
    ({6: "NAO_CONFORME", 4: "NAO_CONFORME"}, {6: "x", 4: "y"}, "REPROVADA", "1 item crítico não conforme"),
])
def test_conclusao_traz_o_resultado_e_a_regra(api, situacoes, obs, resultado, regra):
    d = finalizada(api, situacoes, obs)
    c = relatorio(api, d["id"])["conclusao"]
    assert c == {"resultado": resultado, "regra": regra}


def test_fotos_numeradas_com_original_e_item_vinculado(api):
    d = nova(api)
    responder(api, d)
    item4 = next(i for i in d["itens"] if i["ordem"] == 4)

    def enviar(arquivo, anotacao, **extra):
        r = api.post(f"{BASE}/inspecoes/{d['id']}/fotos", files={"arquivo": ("f.jpg", arquivo, "image/jpeg")},
                     data={"anotacao": anotacao, **{k: str(v) for k, v in extra.items()}})
        assert r.status_code == 201, r.text
        return r.json()

    f1 = enviar(imagens.jpeg(1), "Primeira anotação", legenda="Legenda um", item_id=item4["id"], data_captura="2026-10-22T09:30:00")
    f2 = enviar(imagens.jpeg(2), "Segunda anotação")
    api.post(f"{BASE}/inspecoes/{d['id']}/fechar")
    fotos = relatorio(api, d["id"])["fotos"]
    assert [f["numero"] for f in fotos] == [1, 2]
    assert fotos[0]["url_original"] == f1["url_original"] and "versao=original" in fotos[0]["url_original"]  # original, não miniatura
    assert (fotos[0]["legenda"], fotos[0]["anotacao"]) == ("Legenda um", "Primeira anotação")
    assert (fotos[0]["item_numero"], fotos[0]["item_descricao"]) == (4, item4["descricao"])
    assert fotos[0]["data_captura"] == "2026-10-22T09:30:00"
    assert (fotos[1]["item_numero"], fotos[1]["item_descricao"], fotos[1]["legenda"], fotos[1]["data_captura"]) == (None, None, None, None)
    assert api.get(fotos[1]["url_original"]).status_code == 200 and fotos[1]["url_original"] == f2["url_original"]


def test_relatorio_sem_fotos_tem_lista_vazia(api):
    assert relatorio(api, finalizada(api)["id"])["fotos"] == []


def test_relatorio_de_inspecao_inexistente_404(api):
    r = api.get(f"{BASE}/inspecoes/999/relatorio")
    assert r.status_code == 404 and r.json()["erro"]["codigo"] == "NAO_ENCONTRADO"


# ---------- prévia ----------
def test_previa_em_andamento_sem_numero_e_com_marca(api):
    d = nova(api)
    api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{d['itens'][0]['id']}", json={"situacao": "CONFORME"})
    r = relatorio(api, d["id"])
    assert r["previa"] is True and r["marca_dagua"] == "PRÉVIA, NÃO FINALIZADO"
    assert r["numero_relatorio"] is None and r["titulo"] == "Relatório de Vistoria (sem número)"
    assert r["conclusao"]["resultado"] is None and "5 itens não respondidos" in r["conclusao"]["regra"]
    assert r["identificacao"]["fechado_em"] is None


def test_previa_aberta_e_cancelada(api):
    aberta = relatorio(api, nova(api)["id"])
    assert aberta["previa"] and aberta["marca_dagua"] == "PRÉVIA, NÃO FINALIZADO" and aberta["numero_relatorio"] is None
    c = nova(api)
    api.post(f"{BASE}/inspecoes/{c['id']}/cancelar", json={"motivo": "teste"})
    cancelada = relatorio(api, c["id"])
    assert cancelada["previa"] and cancelada["marca_dagua"] == "CANCELADA, NÃO FINALIZADO" and cancelada["numero_relatorio"] is None


def test_gerar_a_previa_nao_consome_numero(api):
    d = nova(api)
    responder(api, d)
    for _ in range(3):
        relatorio(api, d["id"])
    assert api.post(f"{BASE}/inspecoes/{d['id']}/fechar").json()["numero_relatorio"] == "0004/2026"


# ---------- dados do empreendimento no relatório ----------
def editar_local(api, **mudancas):
    atual = api.get(f"{BASE}/locais/1").json()
    corpo = {k: atual[k] for k in ("nome", "municipio", "tipo", "latitude", "longitude", "numero_car")}
    corpo["proprietarios"] = [{"nome": p["nome"], "telefone": p["telefone"]} for p in atual["proprietarios"]]
    corpo.update(mudancas)
    assert api.put(f"{BASE}/locais/1", json=corpo).status_code == 200


def test_relatorio_finalizado_usa_a_copia_e_a_previa_usa_os_dados_atuais(api):
    d = finalizada(api)
    previa = nova(api)
    responder(api, previa)
    editar_local(api, nome="Nome Alterado Fictício", numero_car="mt-0-alterado", proprietarios=[{"nome": "Dono Alterado Fictício"}])
    fin = relatorio(api, d["id"])["empreendimento"]
    assert fin["nome"] == "Fazenda Horizonte Azul" and fin["numero_car"].startswith("MT-5107925-")
    assert fin["proprietarios"][0]["nome"] == "Proprietário Fictício Um"
    atual = relatorio(api, previa["id"])["empreendimento"]
    assert atual["nome"] == "Nome Alterado Fictício" and atual["numero_car"] == "MT-0-ALTERADO"
    assert [p["nome"] for p in atual["proprietarios"]] == ["Dono Alterado Fictício"]


def test_car_vazio_chega_como_nulo_para_a_tela_mostrar_nao_informado(api):
    d = finalizada(api, local_id=2)  # a serraria do exemplo não tem CAR nem proprietários listados com CAR
    emp = relatorio(api, d["id"])["empreendimento"]
    assert emp["numero_car"] is None
