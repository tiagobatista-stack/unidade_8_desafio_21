import pytest
from sqlalchemy import text

BASE = "/api/v1"


@pytest.fixture
def api(client, exemplos):
    return client


def local_json(**kw):
    base = dict(nome="Fazenda Teste Fictícia", municipio="Município Fictício", tipo="Propriedade rural",
                latitude=-12.5, longitude=-55.5)
    base.update(kw)
    return base


def erro(r, status, codigo):
    assert r.status_code == status, r.text
    corpo = r.json()["erro"]
    assert corpo["codigo"] == codigo, corpo
    return corpo


def test_criar_com_car_e_proprietarios(api, engine):
    r = api.post(f"{BASE}/locais", json=local_json(
        numero_car="  mt-5107925-abc123  ",
        proprietarios=[{"nome": "  Fulano Fictício ", "telefone": "(65) 90000-0001"},
                       {"nome": "Beltrana Fictícia", "telefone": ""},
                       {"nome": "Sicrano Fictício"}]))
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["numero_car"] == "MT-5107925-ABC123"
    campos = ("nome", "telefone", "telefone_formatado")  # os campos da R4 têm testes próprios
    assert [{k: p[k] for k in campos} for p in d["proprietarios"]] == [
        {"nome": "Fulano Fictício", "telefone": "65900000001", "telefone_formatado": "(65) 90000-0001"},
        {"nome": "Beltrana Fictícia", "telefone": None, "telefone_formatado": None},
        {"nome": "Sicrano Fictício", "telefone": None, "telefone_formatado": None},
    ]
    with engine.connect() as con:  # no banco: só dígitos, em tabela própria
        linhas = con.execute(text("SELECT nome, telefone, ordem FROM proprietario WHERE local_id = :i ORDER BY ordem"), {"i": d["id"]}).all()
    assert [tuple(l) for l in linhas] == [("Fulano Fictício", "65900000001", 0), ("Beltrana Fictícia", None, 1), ("Sicrano Fictício", None, 2)]


def test_payload_antigo_sem_car_nem_proprietarios_continua_valido(api):
    r = api.post(f"{BASE}/locais", json=local_json())
    assert r.status_code == 201
    assert r.json()["numero_car"] is None and r.json()["proprietarios"] == []


@pytest.mark.parametrize("car", ["MT-5107925-X", "mt-123456/2020", "OUTRO FORMATO 99"])
def test_car_de_qualquer_formato_e_aceito(api, car):
    r = api.post(f"{BASE}/locais", json=local_json(numero_car=car))
    assert r.status_code == 201 and r.json()["numero_car"] == car.upper()


def test_car_acima_de_60_rejeitado(api):
    corpo = erro(api.post(f"{BASE}/locais", json=local_json(numero_car="A" * 61)), 422, "VALIDACAO_CAMPO")
    assert corpo["detalhes"][0]["campo"] == "numero_car"


def test_erros_de_proprietarios_apontam_a_linha(api):
    r = api.post(f"{BASE}/locais", json=local_json(proprietarios=[
        {"nome": "Ok Fictício", "telefone": "65900000001"},
        {"nome": "Telefone Curto", "telefone": "9000-0001"},
        {"nome": "   ", "telefone": "(65) 90000-0002"},
        {"nome": "N" * 121},
    ]))
    campos = {d["campo"] for d in erro(r, 422, "VALIDACAO_CAMPO")["detalhes"]}
    assert campos == {"proprietarios.1.telefone", "proprietarios.2.nome", "proprietarios.3.nome"}


def test_limite_de_20_proprietarios(api):
    vinte = [{"nome": f"Proprietário Fictício {i}"} for i in range(20)]
    assert api.post(f"{BASE}/locais", json=local_json(nome="Vinte", proprietarios=vinte)).status_code == 201
    erro(api.post(f"{BASE}/locais", json=local_json(nome="Vinte e um", proprietarios=vinte + [{"nome": "Extra"}])), 422, "VALIDACAO_CAMPO")


def test_proprietario_sem_nome_no_json_e_422(api):
    erro(api.post(f"{BASE}/locais", json=local_json(proprietarios=[{"telefone": "65900000001"}])), 422, "VALIDACAO_CAMPO")


def test_erro_em_proprietario_nao_cria_o_local(api):
    antes = api.get(f"{BASE}/locais").json()["total"]
    api.post(f"{BASE}/locais", json=local_json(nome="Nao Deve Existir", proprietarios=[{"nome": "X", "telefone": "1"}]))
    depois = api.get(f"{BASE}/locais").json()
    assert depois["total"] == antes and all(l["nome"] != "Nao Deve Existir" for l in depois["dados"])


# ---------- PUT: a lista enviada substitui a anterior ----------
def criar_com_dois(api):
    return api.post(f"{BASE}/locais", json=local_json(proprietarios=[
        {"nome": "Primeiro Fictício", "telefone": "65900000001"}, {"nome": "Segundo Fictício", "telefone": "65900000002"}])).json()


def test_put_troca_remove_e_reordena(api):
    d = criar_com_dois(api)
    r = api.put(f"{BASE}/locais/{d['id']}", json=local_json(numero_car="mt-9", proprietarios=[
        {"nome": "Segundo Fictício", "telefone": "(65) 90000-0009"}, {"nome": "Terceiro Fictício"}]))
    assert r.status_code == 200
    assert r.json()["numero_car"] == "MT-9"
    assert [(p["nome"], p["telefone_formatado"]) for p in r.json()["proprietarios"]] == [
        ("Segundo Fictício", "(65) 90000-0009"), ("Terceiro Fictício", None)]
    assert api.get(f"{BASE}/locais/{d['id']}").json()["proprietarios"][0]["nome"] == "Segundo Fictício"


def test_put_com_lista_vazia_remove_todos_e_car_vazio_limpa(api):
    d = criar_com_dois(api)
    api.put(f"{BASE}/locais/{d['id']}", json=local_json(numero_car="MT-1"))
    r = api.put(f"{BASE}/locais/{d['id']}", json=local_json(numero_car="   "))
    assert r.json()["proprietarios"] == [] and r.json()["numero_car"] is None


def test_put_invalido_nao_altera_nada(api):
    d = criar_com_dois(api)
    erro(api.put(f"{BASE}/locais/{d['id']}", json=local_json(proprietarios=[{"nome": "Novo", "telefone": "123"}])), 422, "VALIDACAO_CAMPO")
    assert [p["nome"] for p in api.get(f"{BASE}/locais/{d['id']}").json()["proprietarios"]] == ["Primeiro Fictício", "Segundo Fictício"]


def test_put_nao_duplica_proprietarios_ao_repetir(api, engine):
    d = criar_com_dois(api)
    for _ in range(3):
        api.put(f"{BASE}/locais/{d['id']}", json=local_json(proprietarios=[{"nome": "Primeiro Fictício"}, {"nome": "Segundo Fictício"}]))
    with engine.connect() as con:
        assert con.execute(text("SELECT COUNT(*) FROM proprietario WHERE local_id = :i"), {"i": d["id"]}).scalar() == 2


def test_listagem_e_detalhe_da_inspecao_trazem_os_dados(api):
    lista = api.get(f"{BASE}/locais").json()["dados"]
    fazenda = next(l for l in lista if l["nome"] == "Fazenda Horizonte Azul")
    assert fazenda["numero_car"].startswith("MT-5107925-") and len(fazenda["proprietarios"]) == 2
    insp = api.get(f"{BASE}/inspecoes", params={"tamanho": 100}).json()["dados"]
    id_ins1 = next(i["id"] for i in insp if i["codigo"] == "INS-001")
    local = api.get(f"{BASE}/inspecoes/{id_ins1}").json()["local"]
    assert local["numero_car"] == fazenda["numero_car"]
    assert local["proprietarios"][0]["telefone_formatado"] == "(65) 90000-0001"


# ---------- seed 100% fictício (LGPD) ----------
def test_seed_so_tem_dados_ficticios(api):
    for l in api.get(f"{BASE}/locais").json()["dados"]:
        if l["numero_car"]:
            assert l["numero_car"].startswith("MT-5107925-0000000000")
        for p in l["proprietarios"]:
            assert "Fictíci" in p["nome"] or p["nome"].endswith("Ltda.") and "Fictícia" in p["nome"]
            if p["telefone"]:
                assert p["telefone"].startswith("659000000")  # (65) 90000-000N
