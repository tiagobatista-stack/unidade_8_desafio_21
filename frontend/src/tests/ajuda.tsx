import { render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import type { InspecaoDetalhe, InspecaoResumo, Item, Foto, Local, Relatorio } from "../api/tipos";

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

export const local: Local = { id: 1, nome: "Fazenda Horizonte Azul", municipio: "Vila Nova do Cerrado", tipo: "Propriedade rural", latitude: -10.42318, longitude: -58.71264, ativo: true, numero_car: null, proprietarios: [] };

export const empreendimentoDe = (l: Local) => ({
  nome: l.nome, municipio: l.municipio, tipo: l.tipo, latitude: l.latitude, longitude: l.longitude,
  numero_car: l.numero_car, proprietarios: l.proprietarios,
});

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

/** Espelha o que a API devolve em `campos_editaveis` por status. */
const CAPA = ["assunto_outro", "assunto_tipo", "atos", "equipe", "interessado_comarca", "interessado_orgao", "interessado_requerente", "interessado_unidade", "numero_relatorio_sema", "providencias_texto"];
const EDITAVEIS: Record<string, string[]> = {
  ABERTA: ["data_agendamento", "local_id", "numero_processo", "objetivo", "observacoes", "observacoes_vistoria", ...CAPA],
  EM_ANDAMENTO: ["data_realizacao", "numero_processo", "observacoes", "observacoes_vistoria", ...CAPA],
  FINALIZADA: [],
  CANCELADA: [],
};

export const MSG_NAO_INICIADA =
  "A inspeção ainda não foi iniciada. Registre a situação de pelo menos um item do checklist antes de fechar.";

export function inspecao(parcial: Partial<InspecaoDetalhe> = {}): InspecaoDetalhe {
  const itens = parcial.itens ?? [item(1), item(2), item(3)];
  return {
    id: 4, codigo: "INS-004", numero_processo: "SEMA-PRO-2026/12345", campos_editaveis: EDITAVEIS[parcial.status ?? "ABERTA"],
    // como a API: só em ABERTA há motivo para não fechar; o aviso de agendamento futuro vem de cada teste
    fechamento_bloqueado_motivo: (parcial.status ?? "ABERTA") === "ABERTA" ? MSG_NAO_INICIADA : null,
    registro_bloqueado_motivo: null, empreendimento: empreendimentoDe(parcial.local ?? local),
    numero_relatorio: (parcial.status ?? "ABERTA") === "FINALIZADA" ? "0001/2026" : null, local, objetivo: "Vistoria de rotina", observacoes: null, observacoes_vistoria: null,
    data_agendamento: "2026-10-20", data_realizacao: null, status: "ABERTA", resultado: null, motivo_cancelamento: null,
    fechado_em: null, itens, fotos: [],
    resumo_itens: { total: itens.length, respondidos: itens.filter((i) => i.situacao !== "NAO_RESPONDIDO").length, nao_conformes: itens.filter((i) => i.situacao === "NAO_CONFORME").length },
    ...parcial,
  };
}

export function resumo(id: number, parcial: Partial<InspecaoResumo> = {}): InspecaoResumo {
  return {
    id, codigo: `INS-00${id}`, numero_processo: `SEMA-PRO-2026/1000${id}`, local: { id: 1, nome: "Fazenda Horizonte Azul", municipio: "Vila Nova do Cerrado" }, objetivo: "x",
    data_agendamento: "2026-10-20", data_realizacao: null, status: "ABERTA", resultado: null, qtd_fotos: 0, ...parcial,
  };
}

export const pagina = <T,>(dados: T[]) => ({ corpo: { dados, total: dados.length, pagina: 1, tamanho: 100 } });

/** Corpo do relatório de uma inspeção finalizada, como a API devolve; cada teste sobrescreve o que precisa. */
export function relatorio(parcial: Partial<Relatorio> = {}): Relatorio {
  return {
    previa: false, marca_dagua: null,
    cabecalho: {
      protocolo: "SEMA-PRO-2026/12345", codigo: "INS-004", ref_interna: "0004/2026", numero_relatorio_sema: null,
      linha: "Protocolo nº SEMA-PRO-2026/12345 | Inspeção INS-004 | Ref. interna 0004/2026",
    },
    constatacoes: {
      relato: { data_realizacao: "2026-10-21", observacoes_vistoria: "Texto da vistoria" },
      checklist: {
        itens: [
          { numero: 1, descricao: "Licença ambiental", critico: true, situacao: "CONFORME", observacao: null, critico_nao_conforme: false },
          { numero: 2, descricao: "Destinação de efluentes", critico: true, situacao: "NAO_CONFORME", observacao: "Transbordando", critico_nao_conforme: true },
          { numero: 3, descricao: "Sinalização", critico: false, situacao: "NAO_CONFORME", observacao: "Placa gasta", critico_nao_conforme: false },
          { numero: 4, descricao: "Resíduos", critico: false, situacao: "NAO_SE_APLICA", observacao: null, critico_nao_conforme: false },
        ],
        totais: { total: 4, respondidos: 4, conformes: 1, nao_conformes: 2, nao_aplicaveis: 1, nao_respondidos: 0 },
      },
      fotos: [
        { numero: 1, url_original: "/api/v1/inspecoes/4/fotos/1/arquivo?versao=original", nome_original: "a.jpg", legenda: "Caixa separadora",
          anotacao: "Transbordamento junto à base.", item_numero: 2, item_descricao: "Destinação de efluentes", data_captura: "2026-10-21T09:30:00" },
        { numero: 2, url_original: "/api/v1/inspecoes/4/fotos/2/arquivo?versao=original", nome_original: "b.jpg", legenda: null,
          anotacao: "Vista geral.", item_numero: null, item_descricao: null, data_captura: null },
        { numero: 3, url_original: "/api/v1/inspecoes/4/fotos/3/arquivo?versao=original", nome_original: "c.jpg", legenda: null,
          anotacao: "Terceira foto.", item_numero: null, item_descricao: null, data_captura: null },
      ],
    },
    providencias: {
      texto: "Notificado o responsável.",
      atos: [{ tipo: "Notificação", numero: null, rotulo: "Notificação – nº a definir" }, { tipo: "Auto de Infração", numero: "AI-0001/2030", rotulo: "Auto de Infração – nº AI-0001/2030" }],
    },
    conclusao: { resultado: "REPROVADA", regra: "1 item crítico não conforme" },
    ...parcial,
  };
}
