"""Validação por conteúdo, hash, miniatura e remoção de EXIF (RN20–RN22, RN26, RN27)."""
import hashlib
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps

from app.errors import ErroNegocio

MAX_BYTES = 5_242_880
LADO_MINIATURA = 320
FORMATOS = {"JPEG": ("image/jpeg", "jpg"), "PNG": ("image/png", "png"), "WEBP": ("image/webp", "webp")}


@dataclass
class ImagemProcessada:
    original: bytes
    miniatura: bytes
    mime_type: str
    extensao: str
    largura: int
    altura: int
    hash_sha256: str


def hash_sha256(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def _formato_invalido() -> ErroNegocio:
    return ErroNegocio("FOTO_FORMATO_INVALIDO", "Envie uma imagem JPEG, PNG ou WebP válida.", 415)


def validar_tamanho(conteudo: bytes) -> None:
    if len(conteudo) > MAX_BYTES:
        raise ErroNegocio("FOTO_TAMANHO_EXCEDIDO", "A foto excede o limite de 5 MB.", 413)


def _sem_exif(img: Image.Image, formato: str) -> bytes:
    """Reserializa só os pixels: nenhum metadado (EXIF/GPS) é copiado."""
    limpa = Image.frombytes(img.mode, img.size, img.tobytes())
    if img.mode == "P" and img.getpalette():
        limpa.putpalette(img.getpalette())
    saida = BytesIO()
    opcoes = {"JPEG": {"quality": 92}, "PNG": {}, "WEBP": {"quality": 92}}[formato]
    limpa.save(saida, format=formato, **opcoes)
    return saida.getvalue()


def processar(conteudo: bytes) -> ImagemProcessada:
    """Detecta o tipo pelo conteúdo (não pela extensão/Content-Type)."""
    if not conteudo:
        raise _formato_invalido()
    validar_tamanho(conteudo)
    try:
        with Image.open(BytesIO(conteudo)) as probe:
            formato = probe.format
            probe.verify()
        if formato not in FORMATOS:
            raise _formato_invalido()
        with Image.open(BytesIO(conteudo)) as img:
            img.load()
            img = ImageOps.exif_transpose(img)  # respeita a orientação antes de descartar o EXIF
            if formato == "JPEG" and img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            largura, altura = img.size
            original = _sem_exif(img, formato)
            mini = img.copy()
            mini.thumbnail((LADO_MINIATURA, LADO_MINIATURA))
            miniatura = _sem_exif(mini, formato)
    except ErroNegocio:
        raise
    except Exception:  # arquivo corrompido, bomba de descompressão etc.
        raise _formato_invalido() from None
    mime, ext = FORMATOS[formato]
    return ImagemProcessada(original, miniatura, mime, ext, largura, altura, hash_sha256(conteudo))
