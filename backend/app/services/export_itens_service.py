"""Exportação dos itens do checklist: um CSV separado, uma linha por item (o CSV por inspeção não muda)."""
import csv
from io import StringIO

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import FotoVistoria, Inspecao
from app.services.export_service import _texto_seguro

COLUNAS_ITENS = [
    "codigo_inspecao", "numero_processo", "local", "status_inspecao", "resultado_inspecao",
    "item_numero", "item_descricao", "critico", "situacao", "observacao", "origem", "qtd_fotos",
]


def gerar_csv_itens(db: Session) -> str:
    """`;` como delimitador, texto livre protegido contra fórmulas, itens na ordem do checklist.

    `item_numero` é a posição do item no checklist da inspeção (a mesma numeração do relatório).
    `critico` sai como `sim`/`nao`; `situacao`, `origem`, status e resultado saem com os códigos da API.
    """
    fotos_por_item = dict(
        db.execute(
            select(FotoVistoria.item_inspecao_id, func.count())
            .where(FotoVistoria.item_inspecao_id.is_not(None))
            .group_by(FotoVistoria.item_inspecao_id)
        ).all()
    )
    saida = StringIO()
    w = csv.writer(saida, delimiter=";", lineterminator="\r\n")
    w.writerow(COLUNAS_ITENS)
    for inspecao in db.scalars(select(Inspecao).order_by(Inspecao.id)).unique():
        for numero, item in enumerate(inspecao.itens, start=1):
            w.writerow([
                inspecao.codigo, _texto_seguro(inspecao.numero_processo), _texto_seguro(inspecao.local.nome),
                inspecao.status, inspecao.resultado or "", numero, _texto_seguro(item.descricao),
                "sim" if item.critico else "nao", item.situacao, _texto_seguro(item.observacao), item.origem,
                fotos_por_item.get(item.id, 0),
            ])
    return saida.getvalue()
