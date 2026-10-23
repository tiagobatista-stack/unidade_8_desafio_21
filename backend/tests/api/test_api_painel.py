import csv
from io import StringIO

import pytest
from sqlalchemy import text

from app import config

BASE = "/api/v1"


def ind(c):
    d = c.get(f"{BASE}/indicadores").json()
    assert d["pendencias"] + d["finalizadas"] == d["inspecoes"]  # CA21: invariante
    return (d["inspecoes"], d["pendencias"], d["finalizadas"])


def por_codigo(c, codigo):
    return next(i for i in c.get(f"{BASE}/inspecoes", params={"tamanho": 100}).json()["dados"] if i["codigo"] == codigo)


@pytest.fixture
def com_exemplos(client):
    r = client.post(f"{BASE}/utilitarios/carregar-exemplos")
    assert r.status_code == 201, r.text
    return client


def ler_csv(c):
    r = c.get(f"{BASE}/exportacao/inspecoes.csv")
    assert r.status_code == 200
    texto = r.content.decode("utf-8-sig")
    return r, list(csv.reader(StringIO(texto, newline=""), delimiter=";"))


# ---------- indicadores e exemplos ----------
def test_banco_vazio_zerado(client):
    assert ind(client) == (0, 0, 0)


def test_exemplos_geram_5_2_3(com_exemplos):  # CA18
    assert ind(com_exemplos) == (5, 2, 3)
    assert com_exemplos.get(f"{BASE}/indicadores").json()["gerado_em"]


def test_numeros_batem_com_o_banco(com_exemplos, engine):  # critério S3
    with engine.connect() as con:
        linhas = dict(con.execute(text("SELECT status, COUNT(*) FROM inspecao GROUP BY status")).all())
    assert linhas == {"ABERTA": 1, "EM_ANDAMENTO": 1, "FINALIZADA": 3}
    assert ind(com_exemplos) == (5, 2, 3)


def test_segunda_carga_409_sem_duplicar(com_exemplos):
    r = com_exemplos.post(f"{BASE}/utilitarios/carregar-exemplos")
    assert r.status_code == 409 and r.json()["erro"]["codigo"] == "BANCO_JA_POVOADO"
    assert ind(com_exemplos) == (5, 2, 3)
    assert com_exemplos.get(f"{BASE}/locais").json()["total"] == 4


def test_exemplos_conteudo_completo(com_exemplos):  # CA24, CA25
    assert com_exemplos.get(f"{BASE}/locais").json()["total"] == 4
    resultados = {i["codigo"]: (i["status"], i["resultado"]) for i in com_exemplos.get(f"{BASE}/inspecoes").json()["dados"]}
    assert resultados == {
        "INS-001": ("FINALIZADA", "APROVADA"), "INS-002": ("FINALIZADA", "APROVADA_COM_RESSALVAS"),
        "INS-003": ("FINALIZADA", "REPROVADA"), "INS-004": ("EM_ANDAMENTO", None), "INS-005": ("ABERTA", None),
    }
    d2 = com_exemplos.get(f"{BASE}/inspecoes/{por_codigo(com_exemplos, 'INS-002')['id']}").json()
    assert d2["observacoes_vistoria"].startswith("Pátio com acúmulo moderado de serragem")
    assert len(d2["itens"]) == 6 and d2["resumo_itens"]["nao_conformes"] == 2
    d3 = com_exemplos.get(f"{BASE}/inspecoes/{por_codigo(com_exemplos, 'INS-003')['id']}").json()
    assert d3["resultado"] == "REPROVADA"
    assert [f["item_id"] for f in d3["fotos"]] == [next(i["id"] for i in d3["itens"] if i["ordem"] == 6)] * 2
    assert d3["fotos"][0]["anotacao"].startswith("Caixa separadora com sinais de transbordamento")
    d5 = com_exemplos.get(f"{BASE}/inspecoes/{por_codigo(com_exemplos, 'INS-005')['id']}").json()
    assert d5["observacoes_vistoria"] is None and d5["fotos"] == []


def test_nove_fotos_com_anotacoes_e_arquivos_consistentes(com_exemplos):  # CA24, CA58, CA60
    contagens = {i["codigo"]: i["qtd_fotos"] for i in com_exemplos.get(f"{BASE}/inspecoes").json()["dados"]}
    assert [contagens[f"INS-00{n}"] for n in (1, 2, 3, 4, 5)] == [3, 2, 2, 2, 0]
    todas = [f for i in range(1, 6) for f in com_exemplos.get(f"{BASE}/inspecoes/{i}/fotos").json()]
    assert len(todas) == 9 and all(f["anotacao"].strip() for f in todas)
    assert len([p for p in config.fotos_dir().rglob("*") if p.is_file()]) == 18
    assert com_exemplos.get(f"{BASE}/utilitarios/verificar-fotos").json()["total_inconsistencias"] == 0
    assert com_exemplos.get(todas[0]["url_miniatura"]).status_code == 200


def test_falha_na_carga_nao_deixa_lixo(client, monkeypatch):
    from app.seed import fotos_exemplo

    original = fotos_exemplo.gerar_imagem
    chamadas = []

    def falha_na_quinta(numero, n):
        chamadas.append(1)
        if len(chamadas) == 5:
            raise RuntimeError("falha simulada")
        return original(numero, n)

    monkeypatch.setattr(fotos_exemplo, "gerar_imagem", falha_na_quinta)
    from fastapi.testclient import TestClient

    from app.main import criar_app

    with TestClient(criar_app(), raise_server_exceptions=False) as c:
        assert c.post(f"{BASE}/utilitarios/carregar-exemplos").status_code == 500
        assert ind(c) == (0, 0, 0)
        assert c.get(f"{BASE}/locais").json()["total"] == 0
    assert [p for p in config.fotos_dir().rglob("*") if p.is_file()] == []
    monkeypatch.setattr(fotos_exemplo, "gerar_imagem", original)
    with TestClient(criar_app()) as c:  # depois da falha, a carga normal funciona
        assert c.post(f"{BASE}/utilitarios/carregar-exemplos").status_code == 201


def test_fechar_ins004_vai_para_1_4(com_exemplos):  # CA19
    d = com_exemplos.get(f"{BASE}/inspecoes/{por_codigo(com_exemplos, 'INS-004')['id']}").json()
    for it in d["itens"]:
        if it["situacao"] == "NAO_RESPONDIDO":
            assert com_exemplos.patch(f"{BASE}/inspecoes/{d['id']}/itens/{it['id']}", json={"situacao": "CONFORME"}).status_code == 200
    assert ind(com_exemplos) == (5, 2, 3)  # responder itens não altera os números
    assert com_exemplos.post(f"{BASE}/inspecoes/{d['id']}/fechar").status_code == 200
    assert ind(com_exemplos) == (5, 1, 4)


def test_cancelar_ins005_reduz_inspecoes_e_pendencias(com_exemplos):  # CA20
    i5 = por_codigo(com_exemplos, "INS-005")
    assert com_exemplos.post(f"{BASE}/inspecoes/{i5['id']}/cancelar", json={"motivo": "Sem acesso"}).status_code == 200
    assert ind(com_exemplos) == (4, 1, 3)


def test_cadastrar_nova_aumenta_inspecoes_e_pendencias(com_exemplos):
    corpo = {"numero_processo": "SEMA-PRO-2026/12345", "local_id": 1, "data_agendamento": "2026-10-30", "objetivo": "x"}
    assert com_exemplos.post(f"{BASE}/inspecoes", json=corpo).status_code == 201
    assert ind(com_exemplos) == (6, 3, 3)


# ---------- CSV ----------
COLUNAS = ["codigo", "numero_processo", "local", "latitude", "longitude", "data_agendamento", "data_realizacao",
           "status", "resultado", "observacoes_vistoria", "qtd_fotos"]


def por_coluna(linhas):
    """Linhas do CSV indexadas por código, cada uma como dicionário coluna -> valor."""
    assert len(linhas[0]) == len(COLUNAS)
    return {l[0]: dict(zip(linhas[0], l)) for l in linhas[1:]}


def test_csv_colunas_e_linhas(com_exemplos):  # CA23, CA28, CA58
    r, linhas = ler_csv(com_exemplos)
    assert r.headers["content-type"].startswith("text/csv")
    assert linhas[0] == COLUNAS
    corpo = por_coluna(linhas)
    assert len(corpo) == 5
    assert [corpo[f"INS-00{n}"]["qtd_fotos"] for n in (1, 2, 3, 4, 5)] == ["3", "2", "2", "2", "0"]
    assert [corpo[f"INS-00{n}"]["numero_processo"] for n in (1, 5)] == ["SEMA-PRO-2026/10001", "SEMA-PRO-2026/10005"]
    i1 = corpo["INS-001"]
    assert (i1["local"], i1["latitude"], i1["longitude"], i1["data_agendamento"], i1["data_realizacao"],
            i1["status"], i1["resultado"]) == ("Fazenda Horizonte Azul", "-10.42318", "-58.71264", "2026-10-05",
                                               "2026-10-06", "FINALIZADA", "APROVADA")
    i5 = corpo["INS-005"]
    assert i5["data_realizacao"] == "" and i5["resultado"] == "" and i5["observacoes_vistoria"] == ""


def test_csv_campos_especiais_aspas_ponto_e_virgula_quebra(com_exemplos):  # CA41
    texto = 'Ele disse "ok"; depois\nsegunda linha, com vírgula <script>x</script>'
    i5 = por_codigo(com_exemplos, "INS-005")
    assert com_exemplos.patch(f"{BASE}/inspecoes/{i5['id']}", json={"observacoes_vistoria": texto}).status_code == 200
    _, linhas = ler_csv(com_exemplos)
    ins5 = next(l for l in linhas if l[0] == "INS-005")
    assert len(ins5) == len(COLUNAS) and por_coluna(linhas)["INS-005"]["observacoes_vistoria"] == texto


def test_csv_neutraliza_formulas(com_exemplos):
    i5 = por_codigo(com_exemplos, "INS-005")
    com_exemplos.patch(f"{BASE}/inspecoes/{i5['id']}", json={"observacoes_vistoria": "=HYPERLINK(\"http://x\")"})
    com_exemplos.patch(f"{BASE}/inspecoes/{i5['id']}", json={"numero_processo": "=1+1"})
    _, linhas = ler_csv(com_exemplos)
    ins5 = por_coluna(linhas)["INS-005"]
    assert ins5["observacoes_vistoria"].startswith("'=") and ins5["numero_processo"] == "'=1+1"


def test_csv_banco_vazio_so_cabecalho(client):
    _, linhas = ler_csv(client)
    assert len(linhas) == 1
