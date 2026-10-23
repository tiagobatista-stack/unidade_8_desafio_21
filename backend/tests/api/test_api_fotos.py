from io import BytesIO

import pytest
from PIL import Image

from app import config
from tests.fixtures import imagens

BASE = "/api/v1"
EM_ANDAMENTO = 4  # INS-004
FINALIZADA = 1  # INS-001
ABERTA = 5  # INS-005


@pytest.fixture
def api(client, exemplos):
    return client


def erro(r, status, codigo):
    assert r.status_code == status, r.text
    corpo = r.json()["erro"]
    assert corpo["codigo"] == codigo, corpo
    return corpo


def enviar(api, insp, conteudo, anotacao="Anotação de teste", nome="foto.jpg", tipo="image/jpeg", **extra):
    dados = {"anotacao": anotacao} if anotacao is not None else {}
    dados.update({k: str(v) for k, v in extra.items()})
    return api.post(f"{BASE}/inspecoes/{insp}/fotos", files={"arquivo": (nome, conteudo, tipo)}, data=dados)


def arquivos_em_disco():
    base = config.fotos_dir()
    return sorted(p for p in base.rglob("*") if p.is_file()) if base.exists() else []


def itens_de(api, insp):
    return api.get(f"{BASE}/inspecoes/{insp}").json()["itens"]


# ---------- envio ----------
def test_envio_jpeg_cria_registro_original_e_miniatura(api):  # CA42, CA57
    r = enviar(api, EM_ANDAMENTO, imagens.jpeg(tamanho=(800, 600)))
    assert r.status_code == 201, r.text
    f = r.json()
    assert f["mime_type"] == "image/jpeg" and (f["largura"], f["altura"]) == (800, 600)
    assert f["anotacao"] == "Anotação de teste" and f["ordem"] == 1
    assert len(arquivos_em_disco()) == 2
    mini = api.get(f["url_miniatura"])
    orig = api.get(f["url_original"])
    assert mini.status_code == 200 and mini.headers["content-type"] == "image/jpeg"
    assert mini.headers["x-content-type-options"] == "nosniff"
    assert max(Image.open(BytesIO(mini.content)).size) == 320
    assert Image.open(BytesIO(orig.content)).size == (800, 600)


@pytest.mark.parametrize("fn,mime", [(imagens.png, "image/png"), (imagens.webp, "image/webp")])
def test_envio_png_e_webp(api, fn, mime):  # CA43
    r = enviar(api, EM_ANDAMENTO, fn(), nome="x", tipo="application/octet-stream")
    assert r.status_code == 201 and r.json()["mime_type"] == mime


def test_gif_415_e_nada_em_disco(api):  # CA44
    erro(enviar(api, EM_ANDAMENTO, imagens.gif(), nome="a.gif", tipo="image/gif"), 415, "FOTO_FORMATO_INVALIDO")
    assert arquivos_em_disco() == []


def test_texto_renomeado_jpg_415(api):  # CA45
    erro(enviar(api, EM_ANDAMENTO, imagens.texto_renomeado(), nome="a.jpg", tipo="image/jpeg"), 415, "FOTO_FORMATO_INVALIDO")
    assert arquivos_em_disco() == []


def test_arquivo_vazio_415(api):
    erro(enviar(api, EM_ANDAMENTO, b"", nome="vazio.jpg"), 415, "FOTO_FORMATO_INVALIDO")


def test_sem_arquivo_422(api):
    r = api.post(f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos", data={"anotacao": "x"})
    corpo = erro(r, 422, "VALIDACAO_CAMPO")
    assert corpo["detalhes"][0]["campo"] == "arquivo"


def test_limite_de_5mb(api):  # CA46
    assert enviar(api, EM_ANDAMENTO, imagens.jpeg_com_tamanho(5_242_880)).status_code == 201
    erro(enviar(api, EM_ANDAMENTO, imagens.jpeg_com_tamanho(5_242_881, i=2)), 413, "FOTO_TAMANHO_EXCEDIDO")
    assert len(arquivos_em_disco()) == 2  # só a primeira foi gravada


def test_limite_de_20_fotos(api):  # CA47
    for i in range(1, 21):
        assert enviar(api, EM_ANDAMENTO, imagens.jpeg(i), anotacao=f"foto {i}").status_code == 201
    erro(enviar(api, EM_ANDAMENTO, imagens.jpeg(99)), 409, "LIMITE_FOTOS_EXCEDIDO")
    assert len(arquivos_em_disco()) == 40


def test_duplicada_409_mas_outra_inspecao_aceita(api):  # CA48
    img = imagens.jpeg(7)
    assert enviar(api, EM_ANDAMENTO, img).status_code == 201
    erro(enviar(api, EM_ANDAMENTO, img), 409, "FOTO_DUPLICADA")
    assert len(arquivos_em_disco()) == 2
    assert enviar(api, ABERTA, img).status_code == 201


@pytest.mark.parametrize("fn", [imagens.jpeg_com_exif, imagens.png_com_exif, imagens.webp_com_exif])
def test_exif_gps_ausente_nos_arquivos_gravados(api, fn):  # CA49
    assert enviar(api, EM_ANDAMENTO, fn()).status_code == 201
    arquivos = arquivos_em_disco()
    assert len(arquivos) == 2
    for p in arquivos:
        img = Image.open(p)
        assert not dict(img.getexif()) and not img.getexif().get_ifd(0x8825)
        assert b"Fabricante" not in p.read_bytes()


def test_foto_em_aberta_nao_muda_status(api):  # CA50
    assert enviar(api, ABERTA, imagens.jpeg(3)).status_code == 201
    assert api.get(f"{BASE}/inspecoes/{ABERTA}").json()["status"] == "ABERTA"


def test_finalizada_e_cancelada_imutaveis_mas_consultaveis(api):  # CA51, P6
    erro(enviar(api, FINALIZADA, imagens.jpeg(4)), 409, "INSPECAO_IMUTAVEL")
    # cancelada com foto prévia: a consulta continua funcionando
    f = enviar(api, ABERTA, imagens.jpeg(5)).json()
    assert api.post(f"{BASE}/inspecoes/{ABERTA}/cancelar", json={"motivo": "Sem acesso"}).status_code == 200
    erro(enviar(api, ABERTA, imagens.jpeg(6)), 409, "INSPECAO_IMUTAVEL")
    erro(api.patch(f"{BASE}/inspecoes/{ABERTA}/fotos/{f['id']}", json={"anotacao": "x"}), 409, "INSPECAO_IMUTAVEL")
    erro(api.delete(f"{BASE}/inspecoes/{ABERTA}/fotos/{f['id']}"), 409, "INSPECAO_IMUTAVEL")
    assert len(api.get(f"{BASE}/inspecoes/{ABERTA}/fotos").json()) == 1
    assert api.get(f["url_miniatura"]).status_code == 200


def test_item_de_outra_inspecao_422(api):  # CA52
    outro = itens_de(api, FINALIZADA)[0]["id"]
    erro(enviar(api, EM_ANDAMENTO, imagens.jpeg(8), item_id=outro), 422, "ITEM_NAO_PERTENCE_A_INSPECAO")
    assert arquivos_em_disco() == []


def test_remover_item_avulso_mantem_foto_sem_vinculo(api):  # CA53
    av = api.post(f"{BASE}/inspecoes/{EM_ANDAMENTO}/itens", json={"descricao": "Cerca"}).json()
    f = enviar(api, EM_ANDAMENTO, imagens.jpeg(9), item_id=av["id"]).json()
    assert f["item_id"] == av["id"]
    det = api.get(f"{BASE}/inspecoes/{EM_ANDAMENTO}").json()
    assert next(i for i in det["itens"] if i["id"] == av["id"])["qtd_fotos"] == 1
    assert api.delete(f"{BASE}/inspecoes/{EM_ANDAMENTO}/itens/{av['id']}").status_code == 204
    depois = api.get(f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos/{f['id']}").json()
    assert depois["item_id"] is None
    assert api.get(depois["url_miniatura"]).status_code == 200


def test_legenda_limites(api):  # CA54
    assert enviar(api, EM_ANDAMENTO, imagens.jpeg(10), legenda="l" * 200).status_code == 201
    erro(enviar(api, EM_ANDAMENTO, imagens.jpeg(11), legenda="l" * 201), 422, "VALIDACAO_CAMPO")


def test_excluir_remove_registro_e_arquivos_e_anotacao(api):  # CA55, CA73
    f = enviar(api, EM_ANDAMENTO, imagens.jpeg(12)).json()
    assert len(arquivos_em_disco()) == 2
    assert api.delete(f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos/{f['id']}").status_code == 204
    assert arquivos_em_disco() == []
    erro(api.get(f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos/{f['id']}"), 404, "NAO_ENCONTRADO")
    assert api.get(f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos").json() == []
    erro(api.delete(f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos/{f['id']}"), 404, "NAO_ENCONTRADO")


def test_fotos_persistem_no_banco(api, engine):  # CA56
    f = enviar(api, EM_ANDAMENTO, imagens.jpeg(13), anotacao="Persistida").json()
    from sqlalchemy.orm import Session

    from app.models import FotoVistoria

    with Session(engine) as nova_sessao:
        reg = nova_sessao.get(FotoVistoria, f["id"])
        assert reg.anotacao == "Persistida" and reg.arquivo_path in {p.relative_to(config.fotos_dir()).as_posix() for p in arquivos_em_disco()}


def test_lista_mostra_qtd_fotos_e_detalhe_traz_fotos(api):  # CA58 (parcial)
    for i in (1, 2):
        enviar(api, EM_ANDAMENTO, imagens.jpeg(20 + i))
    enviar(api, ABERTA, imagens.jpeg(30))
    lista = {i["codigo"]: i["qtd_fotos"] for i in api.get(f"{BASE}/inspecoes").json()["dados"]}
    assert lista["INS-004"] == 2 and lista["INS-005"] == 1 and lista["INS-001"] == 0
    det = api.get(f"{BASE}/inspecoes/{EM_ANDAMENTO}").json()
    assert len(det["fotos"]) == 2 and det["fotos"][0]["url_miniatura"].endswith("versao=miniatura")


def test_fechar_sem_fotos_permitido(api):  # CA59
    d = api.post(f"{BASE}/inspecoes", json={"numero_processo": "SEMA-PRO-2026/12345", "local_id": 1, "data_agendamento": "2026-10-20", "objetivo": "x"}).json()
    for it in d["itens"]:
        api.patch(f"{BASE}/inspecoes/{d['id']}/itens/{it['id']}", json={"situacao": "CONFORME"})
    assert api.post(f"{BASE}/inspecoes/{d['id']}/fechar").status_code == 200


# ---------- anotação ----------
def test_sem_anotacao_422_e_nada_gravado(api):  # CA61
    erro(enviar(api, EM_ANDAMENTO, imagens.jpeg(14), anotacao=None), 422, "VALIDACAO_CAMPO")
    assert arquivos_em_disco() == []
    assert api.get(f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos").json() == []


def test_anotacao_so_espacos_422(api):  # CA62
    corpo = erro(enviar(api, EM_ANDAMENTO, imagens.jpeg(15), anotacao="   \n  "), 422, "VALIDACAO_CAMPO")
    assert corpo["detalhes"][0]["campo"] == "anotacao" and arquivos_em_disco() == []


def test_anotacao_limites_e_trim(api):  # CA63, CA64, CA65
    assert enviar(api, EM_ANDAMENTO, imagens.jpeg(16), anotacao="a" * 1000).status_code == 201
    erro(enviar(api, EM_ANDAMENTO, imagens.jpeg(17), anotacao="a" * 1001), 422, "VALIDACAO_CAMPO")
    assert enviar(api, EM_ANDAMENTO, imagens.jpeg(18), anotacao="x").status_code == 201
    r = enviar(api, EM_ANDAMENTO, imagens.jpeg(19), anotacao="  com bordas \n")
    assert r.json()["anotacao"] == "com bordas"


def test_edicao_de_anotacao_persiste_e_vazio_e_rejeitado(api):  # CA66, CA67
    f = enviar(api, EM_ANDAMENTO, imagens.jpeg(40), anotacao="Original").json()
    url = f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos/{f['id']}"
    assert api.patch(url, json={"anotacao": "Editada", "legenda": "Leg"}).json()["anotacao"] == "Editada"
    assert api.get(url).json()["anotacao"] == "Editada"
    erro(api.patch(url, json={"anotacao": "  "}), 422, "VALIDACAO_CAMPO")
    erro(api.patch(url, json={"anotacao": None}), 422, "VALIDACAO_CAMPO")
    assert api.get(url).json()["anotacao"] == "Editada"  # texto anterior mantido


def test_patch_item_ordem_e_validacoes(api):
    f = enviar(api, EM_ANDAMENTO, imagens.jpeg(41)).json()
    url = f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos/{f['id']}"
    item = itens_de(api, EM_ANDAMENTO)[0]["id"]
    r = api.patch(url, json={"item_id": item, "ordem": 3})
    assert r.json()["item_id"] == item and r.json()["ordem"] == 3
    assert api.patch(url, json={"item_id": None}).json()["item_id"] is None
    erro(api.patch(url, json={"item_id": itens_de(api, FINALIZADA)[0]["id"]}), 422, "ITEM_NAO_PERTENCE_A_INSPECAO")
    erro(api.patch(url, json={"ordem": 0}), 422, "VALIDACAO_CAMPO")


def test_texto_html_e_nome_com_script_guardados_literalmente(api):  # CA71 (backend)
    texto = "<script>alert(1)</script>\nlinha dois"
    f = enviar(api, EM_ANDAMENTO, imagens.jpeg(42), anotacao=texto, nome="<img src=x onerror=alert(1)>ç.jpg").json()
    assert f["anotacao"] == texto and f["nome_original"] == "<img src=x onerror=alert(1)>ç.jpg"


def test_nome_com_caminho_nunca_vira_caminho_em_disco(api):
    f = enviar(api, EM_ANDAMENTO, imagens.jpeg(43), nome="../../../etc/passwd.jpg").json()
    assert f["nome_original"] == "passwd.jpg"
    base = config.fotos_dir().resolve()
    assert all(base in p.resolve().parents for p in arquivos_em_disco())


def test_anotacao_nao_altera_resultado(api):  # CA72
    antes = api.get(f"{BASE}/inspecoes/3").json()
    assert antes["resultado"] == "REPROVADA"
    novo = api.post(f"{BASE}/inspecoes", json={"numero_processo": "SEMA-PRO-2026/12345", "local_id": 1, "data_agendamento": "2026-10-20", "objetivo": "x"}).json()
    for it in novo["itens"]:
        sit = "NAO_CONFORME" if it["ordem"] == 6 else "CONFORME"
        body = {"situacao": sit, **({"observacao": "irregular"} if sit == "NAO_CONFORME" else {})}
        api.patch(f"{BASE}/inspecoes/{novo['id']}/itens/{it['id']}", json=body)
    enviar(api, novo["id"], imagens.jpeg(50), anotacao="Tudo parece ótimo")
    assert api.post(f"{BASE}/inspecoes/{novo['id']}/fechar").json()["resultado"] == "REPROVADA"


def test_404_inspecao_e_foto_inexistentes(api):
    erro(enviar(api, 999, imagens.jpeg(1)), 404, "NAO_ENCONTRADO")
    erro(api.get(f"{BASE}/inspecoes/999/fotos"), 404, "NAO_ENCONTRADO")
    erro(api.get(f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos/999/arquivo"), 404, "NAO_ENCONTRADO")


def test_foto_de_outra_inspecao_nao_e_acessivel_pela_url_errada(api):
    f = enviar(api, EM_ANDAMENTO, imagens.jpeg(44)).json()
    erro(api.get(f"{BASE}/inspecoes/{ABERTA}/fotos/{f['id']}"), 404, "NAO_ENCONTRADO")


def test_versao_invalida_422(api):
    f = enviar(api, EM_ANDAMENTO, imagens.jpeg(45)).json()
    erro(api.get(f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos/{f['id']}/arquivo?versao=../x"), 422, "VALIDACAO_CAMPO")


# ---------- consistência (RN28) ----------
def test_verificar_fotos_banco_limpo_zero(api):  # CA60
    assert api.get(f"{BASE}/utilitarios/verificar-fotos").json()["total_inconsistencias"] == 0
    enviar(api, EM_ANDAMENTO, imagens.jpeg(46))
    assert api.get(f"{BASE}/utilitarios/verificar-fotos").json()["total_inconsistencias"] == 0


def test_verificar_fotos_acusa_arquivo_apagado_e_solto(api):  # CA60
    f = enviar(api, EM_ANDAMENTO, imagens.jpeg(47)).json()
    base = config.fotos_dir()
    original = next(p for p in arquivos_em_disco() if "original" in p.parts)
    original.unlink()
    solto = base / "99" / "original" / "solto.jpg"
    solto.parent.mkdir(parents=True)
    solto.write_bytes(b"x")
    rel = api.get(f"{BASE}/utilitarios/verificar-fotos").json()
    assert rel["total_inconsistencias"] == 2
    assert len(rel["registros_sem_arquivo"]) == 1 and rel["arquivos_sem_registro"] == ["99/original/solto.jpg"]
    erro(api.get(f["url_original"]), 404, "FOTO_ARQUIVO_AUSENTE")


def test_falha_ao_gravar_registro_remove_arquivos_gravados(api, monkeypatch):  # RN28
    from sqlalchemy.orm import Session

    def falha(self, *a, **k):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(Session, "commit", falha)
    from fastapi.testclient import TestClient

    from app.main import criar_app

    with TestClient(criar_app(), raise_server_exceptions=False) as c:
        r = c.post(
            f"{BASE}/inspecoes/{EM_ANDAMENTO}/fotos",
            files={"arquivo": ("a.jpg", imagens.jpeg(60), "image/jpeg")},
            data={"anotacao": "x"},
        )
    assert r.status_code == 500 and r.json()["erro"]["codigo"] == "ERRO_INTERNO"
    assert arquivos_em_disco() == []
