"""Fotos fictícias geradas por programa (nenhuma imagem real)."""
from io import BytesIO

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


def gerar_imagem(numero: int, n: int) -> bytes:
    img = Image.new("RGB", (800, 600), CORES[(numero + n) % len(CORES)])
    d = ImageDraw.Draw(img)
    try:
        fonte = ImageFont.load_default(size=36)
    except TypeError:  # Pillow antigo sem fonte escalável
        fonte = ImageFont.load_default()
    d.rectangle([20, 20, 780, 580], outline=(255, 255, 255), width=4)
    d.text((60, 270), f"FOTO FICTÍCIA — INS-{numero:03d} #{n}", fill=(255, 255, 255), font=fonte)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
