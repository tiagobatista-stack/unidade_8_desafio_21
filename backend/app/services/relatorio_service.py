from app.domain.constantes import Situacao, Status
from app.domain.relatorio import explicar_resultado, totais
from app.models import Inspecao
from app.services import empreendimento_service
from app.services.foto_service import foto_dict


def montar(inspecao: Inspecao) -> dict:
    """Relatório estruturado. Finalizada: cópia do empreendimento e número. Demais status: prévia sem número."""
    finalizada = inspecao.status == Status.FINALIZADA
    numeros = {item.id: n for n, item in enumerate(inspecao.itens, start=1)}
    itens = [
        {
            "numero": numeros[i.id], "descricao": i.descricao, "critico": i.critico, "situacao": i.situacao,
            "observacao": i.observacao, "critico_nao_conforme": i.critico and i.situacao == Situacao.NAO_CONFORME,
        }
        for i in inspecao.itens
    ]
    por_id = {i.id: i for i in inspecao.itens}
    fotos = []
    for n, f in enumerate(inspecao.fotos, start=1):
        item = por_id.get(f.item_inspecao_id) if f.item_inspecao_id else None
        fotos.append({
            "numero": n, "url_original": foto_dict(f)["url_original"], "nome_original": f.nome_original,
            "legenda": f.legenda, "anotacao": f.anotacao,
            "item_numero": numeros[item.id] if item else None,
            "item_descricao": item.descricao if item else None, "data_captura": f.data_captura,
        })
    if finalizada:
        marca = None
    elif inspecao.status == Status.CANCELADA:
        marca = "CANCELADA, NÃO FINALIZADO"
    else:
        marca = "PRÉVIA, NÃO FINALIZADO"
    numero = inspecao.numero_relatorio if finalizada else None
    return {
        "previa": not finalizada,
        "marca_dagua": marca,
        "numero_relatorio": numero,
        "titulo": f"Relatório de Vistoria nº {numero}" if numero else "Relatório de Vistoria (sem número)",
        "identificacao": {
            "codigo": inspecao.codigo, "numero_processo": inspecao.numero_processo, "status": inspecao.status,
            "resultado": inspecao.resultado, "data_agendamento": inspecao.data_agendamento,
            "data_realizacao": inspecao.data_realizacao, "fechado_em": inspecao.fechado_em,
        },
        "empreendimento": empreendimento_service.da_inspecao(inspecao),
        "objetivo": {
            "objetivo": inspecao.objetivo, "observacoes": inspecao.observacoes,
            "observacoes_vistoria": inspecao.observacoes_vistoria,
        },
        "checklist": {"itens": itens, "totais": totais(inspecao.itens)},
        "fotos": fotos,
        "conclusao": {"resultado": inspecao.resultado, "regra": explicar_resultado(inspecao.itens, inspecao.resultado)},
    }
