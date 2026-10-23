import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"


def database_url() -> str:
    return os.environ.get("DATABASE_URL") or f"sqlite:///{(DATA_DIR / 'inspecoes.db').as_posix()}"


def fotos_dir() -> Path:
    return Path(os.environ.get("FOTOS_DIR") or (DATA_DIR / "fotos"))
