import type { Detalhe } from "./tipos";

export class ApiErro extends Error {
  constructor(
    public status: number,
    public codigo: string,
    mensagem: string,
    public detalhes: Detalhe[] = [],
  ) {
    super(mensagem);
  }
}

/** Vazio = mesma origem (proxy do Vite). Em produção estática: VITE_API_URL=http://127.0.0.1:8000 */
export const API_BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
const BASE = `${API_BASE}/api/v1`;

/** Converte um caminho devolvido pela API (ex.: /api/v1/...) em URL utilizável pelo navegador. */
export const urlApi = (caminho: string) => (caminho.startsWith("/") ? API_BASE + caminho : caminho);

export async function requisicao<T>(caminho: string, init?: RequestInit): Promise<T> {
  let resposta: Response;
  try {
    resposta = await fetch(BASE + caminho, init);
  } catch {
    throw new ApiErro(0, "SEM_CONEXAO", "Não foi possível conectar à API.");
  }
  if (resposta.status === 204) return undefined as T;
  let corpo: any = null;
  try {
    corpo = await resposta.json();
  } catch {
    /* corpo vazio ou não JSON */
  }
  if (!resposta.ok) {
    const e = corpo?.erro;
    throw new ApiErro(resposta.status, e?.codigo ?? "ERRO_HTTP", e?.mensagem ?? "Falha na requisição.", e?.detalhes ?? []);
  }
  return corpo as T;
}

export const json = (metodo: string, corpo: unknown): RequestInit => ({
  method: metodo,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(corpo),
});

export function paraErro(e: unknown): ApiErro {
  return e instanceof ApiErro ? e : new ApiErro(0, "ERRO_DESCONHECIDO", "Ocorreu um erro inesperado.");
}
