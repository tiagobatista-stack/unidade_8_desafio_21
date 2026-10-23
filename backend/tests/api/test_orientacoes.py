from datetime import date

import pytest

from app.domain.orientacoes import MSG_NAO_INICIADA, motivo_fechamento_bloqueado, motivo_registro_bloqueado

BASE = "/api/v1"
HOJE = date(2026, 10, 23)


@pytest.fixture
def api(client, exemplos):
    return client


def por_codigo(api, codigo):
    return next(i for i in api.get(f"{BASE}/inspecoes", params={"tamanho": 100}).json()["dados"] if i["codigo"] == codigo)


def detalhe(api, codigo):
    return api.get(f"{BASE}/inspecoes/{por_codigo(api, codigo)['id']}").json()


def nova(api, agendamento):
    r = api.post(f"{BASE}/inspecoes", json={
        "numero_processo": "SEMA-PRO-2026/12345", "local_id": 1, "data_agendamento": agendamento, "objetivo": "x"})
    assert r.status_code == 201
    return r.json()


# ---------- domínio (funções puras) ----------
def test_motivo_fechamento_so_em_aberta():
    assert motivo_fechamento_bloqueado("ABERTA") == MSG_NAO_INICIADA
    for status in ("EM_ANDAMENTO", "FINALIZADA", "CANCELADA"):
        assert motivo_fechamento_bloqueado(status) is None


def test_motivo_registro_so_em_aberta_com_agendamento_futuro():
    msg = motivo_registro_bloqueado("ABERTA", date(2026, 10, 30), HOJE)
    assert "30/10/2026" in msg and "Editar inspeção" in msg
    assert motivo_registro_bloqueado("ABERTA", HOJE, HOJE) is None  # hoje não é futuro
    assert motivo_registro_bloqueado("ABERTA", date(2026, 10, 20), HOJE) is None
    for status in ("EM_ANDAMENTO", "FINALIZADA", "CANCELADA"):
        assert motivo_registro_bloqueado(status, date(2026, 12, 1), HOJE) is None


# ---------- A1: mensagem ao fechar inspeção Aberta ----------
def test_fechar_aberta_devolve_orientacao_com_codigo_estavel(api):
    d = nova(api, "2026-10-20")
    r = api.post(f"{BASE}/inspecoes/{d['id']}/fechar")
    assert r.status_code == 409
    erro = r.json()["erro"]
    assert erro["codigo"] == "TRANSICAO_INVALIDA"
    assert erro["mensagem"] == MSG_NAO_INICIADA
    assert "Transição de" not in erro["mensagem"] and "ABERTA" not in erro["mensagem"]  # nada de jargão técnico


def test_fechar_aberta_com_agendamento_futuro_tambem_orienta(api):
    r = api.post(f"{BASE}/inspecoes/{por_codigo(api, 'INS-005')['id']}/fechar")
    assert r.status_code == 409 and r.json()["erro"]["mensagem"] == MSG_NAO_INICIADA


def test_fechar_outros_status_mantem_codigos(api):
    i1 = por_codigo(api, "INS-001")  # finalizada: segue TRANSICAO_INVALIDA
    r = api.post(f"{BASE}/inspecoes/{i1['id']}/fechar")
    assert r.status_code == 409 and r.json()["erro"]["codigo"] == "TRANSICAO_INVALIDA"
    i4 = por_codigo(api, "INS-004")  # em andamento com pendências: segue FECHAMENTO_BLOQUEADO
    r = api.post(f"{BASE}/inspecoes/{i4['id']}/fechar")
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "FECHAMENTO_BLOQUEADO"


def test_detalhe_informa_motivo_de_fechamento_bloqueado(api):
    assert detalhe(api, "INS-005")["fechamento_bloqueado_motivo"] == MSG_NAO_INICIADA
    assert detalhe(api, "INS-004")["fechamento_bloqueado_motivo"] is None
    assert detalhe(api, "INS-001")["fechamento_bloqueado_motivo"] is None


# ---------- A3: aviso preventivo de agendamento futuro ----------
def test_detalhe_aviso_preventivo_com_agendamento_futuro(api):
    d = detalhe(api, "INS-005")  # agendada para 28/10/2026; hoje = 23/10/2026
    assert "28/10/2026" in d["registro_bloqueado_motivo"]
    assert "reagende em Editar inspeção" in d["registro_bloqueado_motivo"]


def test_aviso_nao_aparece_sem_agendamento_futuro_nem_fora_de_aberta(api):
    assert nova(api, "2026-10-23")["registro_bloqueado_motivo"] is None  # agendada para hoje
    assert nova(api, "2026-10-20")["registro_bloqueado_motivo"] is None  # agendada no passado
    assert detalhe(api, "INS-004")["registro_bloqueado_motivo"] is None  # em andamento
    assert detalhe(api, "INS-001")["registro_bloqueado_motivo"] is None  # finalizada


def test_aviso_some_ao_reagendar_e_o_registro_passa_a_funcionar(api):
    i5 = por_codigo(api, "INS-005")
    r = api.patch(f"{BASE}/inspecoes/{i5['id']}", json={"data_agendamento": "2026-10-22"})
    assert r.status_code == 200 and r.json()["registro_bloqueado_motivo"] is None
    item = r.json()["itens"][0]
    ok = api.patch(f"{BASE}/inspecoes/{i5['id']}/itens/{item['id']}", json={"situacao": "CONFORME"})
    assert ok.status_code == 200


def test_bloqueio_da_api_continua_valendo_alem_do_aviso(api):
    d = detalhe(api, "INS-005")
    r = api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{d['itens'][0]['id']}", json={"situacao": "CONFORME"})
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO"


def test_aviso_acompanha_o_relogio_injetavel(api):
    from app import clock

    clock.fixar_hoje(date(2026, 10, 28))  # chegou o dia do agendamento
    assert detalhe(api, "INS-005")["registro_bloqueado_motivo"] is None
    clock.fixar_hoje(date(2026, 10, 27))
    assert "28/10/2026" in detalhe(api, "INS-005")["registro_bloqueado_motivo"]
