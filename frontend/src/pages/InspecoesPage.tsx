import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/api";
import type { FiltrosLista, InspecaoResumo } from "../api/tipos";
import { Carregando, MensagemErro, Selo, Vazio } from "../components/Basicos";
import { ROTULO_STATUS, formatarData, rotuloResultado, rotuloStatus } from "../utils/formatar";

const PENDENTES = "PENDENTES";

/** "Pendências" = Aberta + Em andamento: duas consultas ao mesmo endpoint, unidas na ordem da API. */
async function buscar(f: FiltrosLista): Promise<InspecaoResumo[]> {
  if (f.status !== PENDENTES) return (await api.inspecoes(f)).dados;
  const [a, b] = await Promise.all([
    api.inspecoes({ ...f, status: "ABERTA" }),
    api.inspecoes({ ...f, status: "EM_ANDAMENTO" }),
  ]);
  return [...a.dados, ...b.dados].sort(
    (x, y) => y.data_agendamento.localeCompare(x.data_agendamento) || y.id - x.id,
  );
}

export default function InspecoesPage() {
  const [params, setParams] = useSearchParams();
  const filtros: FiltrosLista = {
    status: params.get("status") ?? "",
    data_inicio: params.get("data_inicio") ?? "",
    data_fim: params.get("data_fim") ?? "",
  };
  const { data, isLoading, error } = useQuery({ queryKey: ["inspecoes", "lista", filtros], queryFn: () => buscar(filtros) });

  const mudar = (campo: string, valor: string) => {
    const novo = new URLSearchParams(params);
    if (valor) novo.set(campo, valor);
    else novo.delete(campo);
    setParams(novo);
  };

  return (
    <section>
      <div className="linha-entre">
        <h1>Inspeções</h1>
        <Link className="botao" to="/inspecoes/nova">Nova inspeção</Link>
      </div>
      <div className="filtros">
        <label>
          Status
          <select aria-label="Filtrar por status" value={filtros.status} onChange={(e) => mudar("status", e.target.value)}>
            <option value="">Todos</option>
            <option value={PENDENTES}>Pendências (Aberta + Em andamento)</option>
            {Object.entries(ROTULO_STATUS).map(([v, r]) => (
              <option key={v} value={v}>{r}</option>
            ))}
          </select>
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
      {data && data.length === 0 && <Vazio texto="Nenhuma inspeção encontrada." />}
      {data && data.length > 0 && (
        <div className="tabela-rolagem">
          <table>
            <thead>
              <tr>
                <th>Código</th><th>Local</th><th>Agendamento</th><th>Realização</th><th>Status</th><th>Resultado</th><th>Fotos</th>
              </tr>
            </thead>
            <tbody>
              {data.map((i) => (
                <tr key={i.id}>
                  <td><Link to={`/inspecoes/${i.id}`}>{i.codigo}</Link></td>
                  <td>{i.local.nome}</td>
                  <td>{formatarData(i.data_agendamento)}</td>
                  <td>{formatarData(i.data_realizacao)}</td>
                  <td><Selo tipo={i.status}>{rotuloStatus(i.status)}</Selo></td>
                  <td>{rotuloResultado(i.resultado)}</td>
                  <td>{i.qtd_fotos}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
