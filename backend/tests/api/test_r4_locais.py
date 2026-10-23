"""R4/E2: endereço do empreendimento e dados do responsável (CPF/CNPJ, correspondência)."""
import json

import pytest
from sqlalchemy import text

BASE = "/api/v1"
CPF, CNPJ = "52998224725", "11222333000181"


@pytest.fixture
def api(client, exemplos):
    return client


def local_json(**kw):
    base = dict(nome="Fazenda Teste Fictícia", municipio="Município Fictício", tipo="Propriedade rural",
                latitude=-12.5, longitude=-55.5)
    base.update(kw)
    return base


def detalhes(r):
    assert r.status_code == 422, r.text
    return {(d["campo"], d["mensagem"]) for d in r.json()["erro"]["detalhes"]}


def test_endereco_do_empreendimento_com_uf_padrao_mt_e_cep_so_digitos(api):
    r = api.post(f"{BASE}/locais", json=local_json(logradouro="  Zona Rural, aos fundos da Fazenda Teste ", cep="78.320-000"))
    assert r.status_code == 201, r.text
    d = r.json()
    assert (d["logradouro"], d["uf"], d["cep"], d["cep_formatado"]) == (
        "Zona Rural, aos fundos da Fazenda Teste", "MT", "78320000", "78.320-000")
    assert d["municipio"] == "Município Fictício"  # o município reaproveita o campo existente


def test_endereco_e_opcional(api):
    d = api.post(f"{BASE}/locais", json=local_json()).json()
    assert (d["logradouro"], d["cep"], d["cep_formatado"]) == (None, None, None)


def test_cep_e_uf_invalidos_do_empreendimento(api):
    r = api.post(f"{BASE}/locais", json=local_json(cep="123", uf="XX"))
    assert detalhes(r) == {("cep", "CEP deve ter 8 dígitos."), ("uf", "UF inválida.")}


def test_responsavel_com_cpf_cnpj_guardado_so_com_digitos(api, engine):
    r = api.post(f"{BASE}/locais", json=local_json(proprietarios=[
        {"nome": "Responsável Fictício", "cpf_cnpj": "529.982.247-25"},
        {"nome": "Empresa Fictícia Ltda.", "cpf_cnpj": "11.222.333/0001-81"},
        {"nome": "Sem documento"},
    ]))
    assert r.status_code == 201, r.text
    p = r.json()["proprietarios"]
    assert [(x["cpf_cnpj"], x["cpf_cnpj_formatado"]) for x in p] == [
        (CPF, "529.982.247-25"), (CNPJ, "11.222.333/0001-81"), (None, None)]
    with engine.connect() as con:
        docs = con.execute(text("SELECT cpf_cnpj FROM proprietario WHERE local_id = :i ORDER BY ordem"), {"i": r.json()["id"]}).scalars().all()
    assert docs == [CPF, CNPJ, None]


def test_cpf_e_cnpj_com_verificador_errado_apontam_a_linha(api):
    r = api.post(f"{BASE}/locais", json=local_json(proprietarios=[
        {"nome": "Ok"}, {"nome": "Ruim", "cpf_cnpj": "529.982.247-24"}, {"nome": "Pior", "cpf_cnpj": "11222333000180"}]))
    assert detalhes(r) == {("proprietarios.1.cpf_cnpj", "CPF inválido."), ("proprietarios.2.cpf_cnpj", "CNPJ inválido.")}


def test_endereco_para_correspondencia_completo(api):
    r = api.post(f"{BASE}/locais", json=local_json(proprietarios=[{
        "nome": "Responsável Fictício", "corr_logradouro": "Rua das Palmeiras", "corr_numero": "123",
        "corr_complemento": "Sala 2", "corr_bairro": "Centro", "corr_municipio": "Cidade Fictícia",
        "corr_uf": "mt", "corr_cep": "78320-010"}]))
    assert r.status_code == 201, r.text
    p = r.json()["proprietarios"][0]
    assert (p["corr_logradouro"], p["corr_numero"], p["corr_complemento"], p["corr_bairro"], p["corr_municipio"],
            p["corr_uf"], p["corr_cep"], p["corr_cep_formatado"]) == (
        "Rua das Palmeiras", "123", "Sala 2", "Centro", "Cidade Fictícia", "MT", "78320010", "78.320-010")


def test_atalho_mesmo_endereco_do_empreendimento_copia_logradouro_municipio_uf_e_cep(api):
    r = api.post(f"{BASE}/locais", json=local_json(
        logradouro="Zona Rural, Gleba Fictícia", cep="78320000", uf="MT",
        proprietarios=[{"nome": "Responsável Fictício", "correspondencia_mesmo_endereco": True,
                        "corr_numero": "S/N", "corr_bairro": "Zona Rural",
                        "corr_logradouro": "ignorado", "corr_cep": "11111111"}]))
    assert r.status_code == 201, r.text
    p = r.json()["proprietarios"][0]
    assert (p["corr_logradouro"], p["corr_municipio"], p["corr_uf"], p["corr_cep"]) == (
        "Zona Rural, Gleba Fictícia", "Município Fictício", "MT", "78320000")
    assert (p["corr_numero"], p["corr_bairro"]) == ("S/N", "Zona Rural")  # número e bairro continuam do usuário


def test_correspondencia_invalida_aponta_cada_campo(api):
    r = api.post(f"{BASE}/locais", json=local_json(proprietarios=[
        {"nome": "X", "corr_cep": "1", "corr_uf": "ZZ", "corr_numero": "n" * 21}]))
    assert detalhes(r) == {
        ("proprietarios.0.corr_cep", "CEP deve ter 8 dígitos."), ("proprietarios.0.corr_uf", "UF inválida."),
        ("proprietarios.0.corr_numero", "Máximo de 20 caracteres.")}


def test_editar_local_atualiza_endereco_e_responsavel(api):
    lid = api.post(f"{BASE}/locais", json=local_json()).json()["id"]
    r = api.put(f"{BASE}/locais/{lid}", json=local_json(
        logradouro="Novo logradouro", cep="78320000", proprietarios=[{"nome": "R", "cpf_cnpj": CPF}]))
    assert r.status_code == 200, r.text
    d = api.get(f"{BASE}/locais/{lid}").json()
    assert (d["logradouro"], d["proprietarios"][0]["cpf_cnpj"]) == ("Novo logradouro", CPF)


def test_copia_do_fechamento_inclui_endereco_cpf_e_correspondencia(api, engine):
    """C2: ao fechar, a cópia leva os campos novos; editar o Local depois não altera a finalizada."""
    lid = api.post(f"{BASE}/locais", json=local_json(logradouro="Logradouro original", cep="78320000", proprietarios=[
        {"nome": "Responsável Fictício", "cpf_cnpj": CPF, "corr_logradouro": "Rua A", "corr_cep": "78320010"}])).json()["id"]
    d = api.post(f"{BASE}/inspecoes", json={"numero_processo": "P", "local_id": lid, "data_agendamento": "2026-10-20",
                                            "objetivo": "x", "equipe": [{"nome": "Analista Fictício"}]}).json()
    for it in d["itens"]:
        api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{it['id']}", json={"situacao": "CONFORME"})
    assert api.post(f"{BASE}/inspecoes/{d['id']}/fechar").status_code == 200
    api.put(f"{BASE}/locais/{lid}", json=local_json(logradouro="Logradouro NOVO", cep="78320099", proprietarios=[]))
    with engine.connect() as con:
        copia = json.loads(con.execute(text("SELECT empreendimento_json FROM inspecao WHERE id = :i"), {"i": d["id"]}).scalar())
    assert (copia["logradouro"], copia["uf"], copia["cep"]) == ("Logradouro original", "MT", "78320000")
    assert (copia["proprietarios"][0]["cpf_cnpj"], copia["proprietarios"][0]["corr_logradouro"],
            copia["proprietarios"][0]["corr_cep"]) == (CPF, "Rua A", "78320010")
    e = api.get(f"{BASE}/inspecoes/{d['id']}").json()["empreendimento"]
    assert (e["logradouro"], e["cep_formatado"], e["proprietarios"][0]["cpf_cnpj_formatado"]) == (
        "Logradouro original", "78.320-000", "529.982.247-25")


def test_exemplos_trazem_endereco_documento_e_correspondencia_ficticios(api):
    locais = api.get(f"{BASE}/locais").json()["dados"]
    fazenda = next(x for x in locais if x["nome"] == "Fazenda Horizonte Azul")
    assert fazenda["logradouro"].startswith("Zona Rural") and fazenda["cep_formatado"] == "78.320-000"
    um, dois = fazenda["proprietarios"]
    assert um["cpf_cnpj"] == CPF and um["corr_logradouro"] == "Rua das Palmeiras"
    assert dois["corr_logradouro"] == fazenda["logradouro"] and dois["corr_cep"] == fazenda["cep"]  # "mesmo endereço"
