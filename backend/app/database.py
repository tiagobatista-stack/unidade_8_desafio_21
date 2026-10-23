from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import config


class Base(DeclarativeBase):
    pass


def criar_engine(url: str | None = None) -> Engine:
    url = url or config.database_url()
    kwargs: dict = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url or url == "sqlite://":
            kwargs["poolclass"] = StaticPool
        else:
            path = url.replace("sqlite:///", "", 1)
            if path:
                import pathlib

                pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _pragma(dbapi_conn, _):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return engine


_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def configurar(engine: Engine) -> None:
    global _engine, _SessionLocal
    _engine = engine
    _SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_engine() -> Engine:
    if _engine is None:
        configurar(criar_engine())
    return _engine


def get_db() -> Iterator[Session]:
    get_engine()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _garantir_colunas(engine: Engine) -> None:
    """Migração leve (sem Alembic): acrescenta colunas novas a bancos criados por versões anteriores."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    tabelas = set(insp.get_table_names())
    novas = {  # tabela -> [(coluna, definição)]
        "inspecao": [("numero_processo", "VARCHAR(60)"), ("empreendimento_json", "TEXT"), ("numero_relatorio", "VARCHAR(20)")],
        "local": [("numero_car", "VARCHAR(60)")],
    }
    indices = [  # SQLite não aceita UNIQUE em ADD COLUMN: o índice único é criado à parte
        ("inspecao", "CREATE UNIQUE INDEX IF NOT EXISTS ux_inspecao_numero_relatorio ON inspecao (numero_relatorio)"),
    ]
    for tabela, colunas_novas in novas.items():
        if tabela not in tabelas:
            continue  # tabela nova: o create_all já a cria completa
        existentes = {c["name"] for c in insp.get_columns(tabela)}
        for coluna, definicao in colunas_novas:
            if coluna not in existentes:
                with engine.begin() as con:
                    con.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}"))
    for tabela, ddl in indices:
        if tabela in tabelas:
            with engine.begin() as con:
                con.execute(text(ddl))


def criar_tabelas() -> None:
    from app import models  # noqa: F401  registra os modelos

    engine = get_engine()
    _garantir_colunas(engine)  # antes do create_all: tabelas novas já nascem completas
    Base.metadata.create_all(engine)
