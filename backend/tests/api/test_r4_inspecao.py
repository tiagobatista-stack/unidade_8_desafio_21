"""R4/E1: interessado, assunto, equipe técnica, providências, atos e nº do relatório na SEMA."""
import pytest

BASE = "/api/v1"
MP = {
    "interessado_orgao": "Ministério Público do Estado de Mato Grosso",
    "interessado_unidade": "1ª Promotoria de Justiça Cível",
    "interessado_comarca": "Comarca de Juína",
    "interessado_requerente": "Promotor de Justiça",
}


@pytest.fixture
def api(client, exemplos):
    return client


def erro(r, status, codigo):
    assert r.status_code == status, r.text
    corpo = r.json()["erro"]
    assert corpo["codigo"] == codigo, corpo
    return corpo


def payload(**kw):
    base = {"numero_processo": "212345/2030", "local_id": 1, "data_agendamento": "2026-10-20", "objetivo": "Vistoria"}
    base.update(kw)
    return base


def criar(api, **kw):
    r = api.post(f"{BASE}/inspecoes", json=payload(**kw))
    assert r.status_code == 201, r.text
    return r.json()


def responder_tudo(api, d):
    for it in d["itens"]:
        assert api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{it['id']}", json={"situacao": "CONFORME"}).status_code == 200


def finalizada(api, **kw):
    d = criar(api, equipe=[{"nome": "Analista Fictício"}], **kw)
    responder_tudo(api, d)
    r = api.post(f"{BASE}/inspecoes/{d['id']}/fechar")
    assert r.status_code == 200, r.text
    return r.json()


def patch(api, d, **kw):
    return api.patch(f"{BASE}/inspecoes/{d['id']}", json=kw)


# ---------- criação ----------
def test_criar_com_todos_os_dados_da_capa(api):
    d = criar(
        api, **MP, assunto_tipo="Atendimento a Denúncia", providencias_texto="  Notificado o responsável.  ",
        equipe=[{"nome": " Ana Fictícia ", "cargo": "Engenheira Florestal", "orgao": "SEMA-MT"}, {"nome": "Beto Fictício"}],
        atos=[{"tipo": "Notificação"}, {"tipo": "Auto de Infração", "numero": " AI-0001/2030 "}],
    )
    assert d["interessado_orgao"] == MP["interessado_orgao"] and d["interessado_comarca"] == "Comarca de Juína"
    assert d["assunto_tipo"] == "Atendimento a Denúncia" and d["assunto_outro"] is None
    assert d["providencias_texto"] == "Notificado o responsável."
    assert d["equipe"] == [
        {"nome": "Ana Fictícia", "cargo": "Engenheira Florestal", "orgao": "SEMA-MT"},
        {"nome": "Beto Fictício", "cargo": None, "orgao": None}]
    assert [(a["tipo"], a["numero"]) for a in d["atos"]] == [("Notificação", None), ("Auto de Infração", "AI-0001/2030")]
    assert d["numero_relatorio_sema"] is None
    assert d["numero_processo"] == "212345/2030"  # o protocolo reaproveita numero_processo


def test_criar_sem_os_dados_novos_continua_valido(api):
    d = criar(api)
    assert (d["interessado_orgao"], d["assunto_tipo"], d["equipe"], d["atos"]) == (None, None, [], [])


# ---------- assunto ----------
def test_assunto_fora_da_lista_e_rejeitado(api):
    c = erro(api.post(f"{BASE}/inspecoes", json=payload(assunto_tipo="Qualquer coisa")), 422, "VALIDACAO_CAMPO")
    assert c["detalhes"][0]["campo"] == "assunto_tipo"


def test_assunto_outro_exige_texto_livre(api):
    c = erro(api.post(f"{BASE}/inspecoes", json=payload(assunto_tipo="Outro")), 422, "VALIDACAO_CAMPO")
    assert c["detalhes"][0]["campo"] == "assunto_outro"
    d = criar(api, assunto_tipo="Outro", assunto_outro="  Vistoria especial  ")
    assert (d["assunto_tipo"], d["assunto_outro"]) == ("Outro", "Vistoria especial")


def test_assunto_da_lista_descarta_o_texto_livre(api):
    d = criar(api, assunto_tipo="Vistoria de Embargo", assunto_outro="sobra")
    assert d["assunto_outro"] is None


def test_trocar_de_outro_para_item_da_lista_limpa_o_texto(api):
    d = criar(api, assunto_tipo="Outro", assunto_outro="Texto")
    r = patch(api, d, assunto_tipo="Atendimento a Denúncia")
    assert (r.json()["assunto_tipo"], r.json()["assunto_outro"]) == ("Atendimento a Denúncia", None)


# ---------- equipe e atos ----------
def test_membro_sem_nome_e_tipo_de_ato_invalido_apontam_a_linha(api):
    c = erro(api.post(f"{BASE}/inspecoes", json=payload(equipe=[{"nome": "Ok"}, {"nome": "  "}])), 422, "VALIDACAO_CAMPO")
    assert c["detalhes"] == [{"campo": "equipe.1.nome", "mensagem": "Campo obrigatório."}]
    c = erro(api.post(f"{BASE}/inspecoes", json=payload(atos=[{"tipo": "Multa"}])), 422, "VALIDACAO_CAMPO")
    assert c["detalhes"][0]["campo"] == "atos.0.tipo"


def test_limites_de_texto_da_capa(api):
    erro(api.post(f"{BASE}/inspecoes", json=payload(interessado_orgao="x" * 121)), 422, "VALIDACAO_CAMPO")
    erro(api.post(f"{BASE}/inspecoes", json=payload(providencias_texto="x" * 2001)), 422, "VALIDACAO_CAMPO")
    erro(api.post(f"{BASE}/inspecoes", json=payload(atos=[{"tipo": "Notificação", "numero": "n" * 41}])), 422, "VALIDACAO_CAMPO")
    erro(api.post(f"{BASE}/inspecoes", json=payload(equipe=[{"nome": f"M{i}"} for i in range(21)])), 422, "VALIDACAO_CAMPO")


def test_editar_substitui_equipe_e_atos_em_aberta_e_em_andamento(api):
    d = criar(api, equipe=[{"nome": "A"}], atos=[{"tipo": "Notificação"}])
    r = patch(api, d, equipe=[{"nome": "B"}, {"nome": "C"}], atos=[], **MP)
    assert r.status_code == 200, r.text
    assert [m["nome"] for m in r.json()["equipe"]] == ["B", "C"] and r.json()["atos"] == []
    assert r.json()["interessado_unidade"] == MP["interessado_unidade"]
    # passa a Em andamento (registrando um item) e continua editável
    it = d["itens"][0]
    api.patch(f"{BASE}/inspecoes/{d['id']}", json={"data_agendamento": "2026-10-20"})
    assert api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{it['id']}", json={"situacao": "CONFORME"}).status_code == 200
    r = patch(api, d, equipe=[{"nome": "D"}], providencias_texto="Novo texto")
    assert r.status_code == 200, r.text
    assert (r.json()["status"], [m["nome"] for m in r.json()["equipe"]], r.json()["providencias_texto"]) == (
        "EM_ANDAMENTO", ["D"], "Novo texto")


def test_limpar_interessado_volta_a_nulo(api):
    d = criar(api, **MP)
    assert patch(api, d, interessado_orgao="  ").json()["interessado_orgao"] is None


# ---------- fechamento exige equipe ----------
def test_fechar_sem_equipe_e_bloqueado_com_detalhe_equipe(api):
    d = criar(api)
    responder_tudo(api, d)
    c = erro(api.post(f"{BASE}/inspecoes/{d['id']}/fechar"), 422, "FECHAMENTO_BLOQUEADO")
    assert c["detalhes"] == [{"campo": "equipe", "mensagem": "Informe ao menos um membro da equipe técnica."}]
    assert api.get(f"{BASE}/inspecoes/{d['id']}").json()["status"] == "EM_ANDAMENTO"  # nada foi gravado
    assert patch(api, d, equipe=[{"nome": "Analista Fictício"}]).status_code == 200
    assert api.post(f"{BASE}/inspecoes/{d['id']}/fechar").status_code == 200


def test_fechar_sem_equipe_e_com_item_pendente_lista_os_dois(api):
    d = criar(api)
    api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{d['itens'][0]['id']}", json={"situacao": "CONFORME"})
    campos = [x["campo"] for x in erro(api.post(f"{BASE}/inspecoes/{d['id']}/fechar"), 422, "FECHAMENTO_BLOQUEADO")["detalhes"]]
    assert "equipe" in campos and any(c.startswith("itens.") for c in campos)


# ---------- depois do fechamento: só o nº dos atos e o nº SEMA ----------
def test_apos_fechar_edita_numero_do_ato_e_numero_sema_e_registra_atualizado_em(api):
    d = finalizada(api, atos=[{"tipo": "Notificação"}, {"tipo": "Auto de Infração", "numero": "AI-1"}])
    atos = d["atos"]
    antes = d["atualizado_em"]
    r = patch(api, d, atos=[{"id": atos[0]["id"], "tipo": "Notificação", "numero": " NOT-0007/2030 "},
                            {"id": atos[1]["id"], "tipo": "Auto de Infração", "numero": "AI-1"}],
              numero_relatorio_sema="RT-0099/2030")
    assert r.status_code == 200, r.text
    novo = r.json()
    assert [(a["tipo"], a["numero"]) for a in novo["atos"]] == [("Notificação", "NOT-0007/2030"), ("Auto de Infração", "AI-1")]
    assert novo["numero_relatorio_sema"] == "RT-0099/2030"
    assert novo["status"] == "FINALIZADA" and novo["resultado"] == d["resultado"]
    assert novo["atualizado_em"] >= antes and novo["atualizado_em"] != antes  # a edição fica registrada


def test_apos_fechar_so_numero_sema_tambem_e_aceito_e_pode_ser_limpo(api):
    d = finalizada(api)
    assert patch(api, d, numero_relatorio_sema="X-1").json()["numero_relatorio_sema"] == "X-1"
    assert patch(api, d, numero_relatorio_sema="").json()["numero_relatorio_sema"] is None


@pytest.mark.parametrize("campo,valor", [
    ("objetivo", "Outro"), ("observacoes", "x"), ("providencias_texto", "x"), ("equipe", [{"nome": "Y"}]),
    ("interessado_orgao", "x"), ("assunto_tipo", "Atendimento a Denúncia"), ("numero_processo", "9/2030"),
])
def test_apos_fechar_nenhum_outro_campo_e_editavel(api, campo, valor):
    d = finalizada(api)
    erro(patch(api, d, **{campo: valor}), 409, "INSPECAO_IMUTAVEL")


def test_apos_fechar_misturar_campo_editavel_e_proibido_nao_grava_nada(api):
    d = finalizada(api)
    erro(patch(api, d, numero_relatorio_sema="A", objetivo="x"), 409, "INSPECAO_IMUTAVEL")
    assert api.get(f"{BASE}/inspecoes/{d['id']}").json()["numero_relatorio_sema"] is None


def test_apos_fechar_nao_muda_tipo_nem_quantidade_de_atos(api):
    d = finalizada(api, atos=[{"tipo": "Notificação"}])
    a = d["atos"][0]
    erro(patch(api, d, atos=[{"id": a["id"], "tipo": "Auto de Infração", "numero": "1"}]), 409, "CAMPO_NAO_EDITAVEL_NO_STATUS")
    erro(patch(api, d, atos=[]), 409, "CAMPO_NAO_EDITAVEL_NO_STATUS")
    erro(patch(api, d, atos=[{"id": a["id"], "tipo": "Notificação"}, {"tipo": "Notificação"}]), 409, "CAMPO_NAO_EDITAVEL_NO_STATUS")
    erro(patch(api, d, atos=[{"id": a["id"] + 999, "tipo": "Notificação"}]), 409, "CAMPO_NAO_EDITAVEL_NO_STATUS")
    assert api.get(f"{BASE}/inspecoes/{d['id']}").json()["atos"] == d["atos"]


def test_cancelada_continua_imutavel_inclusive_para_os_campos_novos(api):
    d = criar(api)
    api.post(f"{BASE}/inspecoes/{d['id']}/cancelar", json={"motivo": "x"})
    erro(patch(api, d, numero_relatorio_sema="A"), 409, "INSPECAO_IMUTAVEL")


def test_campos_editaveis_da_finalizada_sao_so_os_da_sema(api):
    d = finalizada(api)
    assert d["campos_editaveis"] == ["atos", "numero_relatorio_sema"]


# ---------- exemplos ----------
def test_exemplos_trazem_interessado_equipe_e_atos(api):
    dados = api.get(f"{BASE}/inspecoes", params={"tamanho": 100}).json()["dados"]
    por = {i["codigo"]: api.get(f"{BASE}/inspecoes/{i['id']}").json() for i in dados}
    assert por["INS-001"]["interessado_orgao"] == MP["interessado_orgao"] and len(por["INS-001"]["equipe"]) == 2
    assert por["INS-003"]["interessado_orgao"] is None  # demanda interna / de ofício
    assert [(a["tipo"], a["numero"]) for a in por["INS-002"]["atos"]] == [("Notificação", "NOT-0001/2026"), ("Auto de Infração", None)]
    assert all(p["equipe"] for p in por.values())  # as finalizadas respeitam a regra da equipe
