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


# ---------- C1: Local ganha numero_car e nasce a tabela proprietario ----------
ESQUEMA_LOCAL_ANTIGO = """
CREATE TABLE local (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(120) NOT NULL UNIQUE,
    municipio VARCHAR(80) NOT NULL,
    tipo VARCHAR(40) NOT NULL,
    latitude NUMERIC(8, 5) NOT NULL,
    longitude NUMERIC(8, 5) NOT NULL,
    ativo BOOLEAN NOT NULL
)
"""


def test_banco_antigo_ganha_numero_car_e_tabela_proprietario(tmp_path):
    engine = database.criar_engine(f"sqlite:///{(tmp_path / 'local_antigo.db').as_posix()}")
    with engine.begin() as con:
        con.execute(text(ESQUEMA_LOCAL_ANTIGO))
        con.execute(text("INSERT INTO local (nome, municipio, tipo, latitude, longitude, ativo) VALUES ('Local Antigo Fictício', 'M', 'T', -12.5, -55.5, 1)"))
    assert "proprietario" not in inspect(engine).get_table_names()

    database.configurar(engine)
    database.criar_tabelas()

    assert "numero_car" in {c["name"] for c in inspect(engine).get_columns("local")}
    assert "proprietario" in inspect(engine).get_table_names()
    with engine.connect() as con:
        assert tuple(con.execute(text("SELECT nome, numero_car FROM local")).one()) == ("Local Antigo Fictício", None)
    database.criar_tabelas()  # idempotente
    engine.dispose()


def test_local_antigo_pode_receber_car_e_proprietarios(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import criar_app

    monkeypatch.setenv("FOTOS_DIR", str(tmp_path / "fotos"))
    engine = database.criar_engine(f"sqlite:///{(tmp_path / 'local_antigo2.db').as_posix()}")
    with engine.begin() as con:
        con.execute(text(ESQUEMA_LOCAL_ANTIGO))
        con.execute(text("INSERT INTO local (nome, municipio, tipo, latitude, longitude, ativo) VALUES ('Local Antigo Fictício', 'M', 'T', -12.5, -55.5, 1)"))
    database.configurar(engine)
    with TestClient(criar_app()) as c:  # o lifespan migra o banco
        antigo = c.get("/api/v1/locais/1").json()
        assert antigo["numero_car"] is None and antigo["proprietarios"] == []
        r = c.put("/api/v1/locais/1", json={"nome": "Local Antigo Fictício", "municipio": "M", "tipo": "T", "latitude": -12.5,
                                           "longitude": -55.5, "numero_car": "mt-1", "proprietarios": [{"nome": "Dono Fictício", "telefone": "65900000001"}]})
        assert r.status_code == 200 and r.json()["proprietarios"][0]["telefone_formatado"] == "(65) 90000-0001"
    engine.dispose()
