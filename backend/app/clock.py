"""Relógio injetável: testes fixam "hoje" em 2026-10-23."""
import os
from datetime import date, datetime

_hoje_fixo: date | None = None


def _fixo() -> date | None:
    """Fixado por código (testes) ou pela variável INSPECOES_HOJE=AAAA-MM-DD (demonstrações/E2E)."""
    if _hoje_fixo:
        return _hoje_fixo
    env = os.environ.get("INSPECOES_HOJE")
    return date.fromisoformat(env) if env else None


def hoje() -> date:
    return _fixo() or date.today()


def agora() -> datetime:
    fixo = _fixo()
    if fixo:
        return datetime.combine(fixo, datetime.now().time())
    return datetime.now()


def fixar_hoje(valor: date | None) -> None:
    global _hoje_fixo
    _hoje_fixo = valor
