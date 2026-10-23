from app.domain.constantes import Status
from app.errors import ErroNegocio

TRANSICOES: dict[str, set[str]] = {
    Status.ABERTA: {Status.EM_ANDAMENTO, Status.CANCELADA},
    Status.EM_ANDAMENTO: {Status.FINALIZADA},
    Status.FINALIZADA: set(),
    Status.CANCELADA: set(),
}


def validar_transicao(origem: str, destino: str) -> None:
    """RN08."""
    if destino not in TRANSICOES.get(origem, set()):
        raise ErroNegocio(
            "TRANSICAO_INVALIDA", f"Transição de {origem} para {destino} não é permitida.", 409
        )


def exigir_editavel(status: str) -> None:
    """RN07: FINALIZADA e CANCELADA são imutáveis."""
    if status in Status.TERMINAIS:
        raise ErroNegocio("INSPECAO_IMUTAVEL", "Inspeção finalizada ou cancelada não pode ser alterada.", 409)
