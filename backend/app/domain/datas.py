from datetime import date

from app.errors import ErroNegocio


def formatar_br(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def validar_realizacao(realizacao: date, agendamento: date, hoje: date) -> None:
    """RN02 (não futura) e RN13 (não anterior ao agendamento)."""
    if realizacao > hoje:
        raise ErroNegocio(
            "DATA_REALIZACAO_FUTURA", "A data de realização não pode ser posterior a hoje.", 422,
            [{"campo": "data_realizacao", "mensagem": "Data futura."}],
        )
    if realizacao < agendamento:
        raise ErroNegocio(
            "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO",
            "A data de realização não pode ser anterior ao agendamento.", 422,
            [{"campo": "data_realizacao", "mensagem": "Anterior ao agendamento."}],
        )


def realizacao_do_primeiro_item(agendamento: date, hoje: date) -> date:
    """P1: registrar o 1º item de vistoria agendada para o futuro é bloqueado."""
    if hoje < agendamento:
        raise ErroNegocio(
            "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO",
            f"Vistoria agendada para {formatar_br(agendamento)}; reagende (inspeção Aberta) ou aguarde.",
            422,
            [{"campo": "data_agendamento", "mensagem": f"Agendada para {formatar_br(agendamento)}."}],
        )
    return hoje
