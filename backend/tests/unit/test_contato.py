import pytest

from app.domain.contato import formatar_telefone, normalizar_car, normalizar_telefone, padrao_sicar
from app.errors import ErroNegocio


# ---------- CAR ----------
def test_car_em_maiusculas_e_sem_espacos_nas_pontas():
    assert normalizar_car("  mt-5107925-ab12cd  ") == "MT-5107925-AB12CD"


def test_car_vazio_vira_nulo():
    assert normalizar_car(None) is None
    assert normalizar_car("") is None
    assert normalizar_car("   ") is None


@pytest.mark.parametrize("valor", [
    "MT-5107925-00000000000000000000000000000001",  # SICAR
    "mt-123456/2020",  # outro formato (ex.: estadual)
    "CAR 123 456",  # espaços internos preservados
    "qualquer-coisa",  # nada é rejeitado
])
def test_car_texto_livre_nunca_rejeita_formato(valor):
    assert normalizar_car(valor) == valor.strip().upper()


def test_car_limite_de_60_caracteres():
    assert normalizar_car("A" * 60) == "A" * 60
    with pytest.raises(ErroNegocio) as e:
        normalizar_car("A" * 61)
    assert e.value.codigo == "VALIDACAO_CAMPO" and e.value.detalhes[0]["campo"] == "numero_car"


def test_padrao_sicar_e_so_informativo():
    assert padrao_sicar("MT-5107925-00000000000000000000000000000001")
    assert not padrao_sicar("MT-123456/2020") and not padrao_sicar(None) and not padrao_sicar("")


# ---------- telefone ----------
@pytest.mark.parametrize("entrada,esperado", [
    ("(65) 90000-0001", "65900000001"),
    ("65900000001", "65900000001"),
    ("65 9 0000-0001", "65900000001"),
    ("(65) 3333-4444", "6533334444"),
    ("6533334444", "6533334444"),
    ("(11) 91234-5678", "11912345678"),  # DDD 11 é o menor válido
])
def test_telefone_so_digitos(entrada, esperado):
    assert normalizar_telefone(entrada) == esperado


@pytest.mark.parametrize("entrada", [None, "", "   "])
def test_telefone_vazio_vira_nulo(entrada):
    assert normalizar_telefone(entrada) is None


@pytest.mark.parametrize("entrada", [
    "900000001",  # 9 dígitos (sem DDD)
    "659000000011",  # 12 dígitos
    "123",  # curto
    "abc",  # sem dígitos
    "(65) 9000-00001-1",  # 12 dígitos
    "(01) 90000-0001",  # DDD 01
    "(10) 3333-4444",  # DDD 10
])
def test_telefone_invalido(entrada):
    with pytest.raises(ErroNegocio) as e:
        normalizar_telefone(entrada, "proprietarios.0.telefone")
    assert e.value.codigo == "VALIDACAO_CAMPO" and e.value.status == 422
    assert e.value.detalhes[0]["campo"] == "proprietarios.0.telefone"


def test_formatar_telefone():
    assert formatar_telefone("65900000001") == "(65) 90000-0001"
    assert formatar_telefone("6533334444") == "(65) 3333-4444"
    assert formatar_telefone(None) is None
    assert formatar_telefone("") is None
