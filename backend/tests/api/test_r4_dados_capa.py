"""R4/E4: dados para a capa da SEMA e para a lavratura, prontos para copiar."""
import pytest

BASE = "/api/v1"

INS001 = """1 – Interessado:
Ministério Público do Estado de Mato Grosso - 1ª Promotoria de Justiça Cível
Comarca de Juína
Protocolo nº SEMA-PRO-2026/10001
Requerente: Promotor de Justiça

2 – Assunto:
Vistoria de Constatação – Fiscalização Ambiental
Objetivo: Vistoria de rotina (exemplo fictício)

3 – Caracterização do empreendimento:
Nome fantasia: Fazenda Horizonte Azul
Responsável 1: Proprietário Fictício Um
CPF: 529.982.247-25
Responsável 2: Proprietária Fictícia Dois
CPF/CNPJ: Não informado
CAR: MT-5107925-00000000000000000000000000000001
Coordenadas: LAT 10° 25' 23" S | LONG 58° 42' 46" W
Endereço: Zona Rural, aos fundos da Fazenda Horizonte Azul, Vila Nova do Cerrado/MT
CEP: 78.320-000

4 – Equipe técnica:
Analista Fictício Um – Engenheiro Florestal – SEMA-MT / Superintendência de Fiscalização
Analista Fictícia Dois – Técnica Ambiental – SEMA-MT / Superintendência de Fiscalização

Atos a lavrar:
Nenhum ato informado.
Protocolo nº: SEMA-PRO-2026/10001
Empreendimento: Fazenda Horizonte Azul
Coordenadas: LAT 10° 25' 23" S | LONG 58° 42' 46" W
CAR: MT-5107925-00000000000000000000000000000001
Responsável 1: Proprietário Fictício Um
CPF: 529.982.247-25
Telefone: (65) 90000-0001
Endereço para correspondência: Rua das Palmeiras, 123, Sala 2, Centro, Vila Nova do Cerrado/MT – CEP 78.320-010
Responsável 2: Proprietária Fictícia Dois
CPF/CNPJ: Não informado
Telefone: (65) 90000-0002
Endereço para correspondência: Zona Rural, aos fundos da Fazenda Horizonte Azul, Vila Nova do Cerrado/MT – CEP 78.320-000"""

INS003 = """1 – Interessado:
Demanda interna / de ofício
Protocolo nº SEMA-PRO-2026/10003

2 – Assunto:
Vistoria de Constatação – Fiscalização Ambiental
Objetivo: Vistoria de rotina (exemplo fictício)

3 – Caracterização do empreendimento:
Nome fantasia: Posto Rio Claro
Responsável: Não informado
CPF/CNPJ: Não informado
CAR: Não informado
Coordenadas: LAT 9° 42' 44" S | LONG 58° 07' 42" W
Endereço: Avenida Principal, s/n, Centro, São Tomé do Norte/MT
CEP: 78.320-002

4 – Equipe técnica:
Analista Fictício Um – Engenheiro Florestal – SEMA-MT / Superintendência de Fiscalização

Atos a lavrar:
Ato 1: Notificação (nº a definir)
Protocolo nº: SEMA-PRO-2026/10003
Empreendimento: Posto Rio Claro
Coordenadas: LAT 9° 42' 44" S | LONG 58° 07' 42" W
CAR: Não informado
Responsável: Não informado"""


@pytest.fixture
def api(client, exemplos):
    return client


def capa(api, codigo):
    dados = api.get(f"{BASE}/inspecoes", params={"tamanho": 100}).json()["dados"]
    i = next(x for x in dados if x["codigo"] == codigo)
    r = api.get(f"{BASE}/inspecoes/{i['id']}/dados-capa")
    assert r.status_code == 200, r.text
    return i["id"], r.json()


def campo(bloco, rotulo):
    return next(c for c in bloco["campos"] if c["rotulo"] == rotulo)


def test_copiar_tudo_do_seed_bate_exatamente_com_o_esperado(api):
    assert capa(api, "INS-001")[1]["texto_completo"] == INS001
    assert capa(api, "INS-003")[1]["texto_completo"] == INS003


def test_blocos_na_ordem_da_capa_mais_atos_a_lavrar(api):
    d = capa(api, "INS-001")[1]
    assert [b["chave"] for b in d["blocos"]] == ["interessado", "assunto", "empreendimento", "equipe", "atos"]
    assert [b["titulo"] for b in d["blocos"]] == [
        "1 – Interessado", "2 – Assunto", "3 – Caracterização do empreendimento", "4 – Equipe técnica", "Atos a lavrar"]
    assert d["texto_completo"] == "\n\n".join(b["texto"] for b in d["blocos"])
    assert all(b["texto"].startswith(b["titulo"] + ":\n") for b in d["blocos"])


def test_o_exemplo_do_modelo_bloco_interessado(api):
    iid, _ = capa(api, "INS-005")
    api.patch(f"{BASE}/inspecoes/{iid}", json={
        "numero_processo": "212345/2030", "interessado_orgao": "Ministério Público do Estado de Mato Grosso",
        "interessado_unidade": "1ª Promotoria de Justiça Cível", "interessado_comarca": "Comarca de Juína",
        "interessado_requerente": "Promotor de Justiça"})
    bloco = api.get(f"{BASE}/inspecoes/{iid}/dados-capa").json()["blocos"][0]
    assert bloco["texto"] == (
        "1 – Interessado:\nMinistério Público do Estado de Mato Grosso - 1ª Promotoria de Justiça Cível\n"
        "Comarca de Juína\nProtocolo nº 212345/2030\nRequerente: Promotor de Justiça")


def test_campo_vazio_aparece_como_nao_informado_e_marcado_como_faltando(api):
    d = capa(api, "INS-001")[1]
    cpf2 = campo(d["blocos"][2], "Responsável 2 – CPF/CNPJ")
    assert cpf2 == {"rotulo": "Responsável 2 – CPF/CNPJ", "valor": "Não informado", "copiar": "", "ausente": True, "faltando": True}
    assert d["campos_faltando"] == 2  # o CPF/CNPJ do 2º responsável, no bloco 3 e no de atos
    ok = campo(d["blocos"][2], "Responsável 1 – CPF/CNPJ")
    assert (ok["valor"], ok["copiar"], ok["faltando"]) == ("529.982.247-25", "529.982.247-25", False)


def test_comarca_e_opcional_ausente_mas_nao_faltando(api):
    # inspeção com interessado e sem comarca
    r = api.post(f"{BASE}/inspecoes", json={
        "numero_processo": "P-9", "local_id": 1, "data_agendamento": "2026-10-28", "objetivo": "x",
        "interessado_orgao": "Órgão Fictício", "interessado_unidade": "Unidade Fictícia", "interessado_requerente": "Requerente Fictício"})
    novo = api.get(f"{BASE}/inspecoes/{r.json()['id']}/dados-capa").json()["blocos"][0]
    comarca = campo(novo, "Comarca")
    assert (comarca["ausente"], comarca["faltando"], comarca["valor"]) == (True, False, "Não informado")
    assert novo["texto"] == "1 – Interessado:\nÓrgão Fictício - Unidade Fictícia\nProtocolo nº P-9\nRequerente: Requerente Fictício"  # sem linha de comarca


def test_interessado_parcial_destaca_o_que_falta(api):
    r = api.post(f"{BASE}/inspecoes", json={
        "numero_processo": "P-9", "local_id": 1, "data_agendamento": "2026-10-28", "objetivo": "x", "interessado_orgao": "Órgão Fictício"})
    bloco = api.get(f"{BASE}/inspecoes/{r.json()['id']}/dados-capa").json()["blocos"][0]
    assert campo(bloco, "Unidade")["faltando"] and campo(bloco, "Requerente")["faltando"]
    assert bloco["texto"].endswith("Requerente: Não informado")


def test_demanda_interna_nao_tem_campos_faltando_no_interessado(api):
    bloco = capa(api, "INS-003")[1]["blocos"][0]
    assert [c["rotulo"] for c in bloco["campos"]] == ["Interessado", "Protocolo nº"]
    assert not any(c["faltando"] for c in bloco["campos"])


def test_assunto_outro_usa_o_texto_livre(api):
    r = api.post(f"{BASE}/inspecoes", json={
        "numero_processo": "P-9", "local_id": 1, "data_agendamento": "2026-10-28", "objetivo": "Objetivo X",
        "assunto_tipo": "Outro", "assunto_outro": "Vistoria especial"})
    bloco = api.get(f"{BASE}/inspecoes/{r.json()['id']}/dados-capa").json()["blocos"][1]
    assert bloco["texto"] == "2 – Assunto:\nVistoria especial\nObjetivo: Objetivo X"


def test_ato_com_numero_registrado_depois_do_fechamento_aparece_na_capa(api):
    iid, d = capa(api, "INS-003")
    ato = api.get(f"{BASE}/inspecoes/{iid}").json()["atos"][0]
    assert api.patch(f"{BASE}/inspecoes/{iid}", json={"atos": [{"id": ato["id"], "tipo": "Notificação", "numero": "NOT-0007/2026"}]}).status_code == 200
    novo = api.get(f"{BASE}/inspecoes/{iid}/dados-capa").json()
    assert "Ato 1: Notificação (nº NOT-0007/2026)" in novo["blocos"][4]["texto"]
    assert campo(novo["blocos"][4], "Ato 1")["valor"] == "Notificação – NOT-0007/2026"


def test_finalizada_usa_a_copia_do_empreendimento_do_fechamento(api):
    iid, antes = capa(api, "INS-001")
    api.put(f"{BASE}/locais/1", json={"nome": "Fazenda Horizonte Azul", "municipio": "Vila Nova do Cerrado", "tipo": "Propriedade rural",
                                      "latitude": -10.42318, "longitude": -58.71264, "logradouro": "OUTRO ENDEREÇO", "cep": "78999999"})
    assert capa(api, "INS-001")[1]["texto_completo"] == antes["texto_completo"]


def test_inspecao_sem_nada_novo_nao_quebra(api):
    r = api.post(f"{BASE}/inspecoes", json={"numero_processo": "P-0", "local_id": 3, "data_agendamento": "2026-10-28", "objetivo": "x"})
    d = api.get(f"{BASE}/inspecoes/{r.json()['id']}/dados-capa").json()
    assert d["blocos"][3]["texto"] == "4 – Equipe técnica:\nNão informado"
    assert campo(d["blocos"][3], "Equipe técnica")["faltando"]
    assert d["campos_faltando"] > 0


def test_inspecao_inexistente_404(api):
    r = api.get(f"{BASE}/inspecoes/9999/dados-capa")
    assert r.status_code == 404 and r.json()["erro"]["codigo"] == "NAO_ENCONTRADO"
