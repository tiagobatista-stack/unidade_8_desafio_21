import { json, requisicao, urlApi } from "./cliente";
import type {
  FiltrosLista,
  Foto,
  Indicadores,
  InspecaoDetalhe,
  InspecaoResumo,
  Item,
  Local,
  NovoLocal,
  DadosParaCapa,
  Relatorio,
  Pagina,
  Situacao,
} from "./tipos";

const qs = (p: Record<string, string | number | string[] | undefined>) => {
  const u = new URLSearchParams();
  Object.entries(p).forEach(([k, v]) => {
    if (Array.isArray(v)) v.forEach((x) => u.append(k, x)); // status repetido: ?status=A&status=B
    else if (v !== undefined && v !== "") u.set(k, String(v));
  });
  const s = u.toString();
  return s ? `?${s}` : "";
};

export const api = {
  indicadores: () => requisicao<Indicadores>("/indicadores"),
  carregarExemplos: () => requisicao<{ locais: number; inspecoes: number; fotos: number }>("/utilitarios/carregar-exemplos", { method: "POST" }),
  locais: () => requisicao<Pagina<Local>>("/locais"),
  local: (id: number) => requisicao<Local>(`/locais/${id}`),
  criarLocal: (dados: NovoLocal) => requisicao<Local>("/locais", json("POST", dados)),
  atualizarLocal: (id: number, dados: NovoLocal) => requisicao<Local>(`/locais/${id}`, json("PUT", dados)),
  inspecoes: (f: FiltrosLista) => requisicao<Pagina<InspecaoResumo>>(`/inspecoes${qs({ ...f, tamanho: 100 })}`),
  inspecao: (id: number) => requisicao<InspecaoDetalhe>(`/inspecoes/${id}`),
  dadosCapa: (id: number) => requisicao<DadosParaCapa>(`/inspecoes/${id}/dados-capa`),
  relatorio: (id: number) => requisicao<Relatorio>(`/inspecoes/${id}/relatorio`),
  criarInspecao: (dados: { numero_processo: string; local_id: number; data_agendamento: string; objetivo: string; observacoes?: string } & Record<string, unknown>) =>
    requisicao<InspecaoDetalhe>("/inspecoes", json("POST", dados)),
  editarInspecao: (id: number, dados: Record<string, unknown>) =>
    requisicao<InspecaoDetalhe>(`/inspecoes/${id}`, json("PATCH", dados)),
  cancelar: (id: number, motivo: string) => requisicao<InspecaoDetalhe>(`/inspecoes/${id}/cancelar`, json("POST", { motivo })),
  fechar: (id: number) => requisicao<InspecaoDetalhe>(`/inspecoes/${id}/fechar`, { method: "POST" }),
  atualizarItem: (id: number, itemId: number, dados: { situacao?: Situacao; observacao?: string | null }) =>
    requisicao<Item>(`/inspecoes/${id}/itens/${itemId}`, json("PATCH", dados)),
  adicionarItem: (id: number, descricao: string) => requisicao<Item>(`/inspecoes/${id}/itens`, json("POST", { descricao })),
  removerItem: (id: number, itemId: number) => requisicao<void>(`/inspecoes/${id}/itens/${itemId}`, { method: "DELETE" }),
  enviarFoto: (id: number, form: FormData) => requisicao<Foto>(`/inspecoes/${id}/fotos`, { method: "POST", body: form }),
  editarFoto: (id: number, fotoId: number, dados: Record<string, unknown>) =>
    requisicao<Foto>(`/inspecoes/${id}/fotos/${fotoId}`, json("PATCH", dados)),
  excluirFoto: (id: number, fotoId: number) => requisicao<void>(`/inspecoes/${id}/fotos/${fotoId}`, { method: "DELETE" }),
};

export const URL_CSV = urlApi("/api/v1/exportacao/inspecoes.csv");
export const URL_CSV_ITENS = urlApi("/api/v1/exportacao/itens.csv");
