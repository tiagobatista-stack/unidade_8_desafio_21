import pytest

BASE = "/api/v1"
NP = "SEMA-PRO-2026/12345"


@pytest.fixture
def api(client, exemplos):
    return client


def erro(r, status, codigo):
    assert r.status_code == status, r.text
    corpo = r.json()["erro"]
    assert corpo["codigo"] == codigo, corpo
    return corpo


def nova(api, **kw):
    corpo = {"numero_processo": NP, "local_id": 1, "data_agendamento": "2026-10-20", "objetivo": "Vistoria"}
    corpo.update(kw)
    return api.post(f"{BASE}/inspecoes", json=corpo)


def por_codigo(api, codigo):
    return next(i for i in api.get(f"{BASE}/inspecoes", params={"tamanho": 100}).json()["dados"] if i["codigo"] == codigo)


# ---------- cadastro ----------
def test_cadastro_grava_e_devolve_numero_do_processo_com_trim(api):
    r = nova(api, numero_processo="  SEMA-PRO-2026/12345  ")
    assert r.status_code == 201 and r.json()["numero_processo"] == NP
    assert api.get(f"{BASE}/inspecoes/{r.json()['id']}").json()["numero_processo"] == NP


@pytest.mark.parametrize("valor", [None, "", "   "])
def test_cadastro_exige_numero_do_processo(api, valor):
    corpo = {"local_id": 1, "data_agendamento": "2026-10-20", "objetivo": "x"}
    if valor is not None:
        corpo["numero_processo"] = valor
    detalhes = erro(api.post(f"{BASE}/inspecoes", json=corpo), 422, "VALIDACAO_CAMPO")["detalhes"]
    assert detalhes[0]["campo"] == "numero_processo"


def test_numero_do_processo_limite_de_60(api):
    assert nova(api, numero_processo="P" * 60).status_code == 201
    erro(nova(api, numero_processo="P" * 61), 422, "VALIDACAO_CAMPO")


def test_texto_livre_e_aceito_e_nao_e_unico(api):
    assert nova(api, numero_processo="Processo 99/2025 (físico)").status_code == 201
    assert nova(api, numero_processo="Processo 99/2025 (físico)").status_code == 201


def test_exemplos_trazem_numero_do_processo(api):
    assert por_codigo(api, "INS-001")["numero_processo"] == "SEMA-PRO-2026/10001"
    assert por_codigo(api, "INS-005")["numero_processo"] == "SEMA-PRO-2026/10005"


# ---------- edição e campos_editaveis ----------
def detalhe(api, codigo):
    return api.get(f"{BASE}/inspecoes/{por_codigo(api, codigo)['id']}").json()


@pytest.mark.parametrize(
    "codigo,esperado",
    [
        ("INS-005", ["data_agendamento", "local_id", "numero_processo", "objetivo", "observacoes", "observacoes_vistoria"]),
        ("INS-004", ["data_realizacao", "numero_processo", "observacoes", "observacoes_vistoria"]),
        ("INS-001", []),
    ],
)
def test_campos_editaveis_vem_da_api_por_status(api, codigo, esperado):
    assert detalhe(api, codigo)["campos_editaveis"] == esperado


def test_campos_editaveis_vazio_em_cancelada(api):
    i5 = por_codigo(api, "INS-005")
    api.post(f"{BASE}/inspecoes/{i5['id']}/cancelar", json={"motivo": "x"})
    assert detalhe(api, "INS-005")["campos_editaveis"] == []


@pytest.mark.parametrize("codigo", ["INS-005", "INS-004"])  # Aberta e Em andamento
def test_editar_numero_do_processo(api, codigo):
    i = por_codigo(api, codigo)
    r = api.patch(f"{BASE}/inspecoes/{i['id']}", json={"numero_processo": "  SEMA-PRO-2026/99999 "})
    assert r.status_code == 200 and r.json()["numero_processo"] == "SEMA-PRO-2026/99999"
    assert por_codigo(api, codigo)["numero_processo"] == "SEMA-PRO-2026/99999"


def test_editar_numero_vazio_ou_longo_422_e_mantem_o_anterior(api):
    i = por_codigo(api, "INS-005")
    erro(api.patch(f"{BASE}/inspecoes/{i['id']}", json={"numero_processo": "  "}), 422, "VALIDACAO_CAMPO")
    erro(api.patch(f"{BASE}/inspecoes/{i['id']}", json={"numero_processo": "P" * 61}), 422, "VALIDACAO_CAMPO")
    erro(api.patch(f"{BASE}/inspecoes/{i['id']}", json={"numero_processo": None}), 422, "VALIDACAO_CAMPO")
    assert por_codigo(api, "INS-005")["numero_processo"] == "SEMA-PRO-2026/10005"


def test_editar_numero_em_finalizada_409(api):
    i1 = por_codigo(api, "INS-001")
    erro(api.patch(f"{BASE}/inspecoes/{i1['id']}", json={"numero_processo": "X"}), 409, "INSPECAO_IMUTAVEL")


def test_editar_varios_campos_de_uma_vez_em_aberta(api):
    i5 = por_codigo(api, "INS-005")
    r = api.patch(f"{BASE}/inspecoes/{i5['id']}", json={
        "numero_processo": "SEMA-PRO-2026/777", "local_id": 2, "objetivo": "Novo objetivo", "data_agendamento": "2026-10-22",
    })
    d = r.json()
    assert r.status_code == 200
    assert (d["numero_processo"], d["local"]["id"], d["objetivo"], d["data_agendamento"]) == (
        "SEMA-PRO-2026/777", 2, "Novo objetivo", "2026-10-22")


# ---------- listagem: status repetido e filtro por número ----------
def codigos(api, **params):
    r = api.get(f"{BASE}/inspecoes", params=params)
    assert r.status_code == 200, r.text
    return sorted(i["codigo"] for i in r.json()["dados"]), r.json()["total"]


def test_status_repetido_une_os_grupos(api):
    assert codigos(api, status=["ABERTA", "EM_ANDAMENTO"]) == (["INS-004", "INS-005"], 2)  # pendências
    assert codigos(api, status="FINALIZADA")[0] == ["INS-001", "INS-002", "INS-003"]  # um só continua valendo
    i5 = por_codigo(api, "INS-005")
    api.post(f"{BASE}/inspecoes/{i5['id']}/cancelar", json={"motivo": "x"})
    ativas, total = codigos(api, status=["ABERTA", "EM_ANDAMENTO", "FINALIZADA"])  # "Inspeções" = sem canceladas
    assert total == 4 and "INS-005" not in ativas


def test_status_repetido_respeita_paginacao(api):
    r = api.get(f"{BASE}/inspecoes", params={"status": ["ABERTA", "EM_ANDAMENTO", "FINALIZADA"], "tamanho": 2, "pagina": 2})
    corpo = r.json()
    assert corpo["total"] == 5 and len(corpo["dados"]) == 2


def test_status_invalido_na_lista_422(api):
    erro(api.get(f"{BASE}/inspecoes", params={"status": ["ABERTA", "XPTO"]}), 422, "VALIDACAO_CAMPO")


def test_filtro_por_numero_parcial_e_sem_diferenciar_maiusculas(api):
    assert codigos(api, numero_processo="10003")[0] == ["INS-003"]
    assert codigos(api, numero_processo="sema-pro-2026/1000")[1] == 5
    assert codigos(api, numero_processo="  10001 ")[0] == ["INS-001"]
    assert codigos(api, numero_processo="nao-existe") == ([], 0)
    assert codigos(api, numero_processo="")[1] == 5  # vazio não filtra


def test_filtro_trata_percentual_e_sublinhado_como_texto(api):
    nova(api, numero_processo="PRO_2026%A")
    assert codigos(api, numero_processo="%")[1] == 1  # só o que contém % de fato
    assert codigos(api, numero_processo="_")[1] == 1
    assert codigos(api, numero_processo="O_2026%A")[1] == 1


def test_filtro_combina_com_status_e_nao_vaza_aspas(api):
    assert codigos(api, numero_processo="2026/1000", status="FINALIZADA")[0] == ["INS-001", "INS-002", "INS-003"]
    assert codigos(api, numero_processo="2026/1000", status=["ABERTA", "EM_ANDAMENTO"])[0] == ["INS-004", "INS-005"]
    assert codigos(api, numero_processo="' OR 1=1 --") == ([], 0)  # parametrizado: sem injeção


def test_lista_traz_numero_do_processo(api):
    primeiro = api.get(f"{BASE}/inspecoes").json()["dados"][0]
    assert primeiro["numero_processo"] == "SEMA-PRO-2026/10005"


# ---------- locais criados pela interface ----------
def test_criar_local_novo_e_usar_na_inspecao(api):
    r = api.post(f"{BASE}/locais", json=dict(nome="Local Criado na Tela", municipio="Cuiabá", tipo="Indústria", latitude=-15.6, longitude=-56.1))
    assert r.status_code == 201
    i = nova(api, local_id=r.json()["id"])
    assert i.status_code == 201 and i.json()["local"]["nome"] == "Local Criado na Tela"


def test_local_fora_de_mt_nao_e_criado(api):
    r = api.post(f"{BASE}/locais", json=dict(nome="Fora", municipio="X", tipo="Y", latitude=-25.0, longitude=-58.0))
    erro(r, 422, "COORDENADA_FORA_DE_MT")
    assert all(l["nome"] != "Fora" for l in api.get(f"{BASE}/locais").json()["dados"])
