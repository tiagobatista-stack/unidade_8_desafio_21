"""CPF/CNPJ e CEP (R4/E2). Regras puras: guarda só dígitos, valida os verificadores e formata para exibição."""
import re

from app.errors import erro_campo

_NAO_DIGITOS = re.compile(r"\D")

UFS = (
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI",
    "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
)


def _digito(base: str, pesos: list[int]) -> int:
    resto = sum(int(d) * p for d, p in zip(base, pesos)) % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(digitos: str) -> bool:
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    d1 = _digito(digitos[:9], list(range(10, 1, -1)))
    d2 = _digito(digitos[:9] + str(d1), list(range(11, 1, -1)))
    return digitos[9:] == f"{d1}{d2}"


def cnpj_valido(digitos: str) -> bool:
    if len(digitos) != 14 or digitos == digitos[0] * 14:
        return False
    d1 = _digito(digitos[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = _digito(digitos[:12] + str(d1), [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return digitos[12:] == f"{d1}{d2}"


def normalizar_cpf_cnpj(valor: str | None, campo: str = "cpf_cnpj") -> str | None:
    """Só dígitos; 11 = CPF, 14 = CNPJ, com verificadores conferidos. Vazio vira nulo."""
    bruto = (valor or "").strip()
    if not bruto:
        return None
    digitos = _NAO_DIGITOS.sub("", bruto)
    if len(digitos) == 11:
        if not cpf_valido(digitos):
            raise erro_campo(campo, "CPF inválido.")
    elif len(digitos) == 14:
        if not cnpj_valido(digitos):
            raise erro_campo(campo, "CNPJ inválido.")
    else:
        raise erro_campo(campo, "Informe 11 dígitos (CPF) ou 14 dígitos (CNPJ).")
    return digitos


def formatar_cpf_cnpj(digitos: str | None) -> str | None:
    """'12345678909' -> '123.456.789-09'; '11222333000181' -> '11.222.333/0001-81'."""
    if not digitos:
        return None
    if len(digitos) == 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    if len(digitos) == 14:
        return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
    return digitos


def normalizar_cep(valor: str | None, campo: str = "cep") -> str | None:
    """Só dígitos; exatamente 8. Vazio vira nulo."""
    bruto = (valor or "").strip()
    if not bruto:
        return None
    digitos = _NAO_DIGITOS.sub("", bruto)
    if len(digitos) != 8:
        raise erro_campo(campo, "CEP deve ter 8 dígitos.")
    return digitos


def formatar_cep(digitos: str | None) -> str | None:
    """'78320000' -> '78.320-000'."""
    if not digitos or len(digitos) != 8:
        return digitos or None
    return f"{digitos[:2]}.{digitos[2:5]}-{digitos[5:]}"


def normalizar_uf(valor: str | None, campo: str = "uf", padrao: str | None = "MT") -> str | None:
    texto = (valor or "").strip().upper()
    if not texto:
        return padrao
    if texto not in UFS:
        raise erro_campo(campo, "UF inválida.")
    return texto
