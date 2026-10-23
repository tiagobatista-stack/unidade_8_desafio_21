import csv
from io import StringIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FotoVistoria, Inspecao

COLUNAS = [
    "codigo", "local", "latitude", "longitude", "data_agendamento", "data_realizacao",
    "status", "resultado", "observacoes_vistoria", "qtd_fotos",
]
_PERIGOSOS = ("=", "+", "-", "@", "\t", "\r")


def _texto_seguro(valor: str | None) -> str:
    """Evita que planilhas interpretem texto livre como fórmula."""
    if not valor:
        return ""
    return "'" + valor if valor.startswith(_PERIGOSOS) else valor


def gerar_csv(db: Session) -> str:
    contagem: dict[int, int] = {}
    for inspecao_id in db.scalars(select(FotoVistoria.inspecao_id)):
        contagem[inspecao_id] = contagem.get(inspecao_id, 0) + 1
    saida = StringIO()
    w = csv.writer(saida, delimiter=";", lineterminator="\r\n")
    w.writerow(COLUNAS)
    for i in db.scalars(select(Inspecao).order_by(Inspecao.id)).unique():
        w.writerow([
            i.codigo, _texto_seguro(i.local.nome), i.local.latitude, i.local.longitude,
            i.data_agendamento.isoformat(), i.data_realizacao.isoformat() if i.data_realizacao else "",
            i.status, i.resultado or "", _texto_seguro(i.observacoes_vistoria), contagem.get(i.id, 0),
        ])
    return saida.getvalue()
