import re

from app.errors import ErroNegocio, erro_campo

LAT_MIN, LAT_MAX = -18.05, -7.35
LON_MIN, LON_MAX = -61.65, -50.20


def validar_coordenadas(latitude: float, longitude: float) -> None:
    """RN11: dentro das faixas de Mato Grosso."""
    detalhes = []
    if not (LAT_MIN <= latitude <= LAT_MAX):
        detalhes.append({"campo": "latitude", "mensagem": f"Deve estar entre {LAT_MIN} e {LAT_MAX}."})
    if not (LON_MIN <= longitude <= LON_MAX):
        detalhes.append({"campo": "longitude", "mensagem": f"Deve estar entre {LON_MIN} e {LON_MAX}."})
    if detalhes:
        raise ErroNegocio("COORDENADA_FORA_DE_MT", "Coordenada fora de Mato Grosso.", 422, detalhes)


# ---------- R4/E3: graus, minutos e segundos (GMS) ----------
EIXOS = {"latitude": ("N", "S"), "longitude": ("E", "W")}
_LIMITE_GRAUS = {"latitude": 90, "longitude": 180}
_PADRAO_GMS = re.compile(r"^\s*(\d{1,3})\D+?(\d{1,2})\D+?(\d{1,2}(?:[.,]\d+)?)\D*?([NSEWOLnsewol])\s*$")


def para_gms(valor: float, eixo: str) -> tuple[int, int, int, str]:
    """Decimal -> (graus, minutos, segundos, hemisfério). Os segundos são inteiros e o arredondamento é feito sobre o
    total de segundos, então nunca sai 60" (59,9996" vira o minuto seguinte)."""
    positivo, negativo = EIXOS[eixo]
    total = int(abs(valor) * 3600 + 0.5)
    graus, resto = divmod(total, 3600)
    minutos, segundos = divmod(resto, 60)
    return graus, minutos, segundos, negativo if valor < 0 else positivo


def formatar_gms(valor: float, eixo: str) -> str:
    """Só o hemisfério, sem sinal: 11° 46' 34\" S."""
    graus, minutos, segundos, hemisferio = para_gms(valor, eixo)
    return f"{graus}° {minutos:02d}' {segundos:02d}\" {hemisferio}"


def formatar_par_gms(latitude: float, longitude: float) -> str:
    return f"LAT {formatar_gms(latitude, 'latitude')} | LONG {formatar_gms(longitude, 'longitude')}"


def gms_para_decimal(texto: str, eixo: str, campo: str) -> float:
    """'11° 46\' 34\" S' (ou '11 46 34 S') -> -11.77611 (5 casas, como o banco). Minutos e segundos < 60."""
    achou = _PADRAO_GMS.match(texto or "")
    exemplo = "11° 46' 34\" S" if eixo == "latitude" else "59° 05' 12\" W"
    if not achou:
        raise erro_campo(campo, f"Use o formato graus, minutos, segundos e hemisfério. Ex.: {exemplo}.")
    graus, minutos, segundos, letra = int(achou[1]), int(achou[2]), float(achou[3].replace(",", ".")), achou[4].upper()
    letra = "W" if letra == "O" else letra  # "O" de Oeste
    positivo, negativo = EIXOS[eixo]
    if letra not in (positivo, negativo):
        raise erro_campo(campo, f"Hemisfério deve ser {positivo} ou {negativo}.")
    if minutos >= 60 or segundos >= 60:
        raise erro_campo(campo, "Minutos e segundos devem ser menores que 60.")
    if graus > _LIMITE_GRAUS[eixo] or (graus == _LIMITE_GRAUS[eixo] and (minutos or segundos)):
        raise erro_campo(campo, f"Graus devem estar entre 0 e {_LIMITE_GRAUS[eixo]}.")
    decimal = round(graus + minutos / 60 + segundos / 3600, 5)
    return -decimal if letra == negativo else decimal
