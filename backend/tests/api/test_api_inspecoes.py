import pytest

BASE = "/api/v1"


def erro(r, status, codigo):
    assert r.status_code == status, r.text
    corpo = r.json()["erro"]
    assert set(corpo) == {"codigo", "mensagem", "detalhes"}
    assert corpo["codigo"] == codigo, corpo
    assert isinstance(corpo["mensagem"], str) and isinstance(corpo["detalhes"], list)
    return corpo


def por_codigo(client, codigo):
    dados = client.get(f"{BASE}/inspecoes", params={"tamanho": 100}).json()["dados"]
    return next(i for i in dados if i["codigo"] == codigo)


@pytest.fixture
def api(client, exemplos):
    return client


def nova_payload(**kw):
    base = {"numero_processo": "SEMA-PRO-2026/12345", "local_id": 1, "data_agendamento": "2026-10-20", "objetivo": "Vistoria de rotina"}
    base.update(kw)
    return base


# ---------- locais ----------
def test_locais_listar_e_detalhar(api):  # CA25, CA27
    r = api.get(f"{BASE}/locais")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["total"] == 4 and set(corpo) == {"dados", "total", "pagina", "tamanho"}
    assert all(isinstance(l["latitude"], float) and isinstance(l["longitude"], float) for l in corpo["dados"])
    d = api.get(f"{BASE}/locais/1").json()
    assert d["latitude"] == -10.42318 and d["longitude"] == -58.71264


def test_local_inexistente_404(api):
    erro(api.get(f"{BASE}/locais/999"), 404, "NAO_ENCONTRADO")
    erro(api.put(f"{BASE}/locais/999", json=dict(nome="x", municipio="m", tipo="t", latitude=-10, longitude=-58)), 404, "NAO_ENCONTRADO")


def test_local_latitude_fora_de_mt(api):  # CA26
    r = api.post(f"{BASE}/locais", json=dict(nome="Teste", municipio="X", tipo="Y", latitude=-25.0, longitude=-58.0))
    corpo = erro(r, 422, "COORDENADA_FORA_DE_MT")
    assert corpo["detalhes"][0]["campo"] == "latitude"


def test_local_sem_coordenada_422(api):  # RN11
    r = api.post(f"{BASE}/locais", json=dict(nome="Teste", municipio="X", tipo="Y"))
    corpo = erro(r, 422, "VALIDACAO_CAMPO")
    assert {d["campo"] for d in corpo["detalhes"]} == {"latitude", "longitude"}


def test_local_criar_e_atualizar(api):
    r = api.post(f"{BASE}/locais", json=dict(nome="Novo Local", municipio="X", tipo="Y", latitude=-12.5, longitude=-55.5))
    assert r.status_code == 201
    lid = r.json()["id"]
    r = api.put(f"{BASE}/locais/{lid}", json=dict(nome="Novo Local", municipio="Z", tipo="Y", latitude=-12.5, longitude=-55.5))
    assert r.status_code == 200 and r.json()["municipio"] == "Z"
    r = api.post(f"{BASE}/locais", json=dict(nome="Novo Local", municipio="X", tipo="Y", latitude=-12.5, longitude=-55.5))
    erro(r, 422, "VALIDACAO_CAMPO")


# ---------- cadastro ----------
def test_cadastrar_inspecao(api):  # CA01
    r = api.post(f"{BASE}/inspecoes", json=nova_payload())
    assert r.status_code == 201
    d = r.json()
    assert d["codigo"] == "INS-006" and d["status"] == "ABERTA" and d["data_realizacao"] is None
    assert d["resultado"] is None
    assert len(d["itens"]) == 6 and d["resumo_itens"] == {"total": 6, "respondidos": 0, "nao_conformes": 0}
    assert d["local"]["latitude"] == -10.42318


def test_cadastrar_sem_local(api):  # CA02
    erro(api.post(f"{BASE}/inspecoes", json={"numero_processo": "SEMA-PRO-2026/12345", "data_agendamento": "2026-10-20", "objetivo": "x"}), 422, "VALIDACAO_CAMPO")
    erro(api.post(f"{BASE}/inspecoes", json=nova_payload(local_id=999)), 422, "VALIDACAO_CAMPO")


def test_cadastrar_sem_agendamento(api):  # CA29
    corpo = erro(api.post(f"{BASE}/inspecoes", json={"numero_processo": "SEMA-PRO-2026/12345", "local_id": 1, "objetivo": "x"}), 422, "VALIDACAO_CAMPO")
    assert corpo["detalhes"][0]["campo"] == "data_agendamento"


def test_cadastrar_agendamento_28_10(api):  # CA30
    r = api.post(f"{BASE}/inspecoes", json=nova_payload(data_agendamento="2026-10-28"))
    assert r.status_code == 201


def test_cadastrar_realizacao_futura_e_anterior(api):  # CA03, CA32
    erro(api.post(f"{BASE}/inspecoes", json=nova_payload(data_realizacao="2026-10-24")), 422, "DATA_REALIZACAO_FUTURA")
    erro(api.post(f"{BASE}/inspecoes", json=nova_payload(data_realizacao="2026-10-19")), 422, "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO")


def test_cadastrar_data_invalida(api):
    erro(api.post(f"{BASE}/inspecoes", json=nova_payload(data_agendamento="20/10/2026")), 422, "VALIDACAO_CAMPO")


def test_codigos_consecutivos(api):  # CA04
    a = api.post(f"{BASE}/inspecoes", json=nova_payload()).json()["codigo"]
    b = api.post(f"{BASE}/inspecoes", json=nova_payload()).json()["codigo"]
    assert (a, b) == ("INS-006", "INS-007")


# ---------- consulta ----------
def test_lista_envelope_ordenacao_e_campos(api):
    corpo = api.get(f"{BASE}/inspecoes").json()
    assert set(corpo) == {"dados", "total", "pagina", "tamanho"} and corpo["total"] == 5
    datas = [i["data_agendamento"] for i in corpo["dados"]]
    assert datas == sorted(datas, reverse=True)
    primeiro = corpo["dados"][0]
    assert "itens" not in primeiro and primeiro["local"]["nome"] and primeiro["codigo"] == "INS-005"


def test_filtro_status(api):  # CA15
    d = api.get(f"{BASE}/inspecoes", params={"status": "FINALIZADA"}).json()
    assert d["total"] == 3 and {i["status"] for i in d["dados"]} == {"FINALIZADA"}
    erro(api.get(f"{BASE}/inspecoes", params={"status": "XPTO"}), 422, "VALIDACAO_CAMPO")


def test_filtro_periodo_inclusivo(api):  # CA16
    d = api.get(f"{BASE}/inspecoes", params={"data_inicio": "2026-10-13", "data_fim": "2026-10-20"}).json()
    assert sorted(i["codigo"] for i in d["dados"]) == ["INS-002", "INS-003", "INS-004"]
    erro(api.get(f"{BASE}/inspecoes", params={"data_inicio": "2026-10-20", "data_fim": "2026-10-01"}), 422, "VALIDACAO_CAMPO")


def test_filtro_local_e_paginacao(api):
    d = api.get(f"{BASE}/inspecoes", params={"local_id": 1}).json()
    assert d["total"] == 2
    p = api.get(f"{BASE}/inspecoes", params={"pagina": 2, "tamanho": 2}).json()
    assert p["total"] == 5 and len(p["dados"]) == 2 and p["pagina"] == 2
    erro(api.get(f"{BASE}/inspecoes", params={"tamanho": 0}), 422, "VALIDACAO_CAMPO")


def test_detalhe_mostra_itens_e_duas_datas(api):  # CA17, CA34
    insp = por_codigo(api, "INS-004")
    d = api.get(f"{BASE}/inspecoes/{insp['id']}").json()
    assert len(d["itens"]) == 6
    assert d["data_agendamento"] == "2026-10-20" and d["data_realizacao"] == "2026-10-20"
    assert d["resumo_itens"] == {"total": 6, "respondidos": 3, "nao_conformes": 0}
    ins5 = api.get(f"{BASE}/inspecoes/{por_codigo(api, 'INS-005')['id']}").json()
    assert ins5["data_realizacao"] is None and ins5["resultado"] is None  # RN10
    erro(api.get(f"{BASE}/inspecoes/999"), 404, "NAO_ENCONTRADO")


# ---------- itens ----------
def test_registrar_item_e_persistir(api):  # CA05, CA06, CA31
    novo = api.post(f"{BASE}/inspecoes", json=nova_payload()).json()
    item = novo["itens"][0]
    r = api.patch(f"{BASE}/inspecoes/{novo['id']}/itens/{item['id']}", json={"situacao": "CONFORME"})
    assert r.status_code == 200 and r.json()["situacao"] == "CONFORME"
    d = api.get(f"{BASE}/inspecoes/{novo['id']}").json()
    assert d["status"] == "EM_ANDAMENTO" and d["data_realizacao"] == "2026-10-23"
    assert d["itens"][0]["situacao"] == "CONFORME"


def test_item_em_agendada_futura_bloqueado_p1(api):  # P1
    ins5 = api.get(f"{BASE}/inspecoes/{por_codigo(api, 'INS-005')['id']}").json()
    r = api.patch(f"{BASE}/inspecoes/{ins5['id']}/itens/{ins5['itens'][0]['id']}", json={"situacao": "CONFORME"})
    corpo = erro(r, 422, "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO")
    assert "28/10/2026" in corpo["mensagem"]


def test_item_situacao_invalida_422(api):
    d = api.post(f"{BASE}/inspecoes", json=nova_payload()).json()
    erro(api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{d['itens'][0]['id']}", json={"situacao": "TALVEZ"}), 422, "VALIDACAO_CAMPO")


def test_item_avulso_adicionar_e_remover(api):  # CA07
    d = api.post(f"{BASE}/inspecoes", json=nova_payload()).json()
    r = api.post(f"{BASE}/inspecoes/{d['id']}/itens", json={"descricao": "Cerca perimetral"})
    assert r.status_code == 201 and r.json()["origem"] == "AVULSO"
    assert len(api.get(f"{BASE}/inspecoes/{d['id']}/itens").json()) == 7
    assert api.delete(f"{BASE}/inspecoes/{d['id']}/itens/{r.json()['id']}").status_code == 204
    assert len(api.get(f"{BASE}/inspecoes/{d['id']}/itens").json()) == 6
    erro(api.delete(f"{BASE}/inspecoes/{d['id']}/itens/{d['itens'][0]['id']}"), 409, "ITEM_DE_MODELO_NAO_REMOVIVEL")
    erro(api.post(f"{BASE}/inspecoes/{d['id']}/itens", json={"descricao": "  "}), 422, "VALIDACAO_CAMPO")


def test_itens_de_finalizada_imutaveis(api):  # CA08
    d = api.get(f"{BASE}/inspecoes/{por_codigo(api, 'INS-001')['id']}").json()
    erro(api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{d['itens'][0]['id']}", json={"situacao": "NAO_CONFORME"}), 409, "INSPECAO_IMUTAVEL")
    erro(api.post(f"{BASE}/inspecoes/{d['id']}/itens", json={"descricao": "x"}), 409, "INSPECAO_IMUTAVEL")
    erro(api.delete(f"{BASE}/inspecoes/{d['id']}/itens/{d['itens'][0]['id']}"), 409, "INSPECAO_IMUTAVEL")


def test_item_inexistente_404(api):
    d = api.post(f"{BASE}/inspecoes", json=nova_payload()).json()
    erro(api.patch(f"{BASE}/inspecoes/{d['id']}/itens/9999", json={"situacao": "CONFORME"}), 404, "NAO_ENCONTRADO")


# ---------- fechar / cancelar / editar ----------
def test_fechar_bloqueado_lista_itens(api):  # CA09 — INS-004 tem 3 pendentes
    d = api.get(f"{BASE}/inspecoes/{por_codigo(api, 'INS-004')['id']}").json()
    corpo = erro(api.post(f"{BASE}/inspecoes/{d['id']}/fechar"), 422, "FECHAMENTO_BLOQUEADO")
    assert len(corpo["detalhes"]) == 3
    esperados = {f"itens.{i['id']}" for i in d["itens"] if i["situacao"] == "NAO_RESPONDIDO"}
    assert {x["campo"] for x in corpo["detalhes"]} == esperados


def _preencher(api, d, sits, obs=None):
    for it in d["itens"]:
        body = {"situacao": sits.get(it["ordem"], "CONFORME")}
        if obs and it["ordem"] in obs:
            body["observacao"] = obs[it["ordem"]]
        assert api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{it['id']}", json=body).status_code == 200


@pytest.mark.parametrize(
    "sits,obs,esperado",
    [({}, None, "APROVADA"), ({5: "NAO_CONFORME"}, {5: "desatualizado"}, "APROVADA_COM_RESSALVAS"),
     ({6: "NAO_CONFORME"}, {6: "irregular"}, "REPROVADA")],
)
def test_fechar_fluxo_completo(api, sits, obs, esperado):  # CA11–CA14
    d = api.post(f"{BASE}/inspecoes", json=nova_payload()).json()
    _preencher(api, d, sits, obs)
    r = api.post(f"{BASE}/inspecoes/{d['id']}/fechar")
    assert r.status_code == 200
    f = r.json()
    assert f["status"] == "FINALIZADA" and f["resultado"] == esperado and f["fechado_em"]
    erro(api.patch(f"{BASE}/inspecoes/{d['id']}", json={"observacoes": "x"}), 409, "INSPECAO_IMUTAVEL")
    erro(api.post(f"{BASE}/inspecoes/{d['id']}/fechar"), 409, "TRANSICAO_INVALIDA")


def test_fechar_nc_sem_observacao(api):  # CA10
    d = api.post(f"{BASE}/inspecoes", json=nova_payload()).json()
    _preencher(api, d, {4: "NAO_CONFORME"})
    erro(api.post(f"{BASE}/inspecoes/{d['id']}/fechar"), 422, "FECHAMENTO_BLOQUEADO")


def test_fechar_aberta_409(api):  # P3
    d = api.post(f"{BASE}/inspecoes", json=nova_payload()).json()
    erro(api.post(f"{BASE}/inspecoes/{d['id']}/fechar"), 409, "TRANSICAO_INVALIDA")


def test_cancelar(api):
    ins5 = por_codigo(api, "INS-005")
    erro(api.post(f"{BASE}/inspecoes/{ins5['id']}/cancelar", json={"motivo": "  "}), 422, "VALIDACAO_CAMPO")
    erro(api.post(f"{BASE}/inspecoes/{ins5['id']}/cancelar", json={}), 422, "VALIDACAO_CAMPO")
    r = api.post(f"{BASE}/inspecoes/{ins5['id']}/cancelar", json={"motivo": "Sem acesso ao local"})
    assert r.status_code == 200 and r.json()["status"] == "CANCELADA"
    erro(api.post(f"{BASE}/inspecoes/{ins5['id']}/cancelar", json={"motivo": "outra vez"}), 409, "TRANSICAO_INVALIDA")
    ins4 = por_codigo(api, "INS-004")  # P5
    erro(api.post(f"{BASE}/inspecoes/{ins4['id']}/cancelar", json={"motivo": "x"}), 409, "TRANSICAO_INVALIDA")
    erro(api.post(f"{BASE}/inspecoes/999/cancelar", json={"motivo": "x"}), 404, "NAO_ENCONTRADO")


def test_patch_finalizada_imutavel(api):
    ins1 = por_codigo(api, "INS-001")
    erro(api.patch(f"{BASE}/inspecoes/{ins1['id']}", json={"observacoes": "x"}), 409, "INSPECAO_IMUTAVEL")


def test_patch_agendamento_por_status(api):  # CA33
    ins4 = por_codigo(api, "INS-004")
    erro(api.patch(f"{BASE}/inspecoes/{ins4['id']}", json={"data_agendamento": "2026-10-21"}), 409, "CAMPO_NAO_EDITAVEL_NO_STATUS")
    ins5 = por_codigo(api, "INS-005")
    r = api.patch(f"{BASE}/inspecoes/{ins5['id']}", json={"data_agendamento": "2026-10-22", "objetivo": "Novo objetivo"})
    assert r.status_code == 200 and r.json()["data_agendamento"] == "2026-10-22"
    # agora já pode registrar item (P1 resolvido por reagendamento)
    d = r.json()
    ok = api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{d['itens'][0]['id']}", json={"situacao": "CONFORME"})
    assert ok.status_code == 200


def test_patch_realizacao_em_andamento(api):
    ins4 = por_codigo(api, "INS-004")
    erro(api.patch(f"{BASE}/inspecoes/{ins4['id']}", json={"data_realizacao": "2026-10-24"}), 422, "DATA_REALIZACAO_FUTURA")
    erro(api.patch(f"{BASE}/inspecoes/{ins4['id']}", json={"data_realizacao": "2026-10-19"}), 422, "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO")


def test_observacoes_vistoria_via_api(api):  # CA35–CA41
    ins5 = por_codigo(api, "INS-005")
    url = f"{BASE}/inspecoes/{ins5['id']}"
    r = api.patch(url, json={"observacoes_vistoria": "x" * 500})
    assert r.status_code == 200 and r.json()["status"] == "ABERTA"
    assert api.patch(url, json={"observacoes_vistoria": "a" * 2000}).status_code == 200
    erro(api.patch(url, json={"observacoes_vistoria": "a" * 2001}), 422, "VALIDACAO_CAMPO")
    assert api.patch(url, json={"observacoes_vistoria": "   "}).json()["observacoes_vistoria"] is None
    texto = "<script>alert(1)</script>\nlinha 2"
    assert api.patch(url, json={"observacoes_vistoria": texto}).json()["observacoes_vistoria"] == texto
    ins1 = por_codigo(api, "INS-001")
    erro(api.patch(f"{BASE}/inspecoes/{ins1['id']}", json={"observacoes_vistoria": "x"}), 409, "INSPECAO_IMUTAVEL")


def test_patch_vazio_nao_altera(api):
    ins5 = por_codigo(api, "INS-005")
    r = api.patch(f"{BASE}/inspecoes/{ins5['id']}", json={})
    assert r.status_code == 200


def test_erro_interno_nao_vaza_detalhes(engine):
    from fastapi.testclient import TestClient

    from app.main import criar_app

    app = criar_app()

    @app.get("/api/v1/explode")
    def explode():
        raise RuntimeError("segredo interno")

    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/api/v1/explode")
    corpo = erro(r, 500, "ERRO_INTERNO")
    assert "segredo" not in r.text and corpo["detalhes"] == []
