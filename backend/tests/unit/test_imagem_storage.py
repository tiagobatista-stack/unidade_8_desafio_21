from io import BytesIO

import pytest
from PIL import Image

from app.domain import imagem
from app.errors import ErroNegocio
from app.storage.arquivos import ArmazenamentoDisco
from tests.fixtures import imagens


def abrir(b: bytes) -> Image.Image:
    return Image.open(BytesIO(b))


@pytest.mark.parametrize("fn,mime", [(imagens.jpeg, "image/jpeg"), (imagens.png, "image/png"), (imagens.webp, "image/webp")])
def test_formatos_aceitos(fn, mime):  # CA42, CA43
    p = imagem.processar(fn())
    assert p.mime_type == mime and p.largura > 0 and len(p.hash_sha256) == 64


def test_gif_rejeitado_por_conteudo():  # CA44
    with pytest.raises(ErroNegocio) as e:
        imagem.processar(imagens.gif())
    assert e.value.codigo == "FOTO_FORMATO_INVALIDO" and e.value.status == 415


def test_texto_renomeado_rejeitado():  # CA45
    with pytest.raises(ErroNegocio) as e:
        imagem.processar(imagens.texto_renomeado())
    assert e.value.status == 415


def test_arquivo_vazio_e_corrompido_rejeitados():
    for conteudo in (b"", b"\xff\xd8\xff\xe0 truncado"):
        with pytest.raises(ErroNegocio) as e:
            imagem.processar(conteudo)
        assert e.value.status == 415


def test_limite_de_tamanho():  # CA46
    imagem.processar(imagens.jpeg_com_tamanho(5_242_880))
    with pytest.raises(ErroNegocio) as e:
        imagem.processar(imagens.jpeg_com_tamanho(5_242_881))
    assert e.value.codigo == "FOTO_TAMANHO_EXCEDIDO" and e.value.status == 413


@pytest.mark.parametrize("fn", [imagens.jpeg_com_exif, imagens.png_com_exif, imagens.webp_com_exif])
def test_exif_e_gps_removidos_do_original_e_da_miniatura(fn):  # CA49
    bruto = fn()
    if fn is imagens.jpeg_com_exif:
        assert abrir(bruto).getexif().get_ifd(0x8825)  # a entrada realmente tinha GPS
    p = imagem.processar(bruto)
    for saida in (p.original, p.miniatura):
        img = abrir(saida)
        assert not dict(img.getexif()) and not img.getexif().get_ifd(0x8825)
        assert b"Exif" not in saida[:64] and b"Fabricante" not in saida


def test_miniatura_ate_320_e_original_integro():  # CA57
    p = imagem.processar(imagens.jpeg(tamanho=(800, 600)))
    assert max(abrir(p.miniatura).size) == 320
    assert abrir(p.original).size == (800, 600) and (p.largura, p.altura) == (800, 600)


def test_miniatura_nao_amplia_imagem_pequena():
    p = imagem.processar(imagens.png(tamanho=(100, 50)))
    assert abrir(p.miniatura).size == (100, 50)


def test_hash_estavel_e_distinto():  # base de CA48
    assert imagem.hash_sha256(imagens.jpeg(1)) == imagem.hash_sha256(imagens.jpeg(1))
    assert imagem.hash_sha256(imagens.jpeg(1)) != imagem.hash_sha256(imagens.jpeg(2))


# ---------- storage ----------
def test_storage_salvar_ler_remover(tmp_path):
    st = ArmazenamentoDisco(tmp_path)
    c = st.salvar(7, "original", "jpg", b"abc")
    assert c.startswith("7/original/") and c.endswith(".jpg")
    assert st.existe(c) and st.ler(c) == b"abc" and st.listar() == [c]
    st.remover(c)
    assert not st.existe(c) and st.ler(c) is None
    st.remover(c)  # idempotente


def test_storage_bloqueia_caminho_fora_da_base(tmp_path):
    st = ArmazenamentoDisco(tmp_path / "fotos")
    with pytest.raises(ValueError):
        st.ler("../segredo.txt")
    with pytest.raises(ValueError):
        st.remover("../../x")
