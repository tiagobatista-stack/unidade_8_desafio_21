def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_rota_inexistente_segue_contrato_de_erro(client):
    r = client.get("/api/v1/nao-existe")
    assert r.status_code == 404
    corpo = r.json()["erro"]
    assert corpo["codigo"] == "NAO_ENCONTRADO"
    assert corpo["detalhes"] == []
