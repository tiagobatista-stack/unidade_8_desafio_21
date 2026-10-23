from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.domain.contato import formatar_telefone
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
    latitude: float
    longitude: float
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


class LocalOut(_EnderecoOut):
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


class EmpreendimentoOut(_EnderecoOut):
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
