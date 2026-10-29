"""Erros de validação do FastAPI/Pydantic chegam em português, com o rótulo do campo."""
import re

import pytest

from app.errors import _mensagem_pt

BASE = "/api/v1"
INGLES = re.compile(r"Field required|Input should|valid (integer|number|string|date)|String should|ensure this", re.I)


@pytest.fixture
def api(client, exemplos):
    return client


def detalhes(r):
    assert r.status_code == 422, r.text
    corpo = r.json()["erro"]
    assert corpo["codigo"] == "VALIDACAO_CAMPO"
    assert not INGLES.search(r.text), r.text  # nenhuma mensagem em inglês
    return {d["campo"]: d["mensagem"] for d in corpo["detalhes"]}


def inspecao(**kw):
    base = {"numero_processo": "P-1", "local_id": 1, "data_agendamento": "2026-10-20", "objetivo": "x"}
    base.update(kw)
    return base


def test_campo_obrigatorio_usa_o_rotulo_e_mantem_o_nome_tecnico_em_campo(api):
    corpo = inspecao()
    del corpo["objetivo"], corpo["numero_processo"]
    assert detalhes(api.post(f"{BASE}/inspecoes", json=corpo)) == {
        "objetivo": "Objetivo: obrigatória", "numero_processo": "Número do processo: obrigatória"}


def test_local_sem_nome_e_sem_tipo(api):
    d = detalhes(api.post(f"{BASE}/locais", json={"municipio": "M", "latitude": -12.5, "longitude": -55.5}))
    assert d == {"nome": "Nome: obrigatória", "tipo": "Tipo: obrigatória"}


def test_tipos_errados(api):
    d = detalhes(api.post(f"{BASE}/inspecoes", json=inspecao(local_id="abc", data_agendamento="20/10/2026", objetivo=5)))
    assert d == {
        "local_id": "Local: deve ser um número",
        "data_agendamento": "Data de agendamento: data inválida, use AAAA-MM-DD",
        "objetivo": "Objetivo: tipo inválido, esperado texto",
    }


def test_linha_da_lista_aparece_na_mensagem(api):
    d = detalhes(api.post(f"{BASE}/inspecoes", json=inspecao(equipe=[{"nome": "A"}, {"cargo": "x"}])))
    assert d == {"equipe.1.nome": "Nome (linha 2): obrigatória"}


def test_parametros_de_consulta(api):
    r = api.get(f"{BASE}/inspecoes", params={"tamanho": 1000, "pagina": 0, "status": "XX"})
    d = detalhes(r)
    assert d["tamanho"] == "Tamanho: deve ser menor ou igual a 100"
    assert d["pagina"] == "Página: deve ser maior ou igual a 1"
    assert d["status.0"] == "Status (linha 1): valor inválido"  # status é repetível: cada valor é uma linha


def test_corpo_que_nao_e_json(api):
    r = api.post(f"{BASE}/inspecoes", content="{ruim", headers={"content-type": "application/json"})
    assert r.status_code == 422
    assert not INGLES.search(r.text), r.text


@pytest.mark.parametrize("erro,esperado", [
    ({"type": "missing", "loc": ("body", "latitude"), "msg": "Field required"}, "Latitude: obrigatória"),
    ({"type": "string_too_long", "loc": ("body", "objetivo"), "msg": "x", "ctx": {"max_length": 200}}, "Objetivo: máximo de 200 caracteres"),
    ({"type": "missing", "loc": ("body", "campo_desconhecido_x"), "msg": "Field required"}, "Campo desconhecido x: obrigatória"),
    ({"type": "tipo_nunca_visto", "loc": ("body", "uf"), "msg": "x"}, "UF: valor inválido"),
])
def test_mensagem_pt_unitario(erro, esperado):
    assert _mensagem_pt(erro) == esperado
