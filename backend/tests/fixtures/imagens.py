"""Imagens geradas em código (nunca imagens reais)."""
from io import BytesIO

from PIL import Image

LIMITE = 5_242_880


def _salvar(img: Image.Image, formato: str, **kw) -> bytes:
    buf = BytesIO()
    img.save(buf, format=formato, **kw)
    return buf.getvalue()


def cor(i: int) -> tuple[int, int, int]:
    return ((i * 37) % 256, (i * 91 + 20) % 256, (i * 53 + 99) % 256)


def jpeg(i: int = 1, tamanho=(800, 600)) -> bytes:
    return _salvar(Image.new("RGB", tamanho, cor(i)), "JPEG")


def png(i: int = 1, tamanho=(400, 300)) -> bytes:
    return _salvar(Image.new("RGB", tamanho, cor(i)), "PNG")


def webp(i: int = 1, tamanho=(400, 300)) -> bytes:
    return _salvar(Image.new("RGB", tamanho, cor(i)), "WEBP")


def gif(i: int = 1) -> bytes:
    return _salvar(Image.new("P", (50, 50), i % 200), "GIF")


def exif_com_gps() -> Image.Exif:
    exif = Image.Exif()
    exif[0x010F] = "Fabricante Fictício"
    gps = exif.get_ifd(0x8825)
    gps[1], gps[2], gps[3], gps[4] = "S", (10.0, 25.0, 0.0), "W", (58.0, 42.0, 0.0)
    return exif


def jpeg_com_exif(i: int = 1) -> bytes:
    return _salvar(Image.new("RGB", (800, 600), cor(i)), "JPEG", exif=exif_com_gps())


def png_com_exif(i: int = 1) -> bytes:
    return _salvar(Image.new("RGB", (200, 200), cor(i)), "PNG", exif=exif_com_gps())


def webp_com_exif(i: int = 1) -> bytes:
    return _salvar(Image.new("RGB", (200, 200), cor(i)), "WEBP", exif=exif_com_gps())


def jpeg_com_tamanho(total: int, i: int = 1) -> bytes:
    """JPEG válido preenchido (bytes após o EOI são ignorados) até exatamente `total` bytes."""
    base = jpeg(i)
    assert len(base) < total
    return base + b"\x00" * (total - len(base))


def texto_renomeado() -> bytes:
    return "isto é só texto, não uma imagem".encode("utf-8")
