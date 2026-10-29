"""R4/E3: exibição e digitação de coordenadas em graus, minutos e segundos."""
import pytest

from app.domain.coordenadas import formatar_gms, formatar_par_gms, gms_para_decimal, para_gms
from app.errors import ErroNegocio


def mensagem(f, *a):
    with pytest.raises(ErroNegocio) as e:
        f(*a)
    return e.value.detalhes[0]


def test_exemplo_nos_dois_sentidos_gms_decimal_gms():
    lat = gms_para_decimal("11° 46' 34\" S", "latitude", "latitude_gms")
    lon = gms_para_decimal("59° 05' 12\" W", "longitude", "longitude_gms")
    assert (lat, lon) == (-11.77611, -59.08667)
    assert formatar_par_gms(lat, lon) == "LAT 11° 46' 34\" S | LONG 59° 05' 12\" W"


def test_exemplo_decimal_para_gms_e_de_volta():
    assert formatar_gms(-11.77611, "latitude") == "11° 46' 34\" S"
    assert formatar_gms(-59.08667, "longitude") == "59° 05' 12\" W"
    assert gms_para_decimal(formatar_gms(-10.42318, "latitude"), "latitude", "x") == pytest.approx(-10.42318, abs=0.00015)  # a exibição usa segundos inteiros (até 0,5" = 0,00014°)


def test_exibicao_so_com_hemisferio_sem_sinal_negativo():
    assert "-" not in formatar_par_gms(-10.42318, -58.71264)
    assert formatar_gms(10.5, "latitude").endswith(" N") and formatar_gms(50.5, "longitude").endswith(" E")


def test_borda_de_arredondamento_nunca_gera_60_segundos():
    # 11° 46' 59,9996" arredonda para 11° 47' 00" (e não 46' 60")
    d = gms_para_decimal("11° 46' 59,9996\" S", "latitude", "x")
    assert formatar_gms(d, "latitude") == "11° 47' 00\" S"
    assert para_gms(-11.999999, "latitude") == (12, 0, 0, "S")  # vira o grau seguinte
    assert para_gms(-11.99986, "latitude")[2] != 60
    for centesimos in range(0, 100000, 137):  # varredura: nenhum valor com minutos ou segundos = 60
        _, m, s, _ = para_gms(-11 - centesimos / 100000, "latitude")
        assert m < 60 and s < 60


@pytest.mark.parametrize("texto", ["11 46 34 S", "11º46'34\"S", "11° 46' 34\" s", "  11°46′34″S "])
def test_aceita_variacoes_de_digitacao(texto):
    assert gms_para_decimal(texto, "latitude", "x") == -11.77611


def test_oeste_pode_ser_digitado_com_o():
    assert gms_para_decimal("59 05 12 O", "longitude", "x") == -59.08667


def test_minutos_60_sao_invalidos():
    d = mensagem(gms_para_decimal, "11° 60' 00\" S", "latitude", "latitude_gms")
    assert d == {"campo": "latitude_gms", "mensagem": "Minutos e segundos devem ser menores que 60."}


def test_segundos_60_sao_invalidos():
    assert "menores que 60" in mensagem(gms_para_decimal, "11° 46' 60\" S", "latitude", "x")["mensagem"]


def test_hemisferio_errado_para_o_eixo():
    assert mensagem(gms_para_decimal, "11° 46' 34\" W", "latitude", "x")["mensagem"] == "Hemisfério deve ser N ou S."
    assert mensagem(gms_para_decimal, "59° 05' 12\" S", "longitude", "x")["mensagem"] == "Hemisfério deve ser E ou W."


@pytest.mark.parametrize("texto", ["", "abc", "11° 46' S", "11° 46' 34\"", "11,5 S"])
def test_formato_invalido(texto):
    assert "formato" in mensagem(gms_para_decimal, texto, "latitude", "x")["mensagem"]


def test_graus_acima_do_limite():
    assert "Graus" in mensagem(gms_para_decimal, "91° 00' 00\" S", "latitude", "x")["mensagem"]
