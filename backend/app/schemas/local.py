from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.domain.contato import formatar_telefone
from app.domain.coordenadas import formatar_gms, formatar_par_gms
from app.domain.documento import formatar_cep, formatar_cpf_cnpj


class ProprietarioIn(BaseModel):
    nome: str
    telefone: str | None = None
    cpf_cnpj: str | None = None
    corr_logradouro: str | None = None
    corr_numero: str | None = None
    corr_complemento: str | None = None
    corr_bairro: str | None = None
    corr_municipio: str | None = None
    corr_uf: str | None = None
    corr_cep: str | None = None
    # Atalho "Mesmo endereço do empreendimento": o serviço copia logradouro, município, UF e CEP do Local.
    correspondencia_mesmo_endereco: bool = False


class ProprietarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    telefone: str | None  # só dígitos
    cpf_cnpj: str | None = None  # só dígitos
    corr_logradouro: str | None = None
    corr_numero: str | None = None
    corr_complemento: str | None = None
    corr_bairro: str | None = None
    corr_municipio: str | None = None
    corr_uf: str | None = None
    corr_cep: str | None = None  # só dígitos

    @computed_field  # type: ignore[prop-decorator]
    @property
    def telefone_formatado(self) -> str | None:
        return formatar_telefone(self.telefone)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cpf_cnpj_formatado(self) -> str | None:
        return formatar_cpf_cnpj(self.cpf_cnpj)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def corr_cep_formatado(self) -> str | None:
        return formatar_cep(self.corr_cep)


class LocalIn(BaseModel):
    nome: str
    municipio: str
    tipo: str
    latitude: float | None = None  # decimal; ou informe latitude_gms (o GMS vale se vier os dois)
    longitude: float | None = None
    latitude_gms: str | None = None  # ex.: 11° 46' 34" S
    longitude_gms: str | None = None  # ex.: 59° 05' 12" W
    ativo: bool = True
    numero_car: str | None = None
    logradouro: str | None = None
    uf: str | None = None  # padrão MT
    cep: str | None = None
    proprietarios: list[ProprietarioIn] = Field(default_factory=list)


class _EnderecoOut(BaseModel):
    logradouro: str | None = None
    uf: str | None = None
    cep: str | None = None  # só dígitos

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cep_formatado(self) -> str | None:
        return formatar_cep(self.cep)


class _CoordenadasOut(_EnderecoOut):
    latitude: float
    longitude: float

    @computed_field  # type: ignore[prop-decorator]
    @property
    def latitude_gms(self) -> str:
        return formatar_gms(self.latitude, "latitude")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def longitude_gms(self) -> str:
        return formatar_gms(self.longitude, "longitude")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def coordenadas_gms(self) -> str:
        return formatar_par_gms(self.latitude, self.longitude)


class LocalOut(_CoordenadasOut):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    municipio: str
    tipo: str
    ativo: bool
    numero_car: str | None = None
    proprietarios: list[ProprietarioOut] = Field(default_factory=list)


class EmpreendimentoOut(_CoordenadasOut):
    """Dados do empreendimento exibidos na inspeção (cópia do fechamento quando finalizada)."""

    nome: str
    municipio: str
    tipo: str
    numero_car: str | None = None
    proprietarios: list[ProprietarioOut] = Field(default_factory=list)


class LocalResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    municipio: str
