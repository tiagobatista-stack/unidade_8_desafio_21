"""R4/E7: banco criado antes da rodada ganha as colunas e tabelas novas sem perder dados, e o legado abre."""
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app import clock, database
from app.main import criar_app

ANTIGO = [
    """CREATE TABLE local (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome VARCHAR(120) NOT NULL UNIQUE, municipio VARCHAR(80) NOT NULL,
        tipo VARCHAR(40) NOT NULL, latitude NUMERIC(8,5) NOT NULL, longitude NUMERIC(8,5) NOT NULL,
        ativo BOOLEAN NOT NULL, numero_car VARCHAR(60))""",
    """CREATE TABLE proprietario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, local_id INTEGER NOT NULL, nome VARCHAR(120) NOT NULL,
        telefone VARCHAR(11), ordem INTEGER NOT NULL)""",
    """CREATE TABLE inspecao (
        id INTEGER PRIMARY KEY AUTOINCREMENT, codigo VARCHAR(20) NOT NULL UNIQUE, numero_processo VARCHAR(60),
        empreendimento_json TEXT, numero_relatorio VARCHAR(20), local_id INTEGER NOT NULL,
        objetivo VARCHAR(200) NOT NULL, observacoes TEXT, observacoes_vistoria TEXT,
        data_agendamento DATE NOT NULL, data_realizacao DATE, status VARCHAR(20) NOT NULL,
        resultado VARCHAR(30), motivo_cancelamento VARCHAR(300), criado_em DATETIME NOT NULL,
        atualizado_em DATETIME NOT NULL, fechado_em DATETIME)""",
    "INSERT INTO local (id, nome, municipio, tipo, latitude, longitude, ativo) "
    "VALUES (1, 'Fazenda Antiga Fictícia', 'Município Fictício', 'Propriedade rural', -12.5, -55.5, 1)",
    "INSERT INTO proprietario (local_id, nome, telefone, ordem) VALUES (1, 'Responsável Antigo Fictício', '65900000001', 0)",
    "INSERT INTO inspecao (codigo, numero_processo, local_id, objetivo, data_agendamento, data_realizacao, status, resultado, "
    "criado_em, atualizado_em, fechado_em) VALUES ('INS-001', 'P-1', 1, 'Vistoria antiga', '2026-10-01', '2026-10-01', "
    "'FINALIZADA', 'APROVADA', '2026-10-01 08:00:00', '2026-10-01 17:00:00', '2026-10-01 17:00:00')",
]
NOVAS = {
    "inspecao": {"interessado_orgao", "interessado_unidade", "interessado_comarca", "interessado_requerente",
                 "assunto_tipo", "assunto_outro", "providencias_texto", "numero_relatorio_sema"},
    "local": {"logradouro", "uf", "cep"},
    "proprietario": {"cpf_cnpj", "corr_logradouro", "corr_numero", "corr_complemento", "corr_bairro", "corr_municipio",
                     "corr_uf", "corr_cep"},
}


def banco_antigo(tmp_path):
    engine = database.criar_engine(f"sqlite:///{(tmp_path / 'antigo_r3.db').as_posix()}")
    with engine.begin() as con:
        for ddl in ANTIGO:
            con.execute(text(ddl))
    return engine


def cols(engine, tabela):
    return {c["name"] for c in inspect(engine).get_columns(tabela)}


def test_banco_anterior_a_r4_ganha_colunas_e_tabelas_sem_perder_dados(tmp_path):
    engine = banco_antigo(tmp_path)
    assert all(not (cols(engine, t) & novas) for t, novas in NOVAS.items())
    database.configurar(engine)
    database.criar_tabelas()
    for tabela, novas in NOVAS.items():
        assert novas <= cols(engine, tabela), tabela
    assert {"equipe_membro", "ato_lavrado"} <= set(inspect(engine).get_table_names())
    with engine.connect() as con:
        assert tuple(con.execute(text("SELECT codigo, objetivo, interessado_orgao, assunto_tipo FROM inspecao")).one()) == (
            "INS-001", "Vistoria antiga", None, None)
        assert tuple(con.execute(text("SELECT nome, cpf_cnpj, corr_cep FROM proprietario")).one()) == (
            "Responsável Antigo Fictício", None, None)
        assert tuple(con.execute(text("SELECT nome, logradouro, uf, cep FROM local")).one()) == (
            "Fazenda Antiga Fictícia", None, None, None)
    database.criar_tabelas()  # idempotente
    engine.dispose()


def test_inspecao_legada_sem_equipe_continua_abrindo_nas_duas_saidas(tmp_path):
    clock.fixar_hoje(__import__("datetime").date(2026, 10, 23))
    try:
        engine = banco_antigo(tmp_path)
        database.configurar(engine)
        with TestClient(criar_app()) as c:  # a subida da API migra e preenche o legado
            d = c.get("/api/v1/inspecoes/1")
            assert d.status_code == 200, d.text
            d = d.json()
            assert (d["status"], d["equipe"], d["atos"], d["interessado_orgao"], d["numero_relatorio_sema"]) == (
                "FINALIZADA", [], [], None, None)
            assert d["empreendimento"]["nome"] == "Fazenda Antiga Fictícia" and d["empreendimento"]["cep"] is None
            assert c.get("/api/v1/inspecoes/1/relatorio").status_code == 200
            assert c.get("/api/v1/locais").status_code == 200
        engine.dispose()
    finally:
        clock.fixar_hoje(None)
