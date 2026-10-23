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

export interface Local {
  id: number;
  nome: string;
  municipio: string;
  tipo: string;
  latitude: number;
  longitude: number;
  ativo: boolean;
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

export interface InspecaoDetalhe {
  id: number;
  codigo: string;
  numero_processo: string | null;
  campos_editaveis: string[];
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

export interface NovoLocal {
  nome: string;
  municipio: string;
  tipo: string;
  latitude: number;
  longitude: number;
}

export interface FiltrosLista {
  status?: string[];
  numero_processo?: string;
  data_inicio?: string;
  data_fim?: string;
}
