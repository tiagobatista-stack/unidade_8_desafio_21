BASE = "/api/v1"


def test_banco_novo_ja_tem_modelo_e_cria_inspecao_com_6_itens(client):
    local = client.post(
        f"{BASE}/locais",
        json=dict(nome="Local de teste", municipio="M", tipo="T", latitude=-12.5, longitude=-55.5),
    ).json()
    r = client.post(
        f"{BASE}/inspecoes",
        json={"local_id": local["id"], "data_agendamento": "2026-10-20", "objetivo": "Teste"},
    )
    assert r.status_code == 201
    itens = r.json()["itens"]
    assert len(itens) == 6 and sum(1 for i in itens if i["critico"]) == 3
    assert r.json()["codigo"] == "INS-001"


def test_garantir_modelo_e_idempotente(db):
    from app.models import ModeloItem
    from app.seed.modelo import garantir_modelo

    garantir_modelo(db)
    garantir_modelo(db)
    assert db.query(ModeloItem).count() == 6


def test_acentos_fazem_ida_e_volta_em_utf8(client):
    corpo = '{"nome":"Fictício Ipê","municipio":"Município","tipo":"T","latitude":-12.5,"longitude":-55.5}'
    r = client.post(f"{BASE}/locais", content=corpo.encode("utf-8"), headers={"content-type": "application/json"})
    assert r.status_code == 201
    assert client.get(f"{BASE}/locais/{r.json()['id']}").json()["nome"] == "Fictício Ipê"
