from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.domain.contato import formatar_telefone


class ProprietarioIn(BaseModel):
    nome: str
    telefone: str | None = None


class ProprietarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    telefone: str | None  # só dígitos

    @computed_field  # type: ignore[prop-decorator]
    @property
    def telefone_formatado(self) -> str | None:
        return formatar_telefone(self.telefone)


class LocalIn(BaseModel):
    nome: str
    municipio: str
    tipo: str
    latitude: float
    longitude: float
    ativo: bool = True
    numero_car: str | None = None
    proprietarios: list[ProprietarioIn] = Field(default_factory=list)


class LocalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    municipio: str
    tipo: str
    latitude: float
    longitude: float
    ativo: bool
    numero_car: str | None = None
    proprietarios: list[ProprietarioOut] = Field(default_factory=list)


class EmpreendimentoOut(BaseModel):
    """Dados do empreendimento exibidos na inspeção (cópia do fechamento quando finalizada)."""

    nome: str
    municipio: str
    tipo: str
    latitude: float
    longitude: float
    numero_car: str | None = None
    proprietarios: list[ProprietarioOut] = Field(default_factory=list)


class LocalResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    municipio: str
