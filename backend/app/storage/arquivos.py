"""Armazenamento de fotos em disco (ADR-002). Os caminhos são sempre gerados pelo sistema."""
import uuid
from pathlib import Path
from typing import Protocol

from app import config


class ArmazenamentoArquivos(Protocol):
    def salvar(self, inspecao_id: int, versao: str, extensao: str, conteudo: bytes) -> str: ...
    def ler(self, caminho: str) -> bytes | None: ...
    def remover(self, caminho: str) -> None: ...
    def existe(self, caminho: str) -> bool: ...
    def listar(self) -> list[str]: ...


class ArmazenamentoDisco:
    def __init__(self, base: Path):
        self.base = Path(base).resolve()

    def _resolver(self, caminho: str) -> Path:
        destino = (self.base / caminho).resolve()
        if self.base not in destino.parents:
            raise ValueError("caminho fora do diretório de fotos")
        return destino

    def salvar(self, inspecao_id: int, versao: str, extensao: str, conteudo: bytes) -> str:
        caminho = f"{int(inspecao_id)}/{versao}/{uuid.uuid4().hex}.{extensao}"
        destino = self._resolver(caminho)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)
        return caminho

    def ler(self, caminho: str) -> bytes | None:
        destino = self._resolver(caminho)
        return destino.read_bytes() if destino.is_file() else None

    def remover(self, caminho: str) -> None:
        self._resolver(caminho).unlink(missing_ok=True)

    def existe(self, caminho: str) -> bool:
        return self._resolver(caminho).is_file()

    def listar(self) -> list[str]:
        if not self.base.exists():
            return []
        return sorted(p.relative_to(self.base).as_posix() for p in self.base.rglob("*") if p.is_file())


def get_storage() -> ArmazenamentoArquivos:
    return ArmazenamentoDisco(config.fotos_dir())
