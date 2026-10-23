from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import FotoVistoria, Inspecao, ItemInspecao

AGORA = datetime(2026, 10, 23, 10, 0)


def foto(insp_id, n=1, **kw):
    base = dict(
        inspecao_id=insp_id, nome_original="a.jpg", arquivo_path=f"{insp_id}/original/{n}.jpg",
        miniatura_path=f"{insp_id}/miniatura/{n}.jpg", mime_type="image/jpeg", tamanho_bytes=10,
        largura=1, altura=1, hash_sha256=f"h{n}", anotacao="nota", ordem=n, criado_em=AGORA,
    )
    base.update(kw)
    return FotoVistoria(**base)


def test_cascade_ao_excluir_inspecao(exemplos):
    db = exemplos
    insp = db.query(Inspecao).filter_by(codigo="INS-004").one()
    db.add(foto(insp.id))
    db.flush()
    db.delete(insp)
    db.flush()
    assert db.query(FotoVistoria).count() == 0


def test_set_null_ao_excluir_item(exemplos):
    db = exemplos
    insp = db.query(Inspecao).filter_by(codigo="INS-004").one()
    item = ItemInspecao(inspecao_id=insp.id, descricao="avulso", origem="AVULSO", ordem=9)
    db.add(item)
    db.flush()
    f = foto(insp.id, item_inspecao_id=item.id)
    db.add(f)
    db.flush()
    db.execute(ItemInspecao.__table__.delete().where(ItemInspecao.id == item.id))
    db.expire_all()
    assert db.get(FotoVistoria, f.id).item_inspecao_id is None


def test_hash_unico_por_inspecao_mas_repetivel_entre_inspecoes(exemplos):
    db = exemplos
    a = db.query(Inspecao).filter_by(codigo="INS-004").one()
    b = db.query(Inspecao).filter_by(codigo="INS-005").one()
    db.add(foto(a.id, 1, hash_sha256="igual"))
    db.add(foto(b.id, 2, hash_sha256="igual"))
    db.flush()
    db.add(foto(a.id, 3, hash_sha256="igual"))
    with pytest.raises(IntegrityError):
        db.flush()


@pytest.mark.parametrize(
    "kw",
    [
        dict(mime_type="image/gif"),
        dict(tamanho_bytes=0),
        dict(tamanho_bytes=5_242_881),
        dict(anotacao=""),
        dict(anotacao="a" * 1001),
        dict(legenda="l" * 201),
    ],
)
def test_checks_de_foto(exemplos, kw):
    db = exemplos
    insp = db.query(Inspecao).filter_by(codigo="INS-004").one()
    db.add(foto(insp.id, **kw))
    with pytest.raises(IntegrityError):
        db.flush()


def test_arquivo_path_unico(exemplos):
    db = exemplos
    insp = db.query(Inspecao).filter_by(codigo="INS-004").one()
    db.add(foto(insp.id, 1))
    db.add(foto(insp.id, 2, arquivo_path=f"{insp.id}/original/1.jpg"))
    with pytest.raises(IntegrityError):
        db.flush()
