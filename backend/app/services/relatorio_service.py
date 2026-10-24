from app.domain.constantes import Situacao, Status
from app.domain.relatorio import explicar_resultado, totais
from app.models import Inspecao
from app.services.foto_service import foto_dict


def _cabecalho(inspecao: Inspecao, ref_interna: str | None) -> dict:
    protocolo = (inspecao.numero_processo or "").strip() or None
    partes = [
        f"Protocolo nº {protocolo}" if protocolo else "Protocolo nº: Não informado",
        f"Inspeção {inspecao.codigo}",
        f"Ref. interna {ref_interna}" if ref_interna else "Ref. interna: sem número (prévia)",
    ]
    sema = (inspecao.numero_relatorio_sema or "").strip() or None
    if sema:
        partes.append(f"Relatório SEMA nº {sema}")
    return {
        "protocolo": protocolo, "codigo": inspecao.codigo, "ref_interna": ref_interna,
        "numero_relatorio_sema": sema, "linha": " | ".join(partes),
    }


def montar(inspecao: Inspecao, incluir_conclusao: bool = True) -> dict:
    """Corpo do relatório a partir do item 5. Finalizada: com a Ref. interna. Demais status: prévia sem número."""
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
    atos = [
        {"tipo": a.tipo, "numero": a.numero, "rotulo": f"{a.tipo} – {'nº ' + a.numero if a.numero else 'nº a definir'}"}
        for a in inspecao.atos
    ]
    return {
        "previa": not finalizada,
        "marca_dagua": marca,
        "cabecalho": _cabecalho(inspecao, numero),
        "constatacoes": {
            "relato": {
                "data_realizacao": inspecao.data_realizacao, "observacoes_vistoria": inspecao.observacoes_vistoria,
            },
            "checklist": {"itens": itens, "totais": totais(inspecao.itens)},
            "fotos": fotos,
        },
        "providencias": {"texto": inspecao.providencias_texto, "atos": atos},
        "conclusao": {"resultado": inspecao.resultado, "regra": explicar_resultado(inspecao.itens, inspecao.resultado)}
        if incluir_conclusao else None,
    }
