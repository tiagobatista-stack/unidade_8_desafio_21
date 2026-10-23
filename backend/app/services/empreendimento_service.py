"""Dados do empreendimento (Local + proprietários) como um dicionário simples.

Antes do fechamento a inspeção mostra os dados atuais do Local; ao fechar, uma cópia é gravada (C2).
"""
import json

from app.models import Inspecao, Local


def instantaneo(local: Local) -> dict:
    return {
        "nome": local.nome,
        "municipio": local.municipio,
        "tipo": local.tipo,
        "latitude": float(local.latitude),
        "longitude": float(local.longitude),
        "numero_car": local.numero_car,
        "logradouro": local.logradouro,
        "uf": local.uf,
        "cep": local.cep,
        "proprietarios": [
            {
                "nome": p.nome, "telefone": p.telefone, "cpf_cnpj": p.cpf_cnpj,
                "corr_logradouro": p.corr_logradouro, "corr_numero": p.corr_numero,
                "corr_complemento": p.corr_complemento, "corr_bairro": p.corr_bairro,
                "corr_municipio": p.corr_municipio, "corr_uf": p.corr_uf, "corr_cep": p.corr_cep,
            }
            for p in local.proprietarios
        ],
    }


def copiar_no_fechamento(inspecao: Inspecao) -> None:
    """Grava a cópia dos dados do Local; chamada dentro da transação que finaliza a inspeção."""
    inspecao.empreendimento_json = json.dumps(instantaneo(inspecao.local), ensure_ascii=False)


def da_inspecao(inspecao: Inspecao) -> dict:
    """Finalizada: a cópia do fechamento. Demais status (ou legado sem cópia): dados atuais do Local."""
    if inspecao.status == "FINALIZADA" and inspecao.empreendimento_json:
        return json.loads(inspecao.empreendimento_json)
    return instantaneo(inspecao.local)
