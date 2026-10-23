import { json, requisicao, urlApi } from "./cliente";
import type {
  FiltrosLista,
  Foto,
  Indicadores,
  InspecaoDetalhe,
  InspecaoResumo,
  Item,
  Local,
  Pagina,
  Situacao,
} from "./tipos";

const qs = (p: Record<string, string | number | undefined>) => {
  const u = new URLSearchParams();
  Object.entries(p).forEach(([k, v]) => v !== undefined && v !== "" && u.set(k, String(v)));
  const s = u.toString();
  return s ? `?${s}` : "";
};

export const api = {
  indicadores: () => requisicao<Indicadores>("/indicadores"),
  carregarExemplos: () => requisicao<{ locais: number; inspecoes: number; fotos: number }>("/utilitarios/carregar-exemplos", { method: "POST" }),
  locais: () => requisicao<Pagina<Local>>("/locais"),
  inspecoes: (f: FiltrosLista) => requisicao<Pagina<InspecaoResumo>>(`/inspecoes${qs({ ...f, tamanho: 100 })}`),
  inspecao: (id: number) => requisicao<InspecaoDetalhe>(`/inspecoes/${id}`),
  criarInspecao: (dados: { local_id: number; data_agendamento: string; objetivo: string; observacoes?: string }) =>
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
