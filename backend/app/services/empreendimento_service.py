"""Dados do empreendimento (Local + proprietários) como um dicionário simples.

Antes do fechamento a inspeção mostra os dados atuais do Local; ao fechar, uma cópia é gravada (C2).
"""
from app.models import Local


def instantaneo(local: Local) -> dict:
    return {
        "nome": local.nome,
        "municipio": local.municipio,
        "tipo": local.tipo,
        "latitude": float(local.latitude),
        "longitude": float(local.longitude),
        "numero_car": local.numero_car,
        "proprietarios": [{"nome": p.nome, "telefone": p.telefone} for p in local.proprietarios],
    }
