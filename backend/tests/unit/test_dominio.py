from dataclasses import dataclass
from datetime import date

import pytest

from app.domain.coordenadas import validar_coordenadas
from app.domain.datas import realizacao_do_primeiro_item, validar_realizacao
from app.domain.resultado import calcular_resultado
from app.domain.texto import sanear
from app.domain.transicoes import exigir_editavel, validar_transicao
from app.errors import ErroNegocio

HOJE = date(2026, 10, 23)


@dataclass
class It:
    critico: bool
    situacao: str


def test_resultado_sem_nc_aprovada():  # CA11
    assert calcular_resultado([It(True, "CONFORME"), It(False, "NAO_SE_APLICA")]) == "APROVADA"


def test_resultado_nc_nao_critico_ressalvas():  # CA12
    assert calcular_resultado([It(True, "CONFORME"), It(False, "NAO_CONFORME")]) == "APROVADA_COM_RESSALVAS"


def test_resultado_nc_critico_reprovada():  # CA13
    assert calcular_resultado([It(True, "NAO_CONFORME"), It(False, "NAO_CONFORME")]) == "REPROVADA"


@pytest.mark.parametrize(
    "origem,destino",
    [("ABERTA", "EM_ANDAMENTO"), ("ABERTA", "CANCELADA"), ("EM_ANDAMENTO", "FINALIZADA")],
)
def test_transicoes_validas(origem, destino):
    validar_transicao(origem, destino)


@pytest.mark.parametrize(
    "origem,destino",
    [
        ("ABERTA", "FINALIZADA"),
        ("EM_ANDAMENTO", "CANCELADA"),
        ("EM_ANDAMENTO", "ABERTA"),
        ("FINALIZADA", "EM_ANDAMENTO"),
        ("CANCELADA", "ABERTA"),
    ],
)
def test_transicoes_invalidas(origem, destino):
    with pytest.raises(ErroNegocio) as e:
        validar_transicao(origem, destino)
    assert e.value.codigo == "TRANSICAO_INVALIDA" and e.value.status == 409


def test_imutavel():
    exigir_editavel("ABERTA")
    exigir_editavel("EM_ANDAMENTO")
    for s in ("FINALIZADA", "CANCELADA"):
        with pytest.raises(ErroNegocio) as e:
            exigir_editavel(s)
        assert e.value.codigo == "INSPECAO_IMUTAVEL"


def test_realizacao_futura():  # CA03
    with pytest.raises(ErroNegocio) as e:
        validar_realizacao(date(2026, 10, 24), date(2026, 10, 20), HOJE)
    assert e.value.codigo == "DATA_REALIZACAO_FUTURA"


def test_realizacao_anterior_ao_agendamento():  # CA32
    with pytest.raises(ErroNegocio) as e:
        validar_realizacao(date(2026, 10, 19), date(2026, 10, 20), HOJE)
    assert e.value.codigo == "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO"


def test_realizacao_valida_limites():
    validar_realizacao(HOJE, date(2026, 10, 23), HOJE)
    validar_realizacao(date(2026, 10, 20), date(2026, 10, 20), HOJE)


def test_primeiro_item_p1_bloqueia_agendamento_futuro():
    with pytest.raises(ErroNegocio) as e:
        realizacao_do_primeiro_item(date(2026, 10, 28), HOJE)
    assert e.value.codigo == "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO"
    assert "28/10/2026" in e.value.mensagem


def test_primeiro_item_usa_hoje():
    assert realizacao_do_primeiro_item(date(2026, 10, 20), HOJE) == HOJE
    assert realizacao_do_primeiro_item(HOJE, HOJE) == HOJE


def test_coordenada_valida_e_limites():
    validar_coordenadas(-10.42318, -58.71264)
    validar_coordenadas(-18.05, -61.65)
    validar_coordenadas(-7.35, -50.20)


@pytest.mark.parametrize("lat,lon,campo", [(-25.0, -58.0, "latitude"), (-10.0, -40.0, "longitude")])
def test_coordenada_fora_de_mt(lat, lon, campo):  # CA26
    with pytest.raises(ErroNegocio) as e:
        validar_coordenadas(lat, lon)
    assert e.value.codigo == "COORDENADA_FORA_DE_MT"
    assert e.value.detalhes[0]["campo"] == campo


def test_sanear_trim_e_vazio_vira_nulo():  # CA38
    assert sanear("  oi \n", "x", 10) == "oi"
    assert sanear("   ", "x", 10) is None
    assert sanear(None, "x", 10) is None


def test_sanear_limite():  # CA37
    assert sanear("a" * 2000, "x", 2000) == "a" * 2000
    with pytest.raises(ErroNegocio) as e:
        sanear("a" * 2001, "x", 2000)
    assert e.value.codigo == "VALIDACAO_CAMPO"


def test_sanear_obrigatorio():
    with pytest.raises(ErroNegocio):
        sanear("  ", "objetivo", 10, obrigatorio=True)


def test_sanear_preserva_quebras_e_texto_puro():  # CA41
    assert sanear("<script>a</script>\nlinha2", "x", 100) == "<script>a</script>\nlinha2"
