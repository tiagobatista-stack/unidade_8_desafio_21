"""CAR e telefone dos proprietários (C1). Regras puras, sem acesso a banco."""
import re

from app.errors import erro_campo

MAX_CAR = 60
MAX_NOME_PROPRIETARIO = 120
MAX_PROPRIETARIOS = 20
_NAO_DIGITOS = re.compile(r"\D")


def normalizar_car(valor: str | None) -> str | None:
    """Maiúsculas e sem espaços nas pontas. Texto livre: nenhum formato é rejeitado (SICAR, SIMCAR-MT etc.)."""
    texto = (valor or "").strip().upper()
    if not texto:
        return None
    if len(texto) > MAX_CAR:
        raise erro_campo("numero_car", f"Máximo de {MAX_CAR} caracteres.")
    return texto


def normalizar_telefone(valor: str | None, campo: str = "telefone") -> str | None:
    """Só dígitos; 10 ou 11 dígitos com DDD (11 a 99). Vazio vira nulo."""
    bruto = (valor or "").strip()
    if not bruto:
        return None
    digitos = _NAO_DIGITOS.sub("", bruto)
    if len(digitos) not in (10, 11):
        raise erro_campo(campo, "Informe o telefone com DDD (10 ou 11 dígitos).")
    if int(digitos[:2]) < 11:
        raise erro_campo(campo, "DDD inválido.")
    return digitos


def formatar_telefone(digitos: str | None) -> str | None:
    """'65900000001' -> '(65) 90000-0001'; '6533334444' -> '(65) 3333-4444'."""
    if not digitos or len(digitos) not in (10, 11):
        return digitos or None
    cabeca = 5 if len(digitos) == 11 else 4
    return f"({digitos[:2]}) {digitos[2:2 + cabeca]}-{digitos[2 + cabeca:]}"


def padrao_sicar(car: str | None) -> bool:
    """Só informativo (aviso na tela): UF-código IBGE-código, ex.: MT-5107925-<código>."""
    return bool(car and re.fullmatch(r"[A-Z]{2}-\d{7}-[A-Z0-9]+", car))
