from dataclasses import dataclass

import pytest

from app.domain.relatorio import explicar_resultado, formatar_numero, totais


@dataclass
class It:
    critico: bool
    situacao: str


def test_formato_do_numero():
    assert formatar_numero(1, 2026) == "0001/2026"
    assert formatar_numero(42, 2026) == "0042/2026"
    assert formatar_numero(1234, 2027) == "1234/2027"
    assert formatar_numero(12345, 2027) == "12345/2027"  # passa de 4 dígitos sem truncar


def test_totais():
    itens = [It(True, "CONFORME"), It(False, "CONFORME"), It(False, "NAO_CONFORME"), It(True, "NAO_SE_APLICA"), It(False, "NAO_RESPONDIDO")]
    assert totais(itens) == {"total": 5, "respondidos": 4, "conformes": 2, "nao_conformes": 1, "nao_aplicaveis": 1, "nao_respondidos": 1}
    assert totais([]) == {"total": 0, "respondidos": 0, "conformes": 0, "nao_conformes": 0, "nao_aplicaveis": 0, "nao_respondidos": 0}


@pytest.mark.parametrize("itens,resultado,esperado", [
    ([It(True, "NAO_CONFORME"), It(False, "CONFORME")], "REPROVADA", "1 item crítico não conforme"),
    ([It(True, "NAO_CONFORME"), It(True, "NAO_CONFORME"), It(False, "NAO_CONFORME")], "REPROVADA", "2 itens críticos não conformes"),
    ([It(False, "NAO_CONFORME"), It(True, "CONFORME")], "APROVADA_COM_RESSALVAS", "Nenhum item crítico não conforme; 1 item não conforme"),
    ([It(False, "NAO_CONFORME"), It(False, "NAO_CONFORME")], "APROVADA_COM_RESSALVAS", "Nenhum item crítico não conforme; 2 itens não conformes"),
    ([It(True, "CONFORME"), It(False, "NAO_SE_APLICA")], "APROVADA", "Nenhum item não conforme"),
])
def test_explicacao_do_resultado(itens, resultado, esperado):
    assert explicar_resultado(itens, resultado) == esperado


def test_explicacao_da_previa_sem_resultado():
    assert explicar_resultado([It(False, "NAO_RESPONDIDO")], None) == "Resultado ainda não calculado: 1 item não respondido."
    assert "2 itens não respondidos" in explicar_resultado([It(False, "NAO_RESPONDIDO")] * 2, None)
    assert "será calculado quando a inspeção for fechada" in explicar_resultado([It(False, "CONFORME")], None)
