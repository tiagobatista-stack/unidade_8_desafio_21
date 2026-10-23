import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/api";
import { Carregando, MensagemErro, Selo, Vazio } from "../components/Basicos";
import { ROTULO_STATUS, VAZIO, formatarData, rotuloResultado, rotuloStatus, somenteLeitura } from "../utils/formatar";

/** Grupos do Painel (seção 7 do handoff). Cada um vira vários `status` na API; a contagem e o filtro coincidem. */
const GRUPOS: Record<string, { rotulo: string; status: string[] }> = {
  ATIVAS: { rotulo: "Todas, exceto canceladas", status: ["ABERTA", "EM_ANDAMENTO", "FINALIZADA"] },
  PENDENTES: { rotulo: "Pendências (Aberta + Em andamento)", status: ["ABERTA", "EM_ANDAMENTO"] },
};

export const statusParaApi = (valor: string): string[] => (valor ? (GRUPOS[valor]?.status ?? [valor]) : []);
const rotuloFiltro = (valor: string) => GRUPOS[valor]?.rotulo ?? ROTULO_STATUS[valor] ?? valor;

export default function InspecoesPage() {
  const [params, setParams] = useSearchParams();
  const status = params.get("status") ?? "";
  const filtros = {
    status,
    numero_processo: params.get("numero_processo") ?? "",
    data_inicio: params.get("data_inicio") ?? "",
    data_fim: params.get("data_fim") ?? "",
  };
  const { data, isLoading, error } = useQuery({
    queryKey: ["inspecoes", "lista", filtros],
    queryFn: () => api.inspecoes({ ...filtros, status: statusParaApi(status) }),
  });
  const linhas = data?.dados;

  const mudar = (campo: string, valor: string) => {
    const novo = new URLSearchParams(params);
    if (valor) novo.set(campo, valor);
    else novo.delete(campo);
    setParams(novo, { replace: campo === "numero_processo" }); // digitar na busca não enche o histórico
  };

  return (
    <section>
      <div className="linha-entre">
        <h1>Inspeções</h1>
        <Link className="botao" to="/inspecoes/nova">Nova inspeção</Link>
      </div>
      {status && (
        <p className="filtro-ativo" data-testid="filtro-ativo">
          Filtro: <strong>{rotuloFiltro(status)}</strong>
          {data && <> — {data.total} inspeção(ões)</>}
        </p>
      )}
      <div className="filtros">
        <label>
          Status
          <select aria-label="Filtrar por status" value={status} onChange={(e) => mudar("status", e.target.value)}>
            <option value="">Todos</option>
            <option value="ATIVAS">{GRUPOS.ATIVAS.rotulo}</option>
            <option value="PENDENTES">{GRUPOS.PENDENTES.rotulo}</option>
            {Object.entries(ROTULO_STATUS).map(([v, r]) => (
              <option key={v} value={v}>{r}</option>
            ))}
          </select>
        </label>
        <label>
          Nº do processo
          <input
            type="search"
            aria-label="Buscar por número do processo"
            placeholder="SEMA-PRO-2026/12345"
            value={filtros.numero_processo}
            onChange={(e) => mudar("numero_processo", e.target.value)}
          />
        </label>
        <label>
          Agendamento de
          <input type="date" aria-label="Data inicial" value={filtros.data_inicio} onChange={(e) => mudar("data_inicio", e.target.value)} />
        </label>
        <label>
          até
          <input type="date" aria-label="Data final" value={filtros.data_fim} onChange={(e) => mudar("data_fim", e.target.value)} />
        </label>
      </div>
      {isLoading && <Carregando />}
      <MensagemErro erro={error} />
      {linhas && linhas.length === 0 && <Vazio texto="Nenhuma inspeção encontrada." />}
      {linhas && linhas.length > 0 && (
        <div className="tabela-rolagem">
          <table>
            <thead>
              <tr>
                <th>Código</th><th>Processo</th><th>Local</th><th>Agendamento</th><th>Realização</th>
                <th>Status</th><th>Resultado</th><th>Fotos</th><th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {linhas.map((i) => (
                <tr key={i.id}>
                  <td><Link to={`/inspecoes/${i.id}`}>{i.codigo}</Link></td>
                  <td>{i.numero_processo ?? VAZIO}</td>
                  <td>{i.local.nome}</td>
                  <td>{formatarData(i.data_agendamento)}</td>
                  <td>{formatarData(i.data_realizacao)}</td>
                  <td><Selo tipo={i.status}>{rotuloStatus(i.status)}</Selo></td>
                  <td>{rotuloResultado(i.resultado)}</td>
                  <td>{i.qtd_fotos}</td>
                  <td>
                    {somenteLeitura(i.status) ? (
                      VAZIO
                    ) : (
                      <Link to={`/inspecoes/${i.id}/editar`} aria-label={`Editar ${i.codigo}`}>Editar</Link>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
