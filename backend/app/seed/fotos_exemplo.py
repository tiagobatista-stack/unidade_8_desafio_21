"""Fotos fictícias geradas por programa (nenhuma imagem real)."""
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# (numero da inspeção, ordem do item ou None, anotação)
FOTOS = [
    (1, None, "Vista geral da sede: construções em boas condições e área ao redor limpa."),
    (1, None, "Documentação fictícia apresentada pelo responsável, disposta sobre a mesa no ato da vistoria."),
    (1, None, "Divisa da propriedade com cerca íntegra e sem sinais de invasão."),
    (2, 4, "Placa de segurança na entrada do galpão com tinta desgastada e texto parcialmente ilegível."),
    (2, 5, "Livro de registro de manejo com última anotação datada de meses antes da vistoria."),
    (3, 6, "Caixa separadora com sinais de transbordamento junto à base e resíduo oleoso no solo ao redor."),
    (3, 6, "Área de descarga com manchas escuras no piso, compatíveis com derramamento recorrente."),
    (4, None, "Nascente cercada, com vegetação ciliar preservada no trecho norte."),
    (4, None, "Estrada vicinal de acesso em boas condições de trafegabilidade."),
]

CORES = [(70, 120, 90), (60, 100, 150), (150, 110, 60), (120, 80, 140), (90, 130, 130)]

# Fontes TrueType comuns, com acentos e travessão. A fonte padrão do Pillow não tem esses glifos.
FONTES_CANDIDATAS = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def carregar_fonte(tamanho: int = 36, candidatas: list[str] | None = None) -> tuple[ImageFont.ImageFont, bool]:
    """Devolve (fonte, aceita_acentos). Sem TrueType disponível, usa a padrão e o texto vai sem acentos."""
    for caminho in FONTES_CANDIDATAS if candidatas is None else candidatas:
        if Path(caminho).is_file():
            try:
                return ImageFont.truetype(caminho, tamanho), True
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=tamanho), False
    except TypeError:  # Pillow antigo sem fonte escalável
        return ImageFont.load_default(), False


def texto_da_foto(numero: int, n: int, com_acentos: bool) -> str:
    if com_acentos:
        return f"FOTO FICTÍCIA — INS-{numero:03d} #{n}"
    return f"FOTO FICTICIA - INS-{numero:03d} #{n}"


def gerar_imagem(numero: int, n: int) -> bytes:
    img = Image.new("RGB", (800, 600), CORES[(numero + n) % len(CORES)])
    d = ImageDraw.Draw(img)
    fonte, acentos = carregar_fonte()
    d.rectangle([20, 20, 780, 580], outline=(255, 255, 255), width=4)
    d.text((60, 270), texto_da_foto(numero, n, acentos), fill=(255, 255, 255), font=fonte)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
