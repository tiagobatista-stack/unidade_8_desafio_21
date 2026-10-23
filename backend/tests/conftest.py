from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import clock, database
from app.main import criar_app


@pytest.fixture(autouse=True)
def relogio_fixo():
    clock.fixar_hoje(date(2026, 10, 23))
    yield
    clock.fixar_hoje(None)


@pytest.fixture
def engine(tmp_path, monkeypatch):
    monkeypatch.setenv("FOTOS_DIR", str(tmp_path / "fotos"))
    eng = database.criar_engine("sqlite://")
    database.configurar(eng)
    database.criar_tabelas()
    yield eng
    eng.dispose()


@pytest.fixture
def client(engine):
    with TestClient(criar_app()) as c:
        yield c


@pytest.fixture
def db(engine):
    with Session(engine, expire_on_commit=False) as s:
        yield s


@pytest.fixture
def exemplos(db):
    from app.seed.dados_exemplo import carregar

    carregar(db)
    db.commit()
    return db
