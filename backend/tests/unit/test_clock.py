from datetime import date

from app import clock


def test_hoje_fixo_nos_testes():
    assert clock.hoje() == date(2026, 10, 23)


def test_sem_fixar_usa_data_real():
    clock.fixar_hoje(None)
    assert clock.hoje() == date.today()


def test_variavel_de_ambiente_fixa_o_hoje(monkeypatch):
    clock.fixar_hoje(None)
    monkeypatch.setenv("INSPECOES_HOJE", "2026-10-23")
    assert clock.hoje() == date(2026, 10, 23)
    assert clock.agora().date() == date(2026, 10, 23)
