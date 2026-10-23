import { render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import type { InspecaoDetalhe, InspecaoResumo, Item, Foto } from "../api/tipos";

export interface Chamada {
  metodo: string;
  caminho: string;
  consulta: URLSearchParams;
  corpo: any;
}
export interface Resposta {
  status?: number;
  corpo?: any;
}
export type Rota = (c: Chamada) => Resposta | undefined;

/** Substitui o fetch global por um roteador em memória. Retorna o registro de chamadas. */
export function instalarApi(...rotas: Rota[]) {
  const chamadas: Chamada[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const u = new URL(url, "http://localhost");
      let corpo: any = init?.body ?? null;
      if (typeof corpo === "string") corpo = JSON.parse(corpo);
      const c: Chamada = {
        metodo: (init?.method ?? "GET").toUpperCase(),
        caminho: u.pathname.replace("/api/v1", ""),
        consulta: u.searchParams,
        corpo,
      };
      chamadas.push(c);
      for (const r of rotas) {
        const resp = r(c);
        if (resp) {
          const status = resp.status ?? 200;
          return { ok: status < 400, status, json: async () => resp.corpo ?? null };
        }
      }
      return { ok: false, status: 404, json: async () => ({ erro: { codigo: "NAO_ENCONTRADO", mensagem: "Recurso não encontrado.", detalhes: [] } }) };
    }),
  );
  return chamadas;
}

export const rota = (metodo: string, caminho: string | RegExp, resposta: Resposta | ((c: Chamada) => Resposta)): Rota =>
  (c) => {
    if (c.metodo !== metodo) return undefined;
    const bate = typeof caminho === "string" ? c.caminho === caminho : caminho.test(c.caminho);
    if (!bate) return undefined;
    return typeof resposta === "function" ? resposta(c) : resposta;
  };

export const erroApi = (status: number, codigo: string, mensagem: string, detalhes: { campo: string; mensagem: string }[] = []): Resposta => ({
  status,
  corpo: { erro: { codigo, mensagem, detalhes } },
});

export function renderizar(caminho = "/") {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[caminho]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

export const local = { id: 1, nome: "Fazenda Horizonte Azul", municipio: "Vila Nova do Cerrado", tipo: "Propriedade rural", latitude: -10.42318, longitude: -58.71264, ativo: true };

export function item(id: number, parcial: Partial<Item> = {}): Item {
  return { id, descricao: `Item ${id}`, critico: false, situacao: "NAO_RESPONDIDO", observacao: null, origem: "MODELO", ordem: id, qtd_fotos: 0, ...parcial };
}

export function foto(id: number, parcial: Partial<Foto> = {}): Foto {
  return {
    id, inspecao_id: 4, item_id: null, nome_original: `f${id}.jpg`, mime_type: "image/jpeg", tamanho_bytes: 10, largura: 800, altura: 600,
    legenda: null, anotacao: `Anotação ${id}`, ordem: id, url_miniatura: `/api/v1/inspecoes/4/fotos/${id}/arquivo?versao=miniatura`,
    url_original: `/api/v1/inspecoes/4/fotos/${id}/arquivo?versao=original`, ...parcial,
  };
}

export function inspecao(parcial: Partial<InspecaoDetalhe> = {}): InspecaoDetalhe {
  const itens = parcial.itens ?? [item(1), item(2), item(3)];
  return {
    id: 4, codigo: "INS-004", local, objetivo: "Vistoria de rotina", observacoes: null, observacoes_vistoria: null,
    data_agendamento: "2026-10-20", data_realizacao: null, status: "ABERTA", resultado: null, motivo_cancelamento: null,
    fechado_em: null, itens, fotos: [],
    resumo_itens: { total: itens.length, respondidos: itens.filter((i) => i.situacao !== "NAO_RESPONDIDO").length, nao_conformes: itens.filter((i) => i.situacao === "NAO_CONFORME").length },
    ...parcial,
  };
}

export function resumo(id: number, parcial: Partial<InspecaoResumo> = {}): InspecaoResumo {
  return {
    id, codigo: `INS-00${id}`, local: { id: 1, nome: "Fazenda Horizonte Azul", municipio: "Vila Nova do Cerrado" }, objetivo: "x",
    data_agendamento: "2026-10-20", data_realizacao: null, status: "ABERTA", resultado: null, qtd_fotos: 0, ...parcial,
  };
}

export const pagina = <T,>(dados: T[]) => ({ corpo: { dados, total: dados.length, pagina: 1, tamanho: 100 } });
