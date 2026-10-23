from pydantic import BaseModel, ConfigDict


class LocalIn(BaseModel):
    nome: str
    municipio: str
    tipo: str
    latitude: float
    longitude: float
    ativo: bool = True


class LocalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    municipio: str
    tipo: str
    latitude: float
    longitude: float
    ativo: bool


class LocalResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    municipio: str
