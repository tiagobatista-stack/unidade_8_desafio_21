"""Mensagens orientativas ao usuário, calculadas no backend (a tela só exibe)."""
from datetime import date

from app.domain.constantes import Status
from app.domain.datas import formatar_br

MSG_NAO_INICIADA = (
    "A inspeção ainda não foi iniciada. Registre a situação de pelo menos um item do checklist antes de fechar."
)


def motivo_fechamento_bloqueado(status: str) -> str | None:
    """Fechar só é possível com a inspeção em andamento; em ABERTA explica o que falta."""
    return MSG_NAO_INICIADA if status == Status.ABERTA else None


def motivo_registro_bloqueado(status: str, agendamento: date, hoje: date) -> str | None:
    """P1: aviso preventivo quando a vistoria está agendada para depois de hoje."""
    if status == Status.ABERTA and agendamento > hoje:
        return (
            f"Vistoria agendada para {formatar_br(agendamento)}. "
            "Para registrar o checklist antes dessa data, reagende em Editar inspeção."
        )
    return None
