from io import BytesIO

from PIL import Image

from app.domain import imagem
from app.seed import fotos_exemplo as fx


def test_texto_com_e_sem_acentos():
    assert fx.texto_da_foto(4, 1, True) == "FOTO FICTÍCIA — INS-004 #1"
    assert fx.texto_da_foto(4, 1, False) == "FOTO FICTICIA - INS-004 #1"


def test_sem_fonte_truetype_usa_a_padrao_e_texto_sem_acentos():
    fonte, acentos = fx.carregar_fonte(candidatas=["/nao/existe.ttf", "C:/nao/existe.ttf"])
    assert acentos is False and fonte is not None


def test_fonte_truetype_do_sistema_aceita_os_glifos_do_texto():
    fonte, acentos = fx.carregar_fonte()
    if not acentos:  # máquina sem nenhuma das fontes candidatas: o fallback ASCII já foi testado acima
        return
    for caractere in ("Í", "—"):
        assert fonte.getmask(caractere).getbbox() is not None  # glifo desenhado, não um espaço vazio


def test_imagem_de_exemplo_e_jpeg_valido_e_diferente_por_foto():
    a, b = fx.gerar_imagem(1, 1), fx.gerar_imagem(1, 2)
    assert a != b
    img = Image.open(BytesIO(a))
    assert img.format == "JPEG" and img.size == (800, 600)
    imagem.processar(a)  # passa pela mesma validação de upload das fotos reais


def test_todas_as_nove_fotos_geram_imagens_distintas():
    contagem: dict[int, int] = {}
    hashes = set()
    for numero, _item, anotacao in fx.FOTOS:
        contagem[numero] = contagem.get(numero, 0) + 1
        hashes.add(imagem.hash_sha256(fx.gerar_imagem(numero, contagem[numero])))
        assert anotacao.strip()
    assert len(fx.FOTOS) == 9 and len(hashes) == 9  # o hash por inspeção exige imagens diferentes
