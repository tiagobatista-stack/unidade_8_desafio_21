import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { urlApi } from "../api/cliente";
import type { FotoRelatorio, Relatorio } from "../api/tipos";
import { Carregando, MensagemErro, TextoPuro } from "../components/Basicos";
import { useRelatorio } from "../hooks/useDados";
import {
  ROTULO_SITUACAO,
  VAZIO,
  formatarData,
  formatarDataHora,
  rotuloResultado,
  rotuloStatus,
} from "../utils/formatar";

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

function Documento({ r, inspecaoId }: { r: Relatorio; inspecaoId: number }) {
  const [carregadas, setCarregadas] = useState(0);
  const total = r.fotos.length;
  const prontas = carregadas >= total; // só libera a impressão com todas as imagens já carregadas
  const id = r.identificacao;
  const emp = r.empreendimento;
  const t = r.checklist.totais;
  const rodape = `${r.numero_relatorio ? `Relatório nº ${r.numero_relatorio}` : "Relatório sem número (prévia)"} · ${id.codigo} · Sistema fictício/simulado`;

  return (
    <div className="relatorio-pagina">
      <div className="barra-relatorio nao-imprimir">
        <Link to={`/inspecoes/${inspecaoId}`}>← Voltar à inspeção</Link>
        <button type="button" disabled={!prontas} onClick={() => window.print()}>Imprimir / Salvar PDF</button>
        {!prontas && <span role="status" className="dica">Carregando imagens… {carregadas}/{total}</span>}
        <span className="dica">Dica: na janela de impressão escolha "Salvar como PDF", papel A4.</span>
      </div>

      <style data-testid="regra-pagina">{regraDePagina(rodape, r.marca_dagua)}</style>
      <article className="relatorio" data-testid="relatorio">
        {r.marca_dagua && <div className="marca-dagua" data-testid="marca-dagua" aria-hidden="true">{r.marca_dagua}</div>}
        {r.previa && (
          <div role="note" className="faixa-previa" data-testid="faixa-previa">
            {r.marca_dagua}: este documento ainda não tem número e pode mudar até a inspeção ser finalizada.
          </div>
        )}

        <header className="cabecalho-relatorio">
          <h1 data-testid="titulo-relatorio">{r.titulo}</h1>
          <p className="dica">Inspeções Simuladas — sistema fictício, dados de demonstração.</p>
        </header>

        <section aria-labelledby="rel-1">
          <h2 id="rel-1">1. Identificação</h2>
          <dl className="dados-relatorio">
            <div><dt>Relatório nº</dt><dd data-testid="rel-numero">{r.numero_relatorio ?? "— (prévia)"}</dd></div>
            <div><dt>Inspeção</dt><dd>{id.codigo}</dd></div>
            <div><dt>Nº do processo</dt><dd>{id.numero_processo ?? NAO_INFORMADO}</dd></div>
            <div><dt>Status</dt><dd>{rotuloStatus(id.status)}</dd></div>
            <div><dt>Resultado</dt><dd>{rotuloResultado(id.resultado)}</dd></div>
            <div><dt>Data de agendamento</dt><dd>{formatarData(id.data_agendamento)}</dd></div>
            <div><dt>Data da vistoria (realização)</dt><dd>{formatarData(id.data_realizacao)}</dd></div>
            <div><dt>Conclusão (data e hora)</dt><dd data-testid="rel-fechado-em">{formatarDataHora(id.fechado_em)}</dd></div>
          </dl>
        </section>

        <section aria-labelledby="rel-2">
          <h2 id="rel-2">2. Empreendimento</h2>
          <dl className="dados-relatorio">
            <div><dt>Nome</dt><dd>{emp.nome}</dd></div>
            <div><dt>Município</dt><dd>{emp.municipio}</dd></div>
            <div><dt>Tipo</dt><dd>{emp.tipo}</dd></div>
            <div><dt>Coordenadas</dt><dd>{emp.latitude}, {emp.longitude}</dd></div>
            <div><dt>Nº do CAR</dt><dd data-testid="rel-car">{emp.numero_car ?? NAO_INFORMADO}</dd></div>
            <div className="largo">
              <dt>Proprietários</dt>
              <dd data-testid="rel-proprietarios">
                {emp.proprietarios.length === 0 ? (
                  NAO_INFORMADO
                ) : (
                  <ul className="lista-simples">
                    {emp.proprietarios.map((p, i) => (
                      <li key={i}>{p.nome}{p.telefone_formatado ? ` — ${p.telefone_formatado}` : ""}</li>
                    ))}
                  </ul>
                )}
              </dd>
            </div>
          </dl>
        </section>

        <section aria-labelledby="rel-3">
          <h2 id="rel-3">3. Objetivo e observações</h2>
          <h3>Objetivo</h3>
          <TextoPuro valor={r.objetivo.objetivo} />
          <h3>Observações gerais</h3>
          <TextoPuro valor={r.objetivo.observacoes} />
          <h3>Observações da vistoria</h3>
          <TextoPuro valor={r.objetivo.observacoes_vistoria} />
        </section>

        <section aria-labelledby="rel-4" className="bloco-checklist">
          <h2 id="rel-4">4. Checklist</h2>
          <table className="tabela-relatorio">
            <thead>
              <tr><th>Nº</th><th>Item</th><th>Crítico</th><th>Situação</th><th>Observação</th></tr>
            </thead>
            <tbody>
              {r.checklist.itens.map((i) => (
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
        </section>

        <section aria-labelledby="rel-5">
          <h2 id="rel-5">5. Registro fotográfico</h2>
          {total === 0 && <p>Nenhuma foto anexada.</p>}
          {emPares(r.fotos).map((par, i) => (
            <div className="par-fotos" key={i}>
              {par.map((f) => (
                <Foto key={f.numero} foto={f} aoCarregar={() => setCarregadas((n) => n + 1)} />
              ))}
            </div>
          ))}
        </section>

        <section aria-labelledby="rel-6">
          <h2 id="rel-6">6. Conclusão</h2>
          <p data-testid="conclusao-resultado">
            Resultado: <strong>{r.conclusao.resultado ? rotuloResultado(r.conclusao.resultado) : "Ainda não calculado (prévia)"}</strong>
          </p>
          <p data-testid="conclusao-regra">Regra aplicada: {r.conclusao.regra}</p>
        </section>

        <footer className="rodape-relatorio" data-testid="rodape-relatorio">{rodape}</footer>
      </article>
    </div>
  );
}

export default function RelatorioPage() {
  const id = Number(useParams().id);
  const { data, isLoading, error } = useRelatorio(id);
  if (isLoading) return <Carregando texto="Montando o relatório…" />;
  if (error) return <MensagemErro erro={error} />;
  if (!data) return null;
  return <Documento r={data} inspecaoId={id} />;
}
