from app.errors import ErroNegocio, erro_campo


def sanear(valor: str | None, campo: str, maximo: int, obrigatorio: bool = False) -> str | None:
    """Trim; vazio vira nulo (ou erro se obrigatório); limite de tamanho (RN19)."""
    texto = valor.strip() if valor is not None else ""
    if not texto:
        if obrigatorio:
            raise erro_campo(campo, "Campo obrigatório.")
        return None
    if len(texto) > maximo:
        raise erro_campo(campo, f"Máximo de {maximo} caracteres.")
    return texto


__all__ = ["sanear", "ErroNegocio"]
