from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import FotoVistoria, Inspecao, ModeloItem


def obter(db: Session, inspecao_id: int) -> Inspecao | None:
    return db.get(Inspecao, inspecao_id)


def adicionar(db: Session, inspecao: Inspecao) -> Inspecao:
    db.add(inspecao)
    db.flush()
    return inspecao


def modelo_ativo(db: Session) -> list[ModeloItem]:
    return list(db.scalars(select(ModeloItem).where(ModeloItem.ativo.is_(True)).order_by(ModeloItem.ordem)))


def listar(
    db: Session,
    status: list[str] | None,
    data_inicio: date | None,
    data_fim: date | None,
    local_id: int | None,
    numero_processo: str | None,
    pagina: int,
    tamanho: int,
) -> tuple[list[Inspecao], int]:
    filtros = []
    if status:
        filtros.append(Inspecao.status.in_(status))
    if data_inicio:
        filtros.append(Inspecao.data_agendamento >= data_inicio)
    if data_fim:
        filtros.append(Inspecao.data_agendamento <= data_fim)
    if local_id:
        filtros.append(Inspecao.local_id == local_id)
    if numero_processo and numero_processo.strip():
        # contém, sem diferenciar maiúsculas; % e _ digitados pelo usuário valem como texto literal
        esc = chr(92)
        termo = numero_processo.strip().lower()
        for c in (esc, "%", "_"):
            termo = termo.replace(c, esc + c)
        filtros.append(func.lower(Inspecao.numero_processo).like(f"%{termo}%", escape=esc))
    total = db.scalar(select(func.count()).select_from(Inspecao).where(*filtros)) or 0
    consulta = (
        select(Inspecao)
        .where(*filtros)
        .order_by(Inspecao.data_agendamento.desc(), Inspecao.id.desc())
        .offset((pagina - 1) * tamanho)
        .limit(tamanho)
    )
    linhas = list(db.scalars(consulta).unique())
    ids = [i.id for i in linhas]
    contagens = dict(
        db.execute(
            select(FotoVistoria.inspecao_id, func.count()).where(FotoVistoria.inspecao_id.in_(ids)).group_by(FotoVistoria.inspecao_id)
        ).all()
    ) if ids else {}
    for i in linhas:
        i.qtd_fotos = contagens.get(i.id, 0)
    return linhas, total
