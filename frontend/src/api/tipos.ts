export type Status = "ABERTA" | "EM_ANDAMENTO" | "FINALIZADA" | "CANCELADA";
export type Situacao = "NAO_RESPONDIDO" | "CONFORME" | "NAO_CONFORME" | "NAO_SE_APLICA";

export interface Detalhe {
  campo: string;
  mensagem: string;
}

export interface Pagina<T> {
  dados: T[];
  total: number;
  pagina: number;
  tamanho: number;
}

export interface Proprietario {
  nome: string; // nome / razão social
  telefone: string | null; // só dígitos
  telefone_formatado: string | null;
  cpf_cnpj?: string | null; // só dígitos
  cpf_cnpj_formatado?: string | null;
  corr_logradouro?: string | null;
  corr_numero?: string | null;
  corr_complemento?: string | null;
  corr_bairro?: string | null;
  corr_municipio?: string | null;
  corr_uf?: string | null;
  corr_cep?: string | null; // só dígitos
  corr_cep_formatado?: string | null;
}

/** Endereço do empreendimento e coordenadas em GMS, como a API devolve (R4). */
export interface EnderecoCoordenadas {
  logradouro?: string | null;
  uf?: string | null;
  cep?: string | null; // só dígitos
  cep_formatado?: string | null;
  latitude_gms?: string;
  longitude_gms?: string;
  coordenadas_gms?: string; // LAT 11° 46' 34" S | LONG 59° 05' 12" W
}

export interface Local extends EnderecoCoordenadas {
  id: number;
  nome: string;
  municipio: string;
  tipo: string;
  latitude: number;
  longitude: number;
  ativo: boolean;
  numero_car: string | null;
  proprietarios: Proprietario[];
}

/** Dados do empreendimento na inspeção (cópia do fechamento quando finalizada). */
export interface Empreendimento extends EnderecoCoordenadas {
  nome: string;
  municipio: string;
  tipo: string;
  latitude: number;
  longitude: number;
  numero_car: string | null;
  proprietarios: Proprietario[];
}

export interface InspecaoResumo {
  id: number;
  codigo: string;
  numero_processo: string | null;
  local: { id: number; nome: string; municipio: string };
  objetivo: string;
  data_agendamento: string;
  data_realizacao: string | null;
  status: Status;
  resultado: string | null;
  qtd_fotos: number;
}

export interface Item {
  id: number;
  descricao: string;
  critico: boolean;
  situacao: Situacao;
  observacao: string | null;
  origem: "MODELO" | "AVULSO";
  ordem: number;
  qtd_fotos: number;
}

export interface Foto {
  id: number;
  inspecao_id: number;
  item_id: number | null;
  nome_original: string;
  mime_type: string;
  tamanho_bytes: number;
  largura: number;
  altura: number;
  legenda: string | null;
  anotacao: string;
  ordem: number;
  url_miniatura: string;
  url_original: string;
}

export interface CampoCapaApi {
  rotulo: string;
  valor: string; // o valor ou "Não informado"
  copiar: string;
  ausente: boolean;
  faltando: boolean; // vazio e obrigatório para a SEMA
}

export interface BlocoCapaApi {
  chave: string;
  titulo: string;
  texto: string;
  campos: CampoCapaApi[];
}

/** Dados para a capa e a lavratura (GET /inspecoes/{id}/dados-capa). */
export interface DadosParaCapa {
  codigo: string;
  protocolo: string | null;
  blocos: BlocoCapaApi[];
  texto_completo: string;
  campos_faltando: number;
}

export interface InspecaoDetalhe extends DadosCapa {
  id: number;
  codigo: string;
  numero_processo: string | null;
  empreendimento: Empreendimento;
  numero_relatorio: string | null;
  campos_editaveis: string[];
  fechamento_bloqueado_motivo: string | null;
  registro_bloqueado_motivo: string | null;
  local: Local;
  objetivo: string;
  observacoes: string | null;
  observacoes_vistoria: string | null;
  data_agendamento: string;
  data_realizacao: string | null;
  status: Status;
  resultado: string | null;
  motivo_cancelamento: string | null;
  fechado_em: string | null;
  itens: Item[];
  fotos: Foto[];
  resumo_itens: { total: number; respondidos: number; nao_conformes: number };
}

export interface Indicadores {
  inspecoes: number;
  pendencias: number;
  finalizadas: number;
  gerado_em: string;
}

export interface NovoProprietario {
  nome: string;
  telefone: string | null;
  cpf_cnpj?: string;
  corr_logradouro?: string;
  corr_numero?: string;
  corr_complemento?: string;
  corr_bairro?: string;
  corr_municipio?: string;
  corr_uf?: string;
  corr_cep?: string;
  correspondencia_mesmo_endereco?: boolean; // a API copia logradouro, município, UF e CEP do empreendimento
}

export interface NovoLocal {
  nome: string; // nome fantasia / denominação
  municipio: string;
  tipo: string;
  latitude?: number; // decimal, ou latitude_gms (a API converte)
  longitude?: number;
  latitude_gms?: string;
  longitude_gms?: string;
  numero_car?: string | null;
  logradouro?: string;
  uf?: string;
  cep?: string;
  proprietarios?: NovoProprietario[];
}

export interface MembroEquipe {
  nome: string;
  cargo: string | null;
  orgao: string | null;
}

export interface AtoLavrado {
  id: number;
  tipo: string;
  numero: string | null;
}

/** Dados da capa da SEMA que a inspeção guarda (R4). */
export interface DadosCapa {
  interessado_orgao?: string | null;
  interessado_unidade?: string | null;
  interessado_comarca?: string | null;
  interessado_requerente?: string | null;
  assunto_tipo?: string | null;
  assunto_outro?: string | null;
  providencias_texto?: string | null;
  numero_relatorio_sema?: string | null;
  equipe?: MembroEquipe[];
  atos?: AtoLavrado[];
}

export interface FiltrosLista {
  status?: string[];
  numero_processo?: string;
  data_inicio?: string;
  data_fim?: string;
}

export interface ItemRelatorio {
  numero: number;
  descricao: string;
  critico: boolean;
  situacao: Situacao;
  observacao: string | null;
  critico_nao_conforme: boolean;
}

export interface FotoRelatorio {
  numero: number;
  url_original: string;
  nome_original: string;
  legenda: string | null;
  anotacao: string;
  item_numero: number | null;
  item_descricao: string | null;
  data_captura: string | null;
}

export interface Relatorio {
  previa: boolean;
  marca_dagua: string | null;
  numero_relatorio: string | null;
  titulo: string;
  identificacao: {
    codigo: string;
    numero_processo: string | null;
    status: Status;
    resultado: string | null;
    data_agendamento: string;
    data_realizacao: string | null;
    fechado_em: string | null;
  };
  empreendimento: Empreendimento;
  objetivo: { objetivo: string; observacoes: string | null; observacoes_vistoria: string | null };
  checklist: {
    itens: ItemRelatorio[];
    totais: { total: number; respondidos: number; conformes: number; nao_conformes: number; nao_aplicaveis: number; nao_respondidos: number };
  };
  fotos: FotoRelatorio[];
  conclusao: { resultado: string | null; regra: string };
}
