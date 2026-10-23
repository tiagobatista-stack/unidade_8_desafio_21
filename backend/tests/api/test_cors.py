from fastapi.testclient import TestClient

from app.main import criar_app

ORIGEM = "https://unidade-8-desafio-21.vercel.app"


def preflight(c, origem):
    return c.options(
        "/api/v1/inspecoes",
        headers={"Origin": origem, "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "content-type", "Access-Control-Request-Private-Network": "true"},
    )


def test_sem_configuracao_nao_ha_cors(engine, monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    with TestClient(criar_app()) as c:
        r = c.get("/api/v1/health", headers={"Origin": ORIGEM})
        assert "access-control-allow-origin" not in r.headers


def test_origem_listada_e_liberada_e_outras_nao(engine, monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", f"{ORIGEM}/, http://localhost:5173")
    with TestClient(criar_app()) as c:
        ok = preflight(c, ORIGEM)
        assert ok.status_code == 200 and ok.headers["access-control-allow-origin"] == ORIGEM
        assert ok.headers["access-control-allow-private-network"] == "true"
        assert "access-control-allow-origin" not in preflight(c, "https://site-qualquer.example").headers
        r = c.get("/api/v1/health", headers={"Origin": ORIGEM})
        assert r.headers["access-control-allow-origin"] == ORIGEM
