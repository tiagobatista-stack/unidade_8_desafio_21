import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { urlApi } from "../api/cliente";
import type { FotoRelatorio, Relatorio } from "../api/tipos";
import { Carregando, MensagemErro, TextoPuro } from "../components/Basicos";
import { useRelatorio } from "../hooks/useDados";
import { ROTULO_SITUACAO, VAZIO, formatarData, formatarDataHora, rotuloResultado } from "../utils/formatar";

const NAO_INFORMADO = "Não informado";

/** Texto seguro para uma string CSS ("..."): escapa barra invertida, aspas e quebras de linha. */
const cssTexto = (t: string) =>
  t
    .replace(/\\/g, "\\\\") // barra invertida -> duas
    .replace(/"/g, '\\"') // aspas -> \"
    .replace(/\r?\n/g, " "); // quebra de linha -> espaço

/**
 * Rodapé e aviso de prévia em TODAS as páginas impressas: caixas de margem do @page (o navegador as repete
 * em cada página; elementos `position: fixed` não são confiáveis e chegaram a cobrir o conteúdo).
 */
const regraDePagina = (rodape: string, marca: string | null) =>
  `@page {
    @bottom-left { content: "${cssTexto(rodape)}"; font-size: 8.5pt; color: #444; width: 78%; text-align: left; }
    ${marca ? `@top-center { content: "${cssTexto(marca)}"; font-size: 13pt; font-weight: 700; color: #b42318; }` : ""}
  }`;

/** Agrupa as fotos de duas em duas: cada par nunca é cortado entre páginas e ocupa uma página na impressão. */
const emPares = (fotos: FotoRelatorio[]) =>
  Array.from({ length: Math.ceil(fotos.length / 2) }, (_, i) => fotos.slice(i * 2, i * 2 + 2));

function Foto({ foto, aoCarregar }: { foto: FotoRelatorio; aoCarregar: () => void }) {
  return (
    <figure className="foto-relatorio" data-testid="foto-relatorio">
      <img
        src={urlApi(foto.url_original)}
        alt={`Foto ${foto.numero}${foto.legenda ? `: ${foto.legenda}` : ""}`}
        onLoad={aoCarregar}
        onError={aoCarregar}
      />
      <figcaption>
        <p><strong>Foto {foto.numero}</strong>{foto.legenda ? ` — ${foto.legenda}` : ""}</p>
        <p className="texto-puro">{foto.anotacao}</p>
        <p className="dica">
          Item do checklist: {foto.item_numero ? `${foto.item_numero}. ${foto.item_descricao}` : "Sem vínculo"}
          {" · "}Data de captura: {foto.data_captura ? formatarDataHora(foto.data_captura) : NAO_INFORMADO}
        </p>
      </figcaption>
    </figure>
  );
}

interface PropsDocumento {
  r: Relatorio;
  inspecaoId: number;
  incluirConclusao: boolean;
  aoAlternarConclusao: (v: boolean) => void;
}

function Documento({ r, inspecaoId, incluirConclusao, aoAlternarConclusao }: PropsDocumento) {
  const [carregadas, setCarregadas] = useState(0);
  const { cabecalho, constatacoes, providencias } = r;
  const total = constatacoes.fotos.length;
  const prontas = carregadas >= total; // só libera a impressão com todas as imagens já carregadas
  const t = constatacoes.checklist.totais;
  const refInterna = cabecalho.ref_interna ? `Ref. interna ${cabecalho.ref_interna}` : "Ref. interna: sem número (prévia)";
  const rodape = `${refInterna} · ${cabecalho.codigo} · Sistema fictício/simulado`;

  return (
    <div className="relatorio-pagina">
      <div className="barra-relatorio nao-imprimir">
        <Link to={`/inspecoes/${inspecaoId}`}>← Voltar à inspeção</Link>
        <button type="button" disabled={!prontas} onClick={() => window.print()}>Imprimir / Salvar PDF</button>
        <label htmlFor="relatorio-incluir-conclusao">
          <input
            type="checkbox"
            id="relatorio-incluir-conclusao"
            name="relatorio-incluir-conclusao"
            checked={incluirConclusao}
            onChange={(e) => aoAlternarConclusao(e.target.checked)}
          />{" "}
          Incluir conclusão
        </label>
        {!prontas && <span role="status" className="dica">Carregando imagens… {carregadas}/{total}</span>}
        <span className="dica">
          Corpo do relatório, a partir do item 5, para anexar depois da capa gerada no sistema da SEMA. Na janela de impressão
          escolha "Salvar como PDF", papel A4.
        </span>
      </div>

      <style data-testid="regra-pagina">{regraDePagina(rodape, r.marca_dagua)}</style>
      <article className="relatorio" data-testid="relatorio">
        {r.marca_dagua && <div className="marca-dagua" data-testid="marca-dagua" aria-hidden="true">{r.marca_dagua}</div>}
        {r.previa && (
          <div role="note" className="faixa-previa" data-testid="faixa-previa">
            {r.marca_dagua}: este documento ainda não tem Ref. interna e pode mudar até a inspeção ser finalizada.
          </div>
        )}

        <header className="cabecalho-relatorio">
          <h1 className="cabecalho-minimo" data-testid="cabecalho-relatorio">{cabecalho.linha}</h1>
        </header>

        <section aria-labelledby="rel-5">
          <h2 id="rel-5">5 – Constatações</h2>

          <h3>5.1 Relato da vistoria</h3>
          <dl className="dados-relatorio">
            <div className="largo">
              <dt>Data da vistoria</dt>
              <dd data-testid="rel-data-vistoria">{formatarData(constatacoes.relato.data_realizacao)}</dd>
            </div>
          </dl>
          <TextoPuro valor={constatacoes.relato.observacoes_vistoria} />

          <div className="bloco-checklist">
            <h3>5.2 Checklist</h3>
            <table className="tabela-relatorio">
              <thead>
                <tr><th>Nº</th><th>Item</th><th>Crítico</th><th>Situação</th><th>Observação</th></tr>
              </thead>
              <tbody>
                {constatacoes.checklist.itens.map((i) => (
                  <tr key={i.numero} className={i.critico_nao_conforme ? "linha-critica" : undefined} data-testid="linha-checklist">
                    <td>{i.numero}</td>
                    <td>{i.descricao}</td>
                    <td>{i.critico ? "Sim" : "Não"}</td>
                    <td>
                      {ROTULO_SITUACAO[i.situacao]}
                      {i.critico_nao_conforme && <strong className="selo-critico-nc"> · CRÍTICO NÃO CONFORME</strong>}
                    </td>
                    <td className="texto-puro">{i.observacao ?? VAZIO}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="totais-relatorio" data-testid="totais-checklist">
              Totais: {t.respondidos} de {t.total} respondidos · {t.conformes} conformes · {t.nao_conformes} não conformes ·{" "}
              {t.nao_aplicaveis} não aplicáveis{t.nao_respondidos > 0 ? ` · ${t.nao_respondidos} não respondidos` : ""}
            </p>
          </div>

          <h3>5.3 Registro fotográfico</h3>
          {total === 0 && <p>Nenhuma foto anexada.</p>}
          {emPares(constatacoes.fotos).map((par, i) => (
            <div className="par-fotos" key={i}>
              {par.map((f) => (
                <Foto key={f.numero} foto={f} aoCarregar={() => setCarregadas((n) => n + 1)} />
              ))}
            </div>
          ))}
        </section>

        <section aria-labelledby="rel-6">
          <h2 id="rel-6">6 – Providências tomadas</h2>
          {providencias.texto ? (
            <TextoPuro valor={providencias.texto} />
          ) : (
            <p data-testid="sem-providencias-texto">Nenhuma providência registrada em texto.</p>
          )}
          {providencias.atos.length > 0 && (
            <ul className="lista-simples" data-testid="atos-relatorio">
              {providencias.atos.map((a, i) => <li key={i}>{a.rotulo}</li>)}
            </ul>
          )}
        </section>

        {r.conclusao && (
          <section aria-labelledby="rel-7">
            <h2 id="rel-7">7 – Conclusão</h2>
            <p data-testid="conclusao-resultado">
              Resultado: <strong>{r.conclusao.resultado ? rotuloResultado(r.conclusao.resultado) : "Ainda não calculado (prévia)"}</strong>
            </p>
            <p data-testid="conclusao-regra">Regra aplicada: {r.conclusao.regra}</p>
          </section>
        )}

        <footer className="rodape-relatorio" data-testid="rodape-relatorio">{rodape}</footer>
      </article>
    </div>
  );
}

export default function RelatorioPage() {
  const id = Number(useParams().id);
  const [incluirConclusao, setIncluirConclusao] = useState(true); // ligada por padrão
  const { data, isLoading, error } = useRelatorio(id, incluirConclusao);
  if (isLoading) return <Carregando texto="Montando o relatório…" />;
  if (error) return <MensagemErro erro={error} />;
  if (!data) return null;
  return <Documento r={data} inspecaoId={id} incluirConclusao={incluirConclusao} aoAlternarConclusao={setIncluirConclusao} />;
}
