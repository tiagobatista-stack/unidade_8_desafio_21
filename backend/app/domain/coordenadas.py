from app.errors import ErroNegocio

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
