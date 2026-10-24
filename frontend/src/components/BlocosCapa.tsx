import type { DadosCapa } from "../api/tipos";
import { ASSUNTOS, ASSUNTO_OUTRO, TIPOS_ATO } from "../constantes";
import { VAZIO } from "../utils/formatar";

/** Blocos da capa da SEMA nos formulários Nova inspeção e Editar inspeção: interessado, assunto, equipe e providências. */
export interface LinhaEquipe { chave: number; nome: string; cargo: string; orgao: string }
export interface LinhaAto { chave: number; id?: number; tipo: string; numero: string }
export interface ValoresCapa {
  interessado_orgao: string;
  interessado_unidade: string;
  interessado_comarca: string;
  interessado_requerente: string;
  assunto_tipo: string;
  assunto_outro: string;
  providencias_texto: string;
  numero_relatorio_sema: string;
  equipe: LinhaEquipe[];
  atos: LinhaAto[];
}
export type CampoCapa = keyof ValoresCapa;

let sequencia = 1;
const chave = () => sequencia++;

export const capaVazia = (): ValoresCapa => ({
  interessado_orgao: "", interessado_unidade: "", interessado_comarca: "", interessado_requerente: "",
  assunto_tipo: "", assunto_outro: "", providencias_texto: "", numero_relatorio_sema: "", equipe: [], atos: [],
});

export const capaDe = (i: DadosCapa): ValoresCapa => ({
  interessado_orgao: i.interessado_orgao ?? "",
  interessado_unidade: i.interessado_unidade ?? "",
  interessado_comarca: i.interessado_comarca ?? "",
  interessado_requerente: i.interessado_requerente ?? "",
  assunto_tipo: i.assunto_tipo ?? "",
  assunto_outro: i.assunto_outro ?? "",
  providencias_texto: i.providencias_texto ?? "",
  numero_relatorio_sema: i.numero_relatorio_sema ?? "",
  equipe: (i.equipe ?? []).map((m) => ({ chave: chave(), nome: m.nome, cargo: m.cargo ?? "", orgao: m.orgao ?? "" })),
  atos: (i.atos ?? []).map((a) => ({ chave: chave(), id: a.id, tipo: a.tipo, numero: a.numero ?? "" })),
});

const CAMPOS_TEXTO: CampoCapa[] = [
  "interessado_orgao", "interessado_unidade", "interessado_comarca", "interessado_requerente",
  "assunto_tipo", "assunto_outro", "providencias_texto", "numero_relatorio_sema",
];

/** Corpo da API para os campos informados (vazios não vão); equipe e atos só quando houver linhas. */
export function corpoCapa(v: ValoresCapa): Record<string, unknown> {
  const corpo: Record<string, unknown> = {};
  for (const c of CAMPOS_TEXTO) if ((v[c] as string).trim()) corpo[c] = v[c];
  const equipe = v.equipe.filter((m) => m.nome.trim() || m.cargo.trim() || m.orgao.trim());
  if (equipe.length) corpo.equipe = equipe.map((m) => ({ nome: m.nome, cargo: m.cargo.trim() || null, orgao: m.orgao.trim() || null }));
  const atos = v.atos.filter((a) => a.tipo);
  if (atos.length) corpo.atos = atos.map((a) => ({ tipo: a.tipo, numero: a.numero.trim() || null }));
  return corpo;
}

const equipeApi = (l: LinhaEquipe[]) => l.map((m) => ({ nome: m.nome, cargo: m.cargo.trim() || null, orgao: m.orgao.trim() || null }));
const atosApi = (l: LinhaAto[], comId: boolean) =>
  l.map((a) => ({ ...(comId ? { id: a.id } : {}), tipo: a.tipo, numero: a.numero.trim() || null }));

/** Campos que mudaram em relação ao original e que a API deixa editar (`pode`). Equipe e atos vão por inteiro. */
export function alteracoesCapa(
  v: ValoresCapa, original: ValoresCapa, pode: (c: CampoCapa) => boolean, posFechamento: boolean,
): Record<string, unknown> {
  const corpo: Record<string, unknown> = {};
  for (const c of CAMPOS_TEXTO) if (pode(c) && v[c] !== original[c]) corpo[c] = v[c];
  if (pode("equipe") && JSON.stringify(equipeApi(v.equipe)) !== JSON.stringify(equipeApi(original.equipe))) corpo.equipe = equipeApi(v.equipe);
  if (pode("atos") && JSON.stringify(atosApi(v.atos, posFechamento)) !== JSON.stringify(atosApi(original.atos, posFechamento))) {
    corpo.atos = atosApi(v.atos, posFechamento); // depois do fechamento cada ato vai com o id (só o número muda)
  }
  return corpo;
}

interface Props {
  prefixo: string; // "nova" | "editar" (ids dos campos)
  v: ValoresCapa;
  mudar: (parcial: Partial<ValoresCapa>) => void;
  pode?: (c: CampoCapa) => boolean;
  posFechamento?: boolean; // finalizada: só o número dos atos e o nº SEMA
  comNumeroSema?: boolean;
}

export function BlocosCapa({ prefixo, v, mudar, pode = () => true, posFechamento = false, comNumeroSema = false }: Props) {
  const texto = (c: CampoCapa, rotulo: string, extras: { placeholder?: string; area?: boolean } = {}) => {
    const id = `${prefixo}-${c}`;
    const valor = v[c] as string;
    return (
      <label key={c} htmlFor={pode(c) ? id : undefined}>
        {rotulo}
        {!pode(c) ? (
          <span className="somente-leitura" data-testid={`leitura-${c}`}>{valor || VAZIO}</span>
        ) : extras.area ? (
          <textarea id={id} name={id} aria-label={rotulo} rows={3} value={valor} onChange={(e) => mudar({ [c]: e.target.value })} />
        ) : (
          <input id={id} name={id} aria-label={rotulo} placeholder={extras.placeholder} value={valor} onChange={(e) => mudar({ [c]: e.target.value })} />
        )}
      </label>
    );
  };

  const podeEquipe = pode("equipe");
  const podeAtos = pode("atos");
  const mudarMembro = (k: number, p: Partial<LinhaEquipe>) => mudar({ equipe: v.equipe.map((m) => (m.chave === k ? { ...m, ...p } : m)) });
  const mudarAto = (k: number, p: Partial<LinhaAto>) => mudar({ atos: v.atos.map((a) => (a.chave === k ? { ...a, ...p } : a)) });

  return (
    <>
      <fieldset className="proprietarios" aria-label="Interessado">
        <legend>Interessado</legend>
        <p className="dica">Deixe em branco para "Demanda interna / de ofício".</p>
        {texto("interessado_orgao", "Órgão / entidade", { placeholder: "Ex.: Ministério Público do Estado de Mato Grosso" })}
        {texto("interessado_unidade", "Unidade", { placeholder: "Ex.: 1ª Promotoria de Justiça Cível" })}
        {texto("interessado_comarca", "Comarca (opcional)", { placeholder: "Ex.: Comarca de Juína" })}
        {texto("interessado_requerente", "Requerente", { placeholder: "Ex.: Promotor de Justiça" })}
      </fieldset>

      <fieldset className="proprietarios" aria-label="Assunto">
        <legend>Assunto</legend>
        <label htmlFor={pode("assunto_tipo") ? `${prefixo}-assunto_tipo` : undefined}>
          Tipo de vistoria
          {pode("assunto_tipo") ? (
            <select id={`${prefixo}-assunto_tipo`} name={`${prefixo}-assunto_tipo`} aria-label="Tipo de vistoria" value={v.assunto_tipo} onChange={(e) => mudar({ assunto_tipo: e.target.value })}>
              <option value="">Selecione…</option>
              {ASSUNTOS.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          ) : (
            <span className="somente-leitura" data-testid="leitura-assunto_tipo">{v.assunto_tipo || VAZIO}</span>
          )}
        </label>
        {v.assunto_tipo === ASSUNTO_OUTRO && texto("assunto_outro", "Descreva o assunto")}
      </fieldset>

      <fieldset className="proprietarios" aria-label="Equipe técnica">
        <legend>Equipe técnica</legend>
        <p className="dica">Pelo menos 1 membro é necessário para fechar a inspeção.</p>
        {v.equipe.length === 0 && <p className="dica">Nenhum membro informado.</p>}
        {v.equipe.map((m, i) => {
          const p = `${prefixo}-equipe-${m.chave}`;
          return (
            <div className="linha-membro" key={m.chave} data-testid="linha-membro">
              {(["nome", "cargo", "orgao"] as const).map((campo) => {
                const rotulo = { nome: "Nome", cargo: "Cargo / função", orgao: "Órgão / unidade" }[campo];
                return (
                  <label key={campo} htmlFor={podeEquipe ? `${p}-${campo}` : undefined}>
                    {rotulo}{campo === "nome" ? " *" : ""}
                    {podeEquipe ? (
                      <input id={`${p}-${campo}`} name={`${p}-${campo}`} aria-label={`${rotulo} do membro ${i + 1}`} value={m[campo]} onChange={(e) => mudarMembro(m.chave, { [campo]: e.target.value })} />
                    ) : (
                      <span className="somente-leitura">{m[campo] || VAZIO}</span>
                    )}
                  </label>
                );
              })}
              {podeEquipe && (
                <button type="button" className="secundario" aria-label={`Remover membro ${i + 1}`} onClick={() => mudar({ equipe: v.equipe.filter((x) => x.chave !== m.chave) })}>
                  Remover
                </button>
              )}
            </div>
          );
        })}
        {podeEquipe && (
          <button type="button" className="secundario" onClick={() => mudar({ equipe: [...v.equipe, { chave: chave(), nome: "", cargo: "", orgao: "" }] })}>
            + Adicionar membro
          </button>
        )}
      </fieldset>

      <fieldset className="proprietarios" aria-label="Providências tomadas">
        <legend>Providências tomadas</legend>
        {texto("providencias_texto", "Providências (texto livre)", { area: true })}
        {v.atos.length === 0 && <p className="dica">Nenhum ato lavrado informado.</p>}
        {v.atos.map((a, i) => {
          const p = `${prefixo}-ato-${a.chave}`;
          return (
            <div className="linha-proprietario" key={a.chave} data-testid="linha-ato">
              <label htmlFor={podeAtos && !posFechamento ? `${p}-tipo` : undefined}>
                Tipo do ato
                {podeAtos && !posFechamento ? (
                  <select id={`${p}-tipo`} name={`${p}-tipo`} aria-label={`Tipo do ato ${i + 1}`} value={a.tipo} onChange={(e) => mudarAto(a.chave, { tipo: e.target.value })}>
                    {TIPOS_ATO.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                ) : (
                  <span className="somente-leitura">{a.tipo}</span>
                )}
              </label>
              <label htmlFor={podeAtos ? `${p}-numero` : undefined}>
                Número (vazio até lavrar no sistema da SEMA)
                {podeAtos ? (
                  <input id={`${p}-numero`} name={`${p}-numero`} aria-label={`Número do ato ${i + 1}`} value={a.numero} onChange={(e) => mudarAto(a.chave, { numero: e.target.value })} />
                ) : (
                  <span className="somente-leitura">{a.numero || VAZIO}</span>
                )}
              </label>
              {podeAtos && !posFechamento && (
                <button type="button" className="secundario" aria-label={`Remover ato ${i + 1}`} onClick={() => mudar({ atos: v.atos.filter((x) => x.chave !== a.chave) })}>
                  Remover
                </button>
              )}
            </div>
          );
        })}
        {podeAtos && !posFechamento && (
          <button type="button" className="secundario" onClick={() => mudar({ atos: [...v.atos, { chave: chave(), tipo: TIPOS_ATO[0], numero: "" }] })}>
            + Adicionar ato
          </button>
        )}
      </fieldset>

      {comNumeroSema && (
        <fieldset className="proprietarios" aria-label="Relatório na SEMA">
          <legend>Relatório na SEMA</legend>
          {texto("numero_relatorio_sema", "Nº do relatório na SEMA", { placeholder: "Número oficial atribuído pelo sistema da SEMA" })}
        </fieldset>
      )}
    </>
  );
}
