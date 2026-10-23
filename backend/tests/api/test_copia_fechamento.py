import json

import pytest
from sqlalchemy import text

BASE = "/api/v1"


@pytest.fixture
def api(client, exemplos):
    return client


def local_atual(api, local_id=1):
    return api.get(f"{BASE}/locais/{local_id}").json()


def editar_local(api, local_id=1, **mudancas):
    atual = local_atual(api, local_id)
    corpo = {k: atual[k] for k in ("nome", "municipio", "tipo", "latitude", "longitude", "numero_car")}
    corpo["proprietarios"] = [{"nome": p["nome"], "telefone": p["telefone"]} for p in atual["proprietarios"]]
    corpo.update(mudancas)
    r = api.put(f"{BASE}/locais/{local_id}", json=corpo)
    assert r.status_code == 200, r.text
    return r.json()


def nova_em_andamento(api, local_id=1):
    r = api.post(f"{BASE}/inspecoes", json={"numero_processo": "SEMA-PRO-2026/12345", "local_id": local_id,
                                            "data_agendamento": "2026-10-20", "objetivo": "x", "equipe": [{"nome": "Analista Fictício"}]})
    d = r.json()
    for it in d["itens"]:
        assert api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{it['id']}", json={"situacao": "CONFORME"}).status_code == 200
    return d["id"]


def detalhe(api, inspecao_id):
    return api.get(f"{BASE}/inspecoes/{inspecao_id}").json()


def trocar_dados_do_local(api, local_id=1):
    return editar_local(
        api, local_id, nome="Nome Trocado Fictício", municipio="Município Trocado", tipo="Tipo Trocado",
        latitude=-13.0, longitude=-56.0, numero_car="mt-9999999-trocado",
        proprietarios=[{"nome": "Novo Dono Fictício", "telefone": "(65) 90000-0099"}])


def test_fechar_grava_copia_e_editar_o_local_depois_nao_muda_a_finalizada(api):
    id_insp = nova_em_andamento(api)
    original = local_atual(api)
    assert api.post(f"{BASE}/inspecoes/{id_insp}/fechar").status_code == 200

    antes = detalhe(api, id_insp)["empreendimento"]
    assert antes["nome"] == original["nome"] and antes["numero_car"] == original["numero_car"]
    assert [p["nome"] for p in antes["proprietarios"]] == [p["nome"] for p in original["proprietarios"]]

    trocar_dados_do_local(api)  # troca proprietário, CAR, nome, município, tipo e coordenadas
    depois = detalhe(api, id_insp)
    assert depois["empreendimento"] == antes  # a finalizada não mudou
    assert depois["local"]["nome"] == "Nome Trocado Fictício"  # o cadastro do Local sim mudou
    assert local_atual(api)["proprietarios"][0]["nome"] == "Novo Dono Fictício"


def test_cada_campo_da_copia_e_preservado(api):
    id_insp = nova_em_andamento(api)
    original = local_atual(api)
    api.post(f"{BASE}/inspecoes/{id_insp}/fechar")
    trocar_dados_do_local(api)
    emp = detalhe(api, id_insp)["empreendimento"]
    assert (emp["nome"], emp["municipio"], emp["tipo"]) == (original["nome"], original["municipio"], original["tipo"])
    assert (emp["latitude"], emp["longitude"]) == (original["latitude"], original["longitude"])
    assert emp["numero_car"] == original["numero_car"]
    assert [(p["nome"], p["telefone"], p["telefone_formatado"]) for p in emp["proprietarios"]] == [
        (p["nome"], p["telefone"], p["telefone_formatado"]) for p in original["proprietarios"]]


def test_antes_do_fechamento_usa_os_dados_atuais_do_local(api):
    id_insp = nova_em_andamento(api)
    trocar_dados_do_local(api)
    emp = detalhe(api, id_insp)["empreendimento"]  # ainda Em andamento
    assert emp["nome"] == "Nome Trocado Fictício" and emp["numero_car"] == "MT-9999999-TROCADO"
    assert emp["proprietarios"][0]["telefone_formatado"] == "(65) 90000-0099"


def test_aberta_e_cancelada_tambem_usam_dados_atuais(api):
    r = api.post(f"{BASE}/inspecoes", json={"numero_processo": "P", "local_id": 1, "data_agendamento": "2026-10-20", "objetivo": "x"})
    aberta = r.json()["id"]
    cancelada = api.post(f"{BASE}/inspecoes", json={"numero_processo": "P", "local_id": 1, "data_agendamento": "2026-10-20", "objetivo": "x"}).json()["id"]
    api.post(f"{BASE}/inspecoes/{cancelada}/cancelar", json={"motivo": "teste"})
    trocar_dados_do_local(api)
    assert detalhe(api, aberta)["empreendimento"]["nome"] == "Nome Trocado Fictício"
    assert detalhe(api, cancelada)["empreendimento"]["nome"] == "Nome Trocado Fictício"


def test_outra_inspecao_aberta_do_mesmo_local_acompanha_o_cadastro(api):
    finalizada = nova_em_andamento(api)
    api.post(f"{BASE}/inspecoes/{finalizada}/fechar")
    aberta = api.post(f"{BASE}/inspecoes", json={"numero_processo": "P", "local_id": 1, "data_agendamento": "2026-10-20", "objetivo": "x"}).json()["id"]
    trocar_dados_do_local(api)
    assert detalhe(api, finalizada)["empreendimento"]["nome"] != "Nome Trocado Fictício"
    assert detalhe(api, aberta)["empreendimento"]["nome"] == "Nome Trocado Fictício"


def test_copia_fica_gravada_no_banco_como_json_completo(api, engine):
    id_insp = nova_em_andamento(api)
    api.post(f"{BASE}/inspecoes/{id_insp}/fechar")
    with engine.connect() as con:
        bruto = con.execute(text("SELECT empreendimento_json FROM inspecao WHERE id = :i"), {"i": id_insp}).scalar()
    dados = json.loads(bruto)
    assert set(dados) == {"nome", "municipio", "tipo", "latitude", "longitude", "numero_car", "logradouro", "uf", "cep", "proprietarios"}
    assert all({"nome", "telefone", "cpf_cnpj", "corr_cep"} <= set(p) for p in dados["proprietarios"])
    assert dados["proprietarios"][0]["telefone"] == "65900000001"  # só dígitos


def test_mudar_o_local_da_inspecao_nao_e_possivel_depois_de_finalizada(api):
    id_insp = nova_em_andamento(api)
    api.post(f"{BASE}/inspecoes/{id_insp}/fechar")
    r = api.patch(f"{BASE}/inspecoes/{id_insp}", json={"local_id": 2})
    assert r.status_code == 409 and r.json()["erro"]["codigo"] == "INSPECAO_IMUTAVEL"


def test_seed_ja_traz_a_copia_das_finalizadas(api, engine):
    with engine.connect() as con:
        linhas = con.execute(text("SELECT codigo, status, empreendimento_json FROM inspecao ORDER BY id")).all()
    por_codigo = {l[0]: (l[1], l[2]) for l in linhas}
    for codigo in ("INS-001", "INS-002", "INS-003"):
        assert por_codigo[codigo][0] == "FINALIZADA" and por_codigo[codigo][1]
    assert por_codigo["INS-004"][1] is None and por_codigo["INS-005"][1] is None  # só ao fechar


def test_falha_ao_copiar_desfaz_o_fechamento(api, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import criar_app
    from app.services import empreendimento_service

    id_insp = nova_em_andamento(api)

    def falha(_):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(empreendimento_service, "copiar_no_fechamento", falha)
    with TestClient(criar_app(), raise_server_exceptions=False) as c:
        assert c.post(f"{BASE}/inspecoes/{id_insp}/fechar").status_code == 500
        d = c.get(f"{BASE}/inspecoes/{id_insp}").json()
    assert d["status"] == "EM_ANDAMENTO" and d["resultado"] is None and d["fechado_em"] is None  # nada pela metade
