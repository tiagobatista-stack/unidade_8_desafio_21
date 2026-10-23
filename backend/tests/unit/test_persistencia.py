from datetime import date, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Inspecao, ItemInspecao, Local, ModeloItem

AGORA = datetime(2026, 10, 23, 10, 0)


def _local(db, **kw):
    base = dict(nome="L", municipio="M", tipo="T", latitude=-10.0, longitude=-58.0)
    base.update(kw)
    loc = Local(**base)
    db.add(loc)
    db.flush()
    return loc


def _insp(db, local, codigo="INS-001", **kw):
    base = dict(codigo=codigo, local_id=local.id, objetivo="obj", data_agendamento=date(2026, 10, 20),
                status="ABERTA", criado_em=AGORA, atualizado_em=AGORA)
    base.update(kw)
    i = Inspecao(**base)
    db.add(i)
    db.flush()
    return i


def test_latitude_fora_de_mt_rejeitada(db):  # CA26 (camada de banco)
    with pytest.raises(IntegrityError):
        _local(db, latitude=-25.0)


def test_longitude_fora_de_mt_rejeitada(db):
    with pytest.raises(IntegrityError):
        _local(db, longitude=-40.0)


def test_nome_local_unico(db):
    _local(db, nome="A")
    with pytest.raises(IntegrityError):
        _local(db, nome="A")


def test_coordenadas_persistem_como_numero(db):  # CA27
    loc = _local(db, latitude=-10.42318, longitude=-58.71264)
    db.commit()
    db.expire_all()
    lido = db.get(Local, loc.id)
    assert lido.latitude == pytest.approx(-10.42318)


@pytest.mark.parametrize(
    "kw",
    [
        dict(status="XPTO"),
        dict(status="ABERTA", resultado="APROVADA"),  # resultado só em FINALIZADA
        dict(status="FINALIZADA"),  # FINALIZADA exige resultado
        dict(status="CANCELADA"),  # cancelada exige motivo
        dict(data_realizacao=date(2026, 10, 19)),  # anterior ao agendamento
        dict(objetivo=""),
        dict(status="ABERTA", fechado_em=AGORA),
    ],
)
def test_checks_de_inspecao(db, kw):
    loc = _local(db)
    with pytest.raises(IntegrityError):
        _insp(db, loc, **kw)


def test_finalizada_valida_e_cancelada_valida(db):
    loc = _local(db)
    _insp(db, loc, "INS-001", status="FINALIZADA", resultado="APROVADA", fechado_em=AGORA)
    _insp(db, loc, "INS-002", status="CANCELADA", motivo_cancelamento="Sem acesso")


def test_codigo_unico(db):
    loc = _local(db)
    _insp(db, loc, "INS-001")
    with pytest.raises(IntegrityError):
        _insp(db, loc, "INS-001")


def test_fk_local_inexistente_rejeitada(db):  # foreign_keys=ON
    with pytest.raises(IntegrityError):
        db.add(Inspecao(codigo="INS-009", local_id=999, objetivo="o", data_agendamento=date(2026, 10, 1),
                        status="ABERTA", criado_em=AGORA, atualizado_em=AGORA))
        db.flush()


def test_item_situacao_invalida_rejeitada(db):
    loc = _local(db)
    insp = _insp(db, loc)
    with pytest.raises(IntegrityError):
        db.add(ItemInspecao(inspecao_id=insp.id, descricao="x", origem="AVULSO", ordem=1, situacao="TALVEZ"))
        db.flush()


def test_item_cascade_ao_excluir_inspecao(db):
    loc = _local(db)
    insp = _insp(db, loc)
    db.add(ItemInspecao(inspecao_id=insp.id, descricao="x", origem="AVULSO", ordem=1))
    db.flush()
    db.delete(insp)
    db.flush()
    assert db.query(ItemInspecao).count() == 0


def test_item_modelo_exige_modelo_item_id(db):
    loc = _local(db)
    insp = _insp(db, loc)
    with pytest.raises(IntegrityError):
        db.add(ItemInspecao(inspecao_id=insp.id, descricao="x", origem="MODELO", ordem=1))
        db.flush()


def test_seed_cria_estado_esperado(exemplos):
    db = exemplos
    assert db.query(Local).count() == 4
    assert db.query(ModeloItem).count() == 6
    assert db.query(Inspecao).count() == 5
    res = {i.codigo: i.resultado for i in db.query(Inspecao)}
    assert res["INS-001"] == "APROVADA"
    assert res["INS-002"] == "APROVADA_COM_RESSALVAS"
    assert res["INS-003"] == "REPROVADA"
    assert res["INS-004"] is None and res["INS-005"] is None
