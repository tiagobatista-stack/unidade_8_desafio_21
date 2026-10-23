from datetime import date, datetime

from sqlalchemy import text

from app.models import Inspecao, ItemInspecao, Local, Proprietario
from app.services.migracao_dados import preencher_legado

AGORA = datetime(2026, 10, 22, 10, 0)


def _local(db, nome="Local Legado Fictício"):
    local = Local(nome=nome, municipio="Município Fictício", tipo="Tipo", latitude=-12.5, longitude=-55.5,
                  numero_car="MT-5107925-0000000000000000000000000000LEGA",
                  proprietarios=[Proprietario(nome="Dono Legado Fictício", telefone="65900000005", ordem=0)])
    db.add(local)
    db.flush()
    return local


def _insp(db, local, codigo, status, **kw):
    base = dict(codigo=codigo, numero_processo="SEMA-PRO-2026/1", local_id=local.id, objetivo="x",
                data_agendamento=date(2026, 10, 20), status=status, criado_em=AGORA, atualizado_em=AGORA)
    base.update(kw)
    i = Inspecao(**base)
    db.add(i)
    db.flush()
    return i


def _finalizada(db, local, codigo, **kw):
    return _insp(db, local, codigo, "FINALIZADA", resultado="APROVADA", fechado_em=AGORA,
                 data_realizacao=date(2026, 10, 21), **kw)


def test_preenche_a_copia_das_finalizadas_antigas_com_o_local_atual(db):
    local = _local(db)
    antiga = _finalizada(db, local, "INS-001")
    andamento = _insp(db, local, "INS-002", "EM_ANDAMENTO")
    aberta = _insp(db, local, "INS-003", "ABERTA")
    db.commit()
    assert antiga.empreendimento_json is None

    assert preencher_legado(db)["copias"] == 1
    db.expire_all()
    assert '"Dono Legado Fictício"' in db.get(Inspecao, antiga.id).empreendimento_json
    assert db.get(Inspecao, andamento.id).empreendimento_json is None  # só finalizadas
    assert db.get(Inspecao, aberta.id).empreendimento_json is None


def test_nao_sobrescreve_copia_existente_e_e_idempotente(db):
    local = _local(db)
    existente = _finalizada(db, local, "INS-001", empreendimento_json='{"nome": "Copia Original Fictícia"}')
    db.commit()
    assert preencher_legado(db)["copias"] == 0
    assert preencher_legado(db)["copias"] == 0
    db.expire_all()
    assert db.get(Inspecao, existente.id).empreendimento_json == '{"nome": "Copia Original Fictícia"}'


def test_legado_nao_muda_quando_o_local_e_editado_depois_do_preenchimento(db):
    local = _local(db)
    antiga = _finalizada(db, local, "INS-001")
    db.commit()
    preencher_legado(db)
    local.nome = "Nome Alterado Depois"
    local.proprietarios[0].nome = "Outro Dono Fictício"
    db.commit()
    db.expire_all()
    assert "Local Legado Fictício" in db.get(Inspecao, antiga.id).empreendimento_json
    assert "Outro Dono" not in db.get(Inspecao, antiga.id).empreendimento_json


def test_banco_antigo_sem_a_coluna_recebe_coluna_e_copia_na_subida(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app import database
    from app.main import criar_app
    from tests.unit.test_migracao import ESQUEMA_ANTIGO, ESQUEMA_LOCAL_ANTIGO

    monkeypatch.setenv("FOTOS_DIR", str(tmp_path / "fotos"))
    engine = database.criar_engine(f"sqlite:///{(tmp_path / 'legado.db').as_posix()}")
    with engine.begin() as con:
        con.execute(text(ESQUEMA_LOCAL_ANTIGO))
        con.execute(text(ESQUEMA_ANTIGO))
        con.execute(text("INSERT INTO local (nome, municipio, tipo, latitude, longitude, ativo) VALUES ('Local Antigo Fictício', 'M', 'T', -12.5, -55.5, 1)"))
        con.execute(text(
            "INSERT INTO inspecao (codigo, local_id, objetivo, data_agendamento, data_realizacao, status, resultado, criado_em, atualizado_em, fechado_em) "
            "VALUES ('INS-001', 1, 'Antiga', '2026-10-01', '2026-10-02', 'FINALIZADA', 'APROVADA', '2026-10-01 08:00:00', '2026-10-02 08:00:00', '2026-10-02 17:00:00')"))
    database.configurar(engine)
    with TestClient(criar_app()) as c:  # o lifespan migra e preenche
        d = c.get("/api/v1/inspecoes/1").json()
        assert d["empreendimento"]["nome"] == "Local Antigo Fictício" and d["empreendimento"]["numero_car"] is None
        assert d["empreendimento"]["proprietarios"] == []
        c.put("/api/v1/locais/1", json={"nome": "Nome Novo Fictício", "municipio": "M", "tipo": "T", "latitude": -12.5, "longitude": -55.5})
        assert c.get("/api/v1/inspecoes/1").json()["empreendimento"]["nome"] == "Local Antigo Fictício"  # cópia preservada
    engine.dispose()


# ---------- C3: numeração do legado ----------
def _finalizada_em(db, local, codigo, fechado):
    return _insp(db, local, codigo, "FINALIZADA", resultado="APROVADA", fechado_em=fechado,
                 data_realizacao=date(2026, 10, 21))


def test_numera_as_finalizadas_antigas_na_ordem_do_fechamento_e_por_ano(db):
    local = _local(db)
    # criadas fora de ordem de propósito: o número segue o fechamento, não o id
    tarde_2026 = _finalizada_em(db, local, "INS-001", datetime(2026, 10, 20, 9, 0))
    cedo_2026 = _finalizada_em(db, local, "INS-002", datetime(2026, 3, 1, 9, 0))
    ano_2025 = _finalizada_em(db, local, "INS-003", datetime(2025, 12, 31, 23, 0))
    sem_fechar = _insp(db, local, "INS-004", "EM_ANDAMENTO")
    db.commit()

    r = preencher_legado(db)
    db.expire_all()
    numeros = {i.codigo: i.numero_relatorio for i in db.query(Inspecao)}
    assert r["numeros"] == 3
    assert numeros == {"INS-003": "0001/2025", "INS-002": "0001/2026", "INS-001": "0002/2026", "INS-004": None}
    assert db.get(Inspecao, sem_fechar.id).numero_relatorio is None
    assert (tarde_2026.id, cedo_2026.id, ano_2025.id)  # (apenas para deixar claro quais foram criadas)


def test_numeracao_do_legado_e_idempotente_e_nao_renumera(db):
    local = _local(db)
    _finalizada_em(db, local, "INS-001", datetime(2026, 10, 20, 9, 0))
    db.commit()
    assert preencher_legado(db)["numeros"] == 1
    assert preencher_legado(db)["numeros"] == 0
    db.expire_all()
    assert db.query(Inspecao).one().numero_relatorio == "0001/2026"


def test_novos_fechamentos_continuam_a_sequencia_do_legado(db):
    from app.services.numeracao_service import atribuir_numero

    local = _local(db)
    _finalizada_em(db, local, "INS-001", datetime(2026, 10, 20, 9, 0))
    nova = _insp(db, local, "INS-002", "EM_ANDAMENTO")
    db.commit()
    preencher_legado(db)
    assert atribuir_numero(db, nova, 2026) == "0002/2026"


def test_banco_antigo_ganha_coluna_e_indice_unico_do_numero(tmp_path):
    from sqlalchemy import inspect

    from app import database
    from tests.unit.test_migracao import ESQUEMA_ANTIGO

    engine = database.criar_engine(f"sqlite:///{(tmp_path / 'sem_numero.db').as_posix()}")
    with engine.begin() as con:
        con.execute(text(ESQUEMA_ANTIGO))
    database.configurar(engine)
    database.criar_tabelas()
    database.criar_tabelas()  # idempotente
    insp = inspect(engine)
    assert {"numero_relatorio", "empreendimento_json", "numero_processo"} <= {c["name"] for c in insp.get_columns("inspecao")}
    indices = {i["name"]: i for i in insp.get_indexes("inspecao")}
    assert indices["ux_inspecao_numero_relatorio"]["unique"] in (1, True)
    assert "contador_relatorio" in insp.get_table_names()
    engine.dispose()
