import csv
from io import StringIO

import pytest

from tests.fixtures import imagens

BASE = "/api/v1"
COLUNAS = ["codigo_inspecao", "numero_processo", "local", "status_inspecao", "resultado_inspecao", "item_numero",
           "item_descricao", "critico", "situacao", "observacao", "origem", "qtd_fotos"]
COLUNAS_CSV_DAS_INSPECOES = ["codigo", "numero_processo", "local", "latitude", "longitude", "data_agendamento",
                             "data_realizacao", "status", "resultado", "observacoes_vistoria", "qtd_fotos"]


def ler(c, caminho="itens.csv"):
    r = c.get(f"{BASE}/exportacao/{caminho}")
    assert r.status_code == 200, r.text
    texto = r.content.decode("utf-8-sig")
    linhas = list(csv.reader(StringIO(texto, newline=""), delimiter=";"))
    return r, linhas


def linhas_dict(linhas):
    return [dict(zip(linhas[0], l)) for l in linhas[1:]]


@pytest.fixture
def api(client, exemplos):
    return client


def por_codigo(api, codigo):
    return next(i for i in api.get(f"{BASE}/inspecoes", params={"tamanho": 100}).json()["dados"] if i["codigo"] == codigo)


# ---------- formato ----------
def test_cabecalhos_e_colunas_exatos(api):
    r, linhas = ler(api)
    assert r.headers["content-type"].startswith("text/csv")
    assert 'filename="itens-checklist.csv"' in r.headers["content-disposition"]
    assert r.content.startswith(b"\xef\xbb\xbf")  # BOM UTF-8 para o Excel
    assert linhas[0] == COLUNAS
    assert all(len(l) == len(COLUNAS) for l in linhas)  # nenhuma linha "estourou" o delimitador


def test_banco_vazio_so_cabecalho(client):
    _, linhas = ler(client)
    assert linhas == [COLUNAS]


# ---------- conteúdo ----------
def test_uma_linha_por_item_de_cada_inspecao(api):
    _, linhas = ler(api)
    dados = linhas_dict(linhas)
    assert len(dados) == 30  # 5 inspeções x 6 itens do modelo
    for codigo in ("INS-001", "INS-002", "INS-003", "INS-004", "INS-005"):
        itens = [d for d in dados if d["codigo_inspecao"] == codigo]
        assert [d["item_numero"] for d in itens] == ["1", "2", "3", "4", "5", "6"]
    ordem = [d["codigo_inspecao"] for d in dados]
    assert ordem == sorted(ordem)  # inspeções em ordem; itens na ordem do checklist


def test_total_de_linhas_bate_com_os_itens_da_api(api):
    total = 0
    for i in api.get(f"{BASE}/inspecoes", params={"tamanho": 100}).json()["dados"]:
        total += len(api.get(f"{BASE}/inspecoes/{i['id']}/itens").json())
    assert len(linhas_dict(ler(api)[1])) == total


def test_campos_da_inspecao_repetidos_em_cada_linha(api):
    dados = linhas_dict(ler(api)[1])
    ins1 = [d for d in dados if d["codigo_inspecao"] == "INS-001"]
    assert {(d["numero_processo"], d["local"], d["status_inspecao"], d["resultado_inspecao"]) for d in ins1} == {
        ("SEMA-PRO-2026/10001", "Fazenda Horizonte Azul", "FINALIZADA", "APROVADA")}
    ins5 = [d for d in dados if d["codigo_inspecao"] == "INS-005"]
    assert {(d["status_inspecao"], d["resultado_inspecao"]) for d in ins5} == {("ABERTA", "")}  # sem resultado antes de fechar


def test_item_critico_situacao_observacao_e_origem(api):
    dados = linhas_dict(ler(api)[1])
    ins3 = {d["item_numero"]: d for d in dados if d["codigo_inspecao"] == "INS-003"}
    assert [ins3[str(n)]["critico"] for n in range(1, 7)] == ["sim", "sim", "nao", "nao", "nao", "sim"]
    item6 = ins3["6"]
    assert item6["situacao"] == "NAO_CONFORME" and item6["resultado_inspecao"] == "REPROVADA"
    assert item6["observacao"].startswith("Caixa separadora com sinais de transbordamento")
    assert item6["item_descricao"] == "Destinação de efluentes regular" and item6["origem"] == "MODELO"
    assert ins3["1"]["situacao"] == "CONFORME" and ins3["1"]["observacao"] == ""
    ins4 = {d["item_numero"]: d for d in dados if d["codigo_inspecao"] == "INS-004"}
    assert ins4["4"]["situacao"] == "NAO_RESPONDIDO"  # itens ainda não respondidos também saem


def test_qtd_de_fotos_por_item(client):
    assert client.post(f"{BASE}/utilitarios/carregar-exemplos").status_code == 201  # a carga real inclui as 9 fotos
    dados = linhas_dict(ler(client)[1])
    fotos = {(d["codigo_inspecao"], d["item_numero"]): d["qtd_fotos"] for d in dados}
    assert fotos[("INS-002", "4")] == "1" and fotos[("INS-002", "5")] == "1"
    assert fotos[("INS-003", "6")] == "2"
    assert fotos[("INS-001", "1")] == "0"  # as fotos da INS-001 não têm vínculo com item
    assert sum(int(v) for v in fotos.values()) == 4  # só as 4 fotos vinculadas a algum item


def test_qtd_de_fotos_acompanha_envio_e_exclusao(api):
    i4 = api.get(f"{BASE}/inspecoes/{por_codigo(api, 'INS-004')['id']}").json()
    item1 = i4["itens"][0]["id"]
    r = api.post(f"{BASE}/inspecoes/{i4['id']}/fotos", files={"arquivo": ("a.jpg", imagens.jpeg(77), "image/jpeg")},
                 data={"anotacao": "vinculada ao item 1", "item_id": str(item1)})
    assert r.status_code == 201
    linha = next(d for d in linhas_dict(ler(api)[1]) if d["codigo_inspecao"] == "INS-004" and d["item_numero"] == "1")
    assert linha["qtd_fotos"] == "1"
    assert api.delete(f"{BASE}/inspecoes/{i4['id']}/fotos/{r.json()['id']}").status_code == 204
    linha = next(d for d in linhas_dict(ler(api)[1]) if d["codigo_inspecao"] == "INS-004" and d["item_numero"] == "1")
    assert linha["qtd_fotos"] == "0"


def test_item_avulso_sai_com_origem_avulso_e_proximo_numero(api):
    i4 = por_codigo(api, "INS-004")
    api.post(f"{BASE}/inspecoes/{i4['id']}/itens", json={"descricao": "Cerca perimetral", "critico": True})
    dados = [d for d in linhas_dict(ler(api)[1]) if d["codigo_inspecao"] == "INS-004"]
    assert len(dados) == 7
    avulso = dados[-1]
    assert (avulso["item_numero"], avulso["item_descricao"], avulso["origem"], avulso["critico"]) == ("7", "Cerca perimetral", "AVULSO", "sim")


def test_inspecao_cancelada_tambem_aparece(api):
    i5 = por_codigo(api, "INS-005")
    api.post(f"{BASE}/inspecoes/{i5['id']}/cancelar", json={"motivo": "teste"})
    dados = [d for d in linhas_dict(ler(api)[1]) if d["codigo_inspecao"] == "INS-005"]
    assert len(dados) == 6 and {d["status_inspecao"] for d in dados} == {"CANCELADA"}


# ---------- texto livre: aspas, ponto e vírgula, quebra de linha e fórmulas ----------
def test_texto_com_aspas_ponto_e_virgula_e_quebra_volta_identico(api):
    texto = 'Ele disse "ok"; depois\nsegunda linha, <script>x</script>'
    i4 = api.get(f"{BASE}/inspecoes/{por_codigo(api, 'INS-004')['id']}").json()
    item4 = next(i for i in i4["itens"] if i["ordem"] == 4)
    assert api.patch(f"{BASE}/inspecoes/{i4['id']}/itens/{item4['id']}", json={"observacao": texto}).status_code == 200
    _, linhas = ler(api)
    assert all(len(l) == len(COLUNAS) for l in linhas)
    linha = next(d for d in linhas_dict(linhas) if d["codigo_inspecao"] == "INS-004" and d["item_numero"] == "4")
    assert linha["observacao"] == texto  # o leitor de CSV recupera o texto exato


def test_texto_que_parece_formula_e_neutralizado(api):
    i4 = por_codigo(api, "INS-004")
    api.patch(f"{BASE}/inspecoes/{i4['id']}", json={"numero_processo": "@SOMA(A1)"})
    d = api.get(f"{BASE}/inspecoes/{i4['id']}").json()
    api.patch(f"{BASE}/inspecoes/{i4['id']}/itens/{d['itens'][3]['id']}", json={"observacao": "=HYPERLINK(\"http://x\")"})
    api.post(f"{BASE}/inspecoes/{i4['id']}/itens", json={"descricao": "+cmd|' /C calc'!A0"})
    dados = [x for x in linhas_dict(ler(api)[1]) if x["codigo_inspecao"] == "INS-004"]
    assert all(x["numero_processo"] == "'@SOMA(A1)" for x in dados)
    assert dados[3]["observacao"].startswith("'=")
    assert dados[-1]["item_descricao"].startswith("'+")


def test_numeros_e_codigos_nao_recebem_apostrofo(api):
    for d in linhas_dict(ler(api)[1]):
        assert d["item_numero"].isdigit() and d["qtd_fotos"].isdigit() and d["codigo_inspecao"].startswith("INS-")


# ---------- o CSV por inspeção continua exatamente como era ----------
def test_csv_por_inspecao_nao_mudou(api):
    r, linhas = ler(api, "inspecoes.csv")
    assert linhas[0] == COLUNAS_CSV_DAS_INSPECOES  # mesma lista de colunas de antes do B3
    assert len(linhas) == 6  # cabeçalho + 5 inspeções (uma linha por inspeção, não por item)
    assert 'filename="inspecoes.csv"' in r.headers["content-disposition"]
