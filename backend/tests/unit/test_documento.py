import pytest

from app.domain.documento import (
    cnpj_valido,
    cpf_valido,
    formatar_cep,
    formatar_cpf_cnpj,
    normalizar_cep,
    normalizar_cpf_cnpj,
    normalizar_uf,
)
from app.errors import ErroNegocio

# Documentos fictícios com dígitos verificadores válidos.
CPF = "52998224725"
CNPJ = "11222333000181"


def codigo(f, *a, **kw):
    with pytest.raises(ErroNegocio) as e:
        f(*a, **kw)
    return e.value


def test_cpf_e_cnpj_validos():
    assert cpf_valido(CPF) and cnpj_valido(CNPJ)


@pytest.mark.parametrize("cpf", ["52998224724", "11111111111", "1234567890", "529982247250"])
def test_cpf_invalido(cpf):
    assert not cpf_valido(cpf)


@pytest.mark.parametrize("cnpj", ["11222333000182", "00000000000000", "1122233300018"])
def test_cnpj_invalido(cnpj):
    assert not cnpj_valido(cnpj)


def test_normaliza_com_mascara_e_guarda_so_digitos():
    assert normalizar_cpf_cnpj("529.982.247-25") == CPF
    assert normalizar_cpf_cnpj(" 11.222.333/0001-81 ") == CNPJ


@pytest.mark.parametrize("vazio", [None, "", "   "])
def test_vazio_vira_nulo(vazio):
    assert normalizar_cpf_cnpj(vazio) is None
    assert normalizar_cep(vazio) is None


def test_cpf_com_digito_verificador_errado_e_rejeitado():
    e = codigo(normalizar_cpf_cnpj, "529.982.247-24", "proprietarios.0.cpf_cnpj")
    assert e.detalhes == [{"campo": "proprietarios.0.cpf_cnpj", "mensagem": "CPF inválido."}]


def test_cnpj_com_digito_verificador_errado_e_rejeitado():
    assert codigo(normalizar_cpf_cnpj, "11.222.333/0001-80").detalhes[0]["mensagem"] == "CNPJ inválido."


def test_tamanho_diferente_de_11_ou_14_e_rejeitado():
    assert "11 dígitos" in codigo(normalizar_cpf_cnpj, "123456").detalhes[0]["mensagem"]


def test_mascara_de_exibicao():
    assert formatar_cpf_cnpj(CPF) == "529.982.247-25"
    assert formatar_cpf_cnpj(CNPJ) == "11.222.333/0001-81"
    assert formatar_cpf_cnpj(None) is None


def test_cep():
    assert normalizar_cep("78.320-000") == "78320000"
    assert formatar_cep("78320000") == "78.320-000"
    assert codigo(normalizar_cep, "7832000").detalhes[0]["mensagem"] == "CEP deve ter 8 dígitos."


def test_uf_padrao_mt_e_validacao():
    assert normalizar_uf(None) == "MT"
    assert normalizar_uf(" sp ") == "SP"
    assert normalizar_uf("", padrao=None) is None
    assert codigo(normalizar_uf, "XX").detalhes[0]["mensagem"] == "UF inválida."
