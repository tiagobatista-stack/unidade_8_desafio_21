"""Relógio injetável: testes fixam "hoje" em 2026-10-23."""
from datetime import date, datetime

_hoje_fixo: date | None = None


def hoje() -> date:
    return _hoje_fixo or date.today()


def agora() -> datetime:
    if _hoje_fixo:
        return datetime.combine(_hoje_fixo, datetime.now().time())
    return datetime.now()


def fixar_hoje(valor: date | None) -> None:
    global _hoje_fixo
    _hoje_fixo = valor
