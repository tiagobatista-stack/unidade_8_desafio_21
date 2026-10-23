from sqlalchemy import inspect, text

from app import database

# Esquema da tabela `inspecao` antes de existir numero_processo (banco criado por versão anterior).
ESQUEMA_ANTIGO = """
CREATE TABLE inspecao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    local_id INTEGER NOT NULL,
    objetivo VARCHAR(200) NOT NULL,
    observacoes TEXT,
    observacoes_vistoria TEXT,
    data_agendamento DATE NOT NULL,
    data_realizacao DATE,
    status VARCHAR(20) NOT NULL,
    resultado VARCHAR(30),
    motivo_cancelamento VARCHAR(300),
    criado_em DATETIME NOT NULL,
    atualizado_em DATETIME NOT NULL,
    fechado_em DATETIME
)
"""


def colunas(engine):
    return {c["name"] for c in inspect(engine).get_columns("inspecao")}


def test_banco_antigo_ganha_a_coluna_sem_perder_dados(tmp_path):
    url = f"sqlite:///{(tmp_path / 'antigo.db').as_posix()}"
    engine = database.criar_engine(url)
    with engine.begin() as con:
        con.execute(text(ESQUEMA_ANTIGO))
        con.execute(text(
            "INSERT INTO inspecao (codigo, local_id, objetivo, data_agendamento, status, criado_em, atualizado_em) "
            "VALUES ('INS-001', 1, 'Vistoria antiga', '2026-10-01', 'ABERTA', '2026-10-01 08:00:00', '2026-10-01 08:00:00')"
        ))
    assert "numero_processo" not in colunas(engine)

    database.configurar(engine)
    database.criar_tabelas()

    assert "numero_processo" in colunas(engine)
    with engine.connect() as con:
        linha = con.execute(text("SELECT codigo, objetivo, numero_processo FROM inspecao")).one()
    assert tuple(linha) == ("INS-001", "Vistoria antiga", None)  # dado preservado, número ainda nulo
    engine.dispose()


def test_migracao_e_idempotente(tmp_path):
    url = f"sqlite:///{(tmp_path / 'novo.db').as_posix()}"
    engine = database.criar_engine(url)
    database.configurar(engine)
    database.criar_tabelas()
    database.criar_tabelas()  # segunda subida não falha nem duplica
    assert "numero_processo" in colunas(engine)
    engine.dispose()


def test_inspecao_antiga_sem_numero_aparece_e_pode_ser_corrigida(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import criar_app

    monkeypatch.setenv("FOTOS_DIR", str(tmp_path / "fotos"))
    engine = database.criar_engine(f"sqlite:///{(tmp_path / 'antigo2.db').as_posix()}")
    with engine.begin() as con:
        con.execute(text(ESQUEMA_ANTIGO))
    database.configurar(engine)
    database.criar_tabelas()  # cria o restante das tabelas e acrescenta a coluna
    with engine.begin() as con:
        con.execute(text(
            "INSERT INTO local (nome, municipio, tipo, latitude, longitude, ativo) VALUES ('L', 'M', 'T', -12.5, -55.5, 1)"))
        con.execute(text(
            "INSERT INTO inspecao (codigo, local_id, objetivo, data_agendamento, status, criado_em, atualizado_em) "
            "VALUES ('INS-001', 1, 'Antiga', '2026-10-20', 'ABERTA', '2026-10-01 08:00:00', '2026-10-01 08:00:00')"))
    with TestClient(criar_app()) as c:
        lista = c.get("/api/v1/inspecoes").json()["dados"]
        assert lista[0]["numero_processo"] is None
        r = c.patch(f"/api/v1/inspecoes/{lista[0]['id']}", json={"numero_processo": "SEMA-PRO-2026/12345"})
        assert r.status_code == 200 and r.json()["numero_processo"] == "SEMA-PRO-2026/12345"
        assert c.get(f"/api/v1/exportacao/inspecoes.csv").status_code == 200  # CSV tolera número nulo
    engine.dispose()
