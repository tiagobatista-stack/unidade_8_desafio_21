from datetime import date

from app import clock


def test_hoje_fixo_nos_testes():
    assert clock.hoje() == date(2026, 10, 23)


def test_sem_fixar_usa_data_real():
    clock.fixar_hoje(None)
    assert clock.hoje() == date.today()
