import { Link } from "react-router-dom";
import { Carregando, MensagemErro, Vazio } from "../components/Basicos";
import { useLocais } from "../hooks/useDados";
import { VAZIO } from "../utils/formatar";

export default function LocaisPage() {
  const { data, isLoading, error } = useLocais();
  const locais = data?.dados;
  return (
    <section>
      <div className="linha-entre">
        <h1>Locais</h1>
        <Link className="botao" to="/locais/novo">Novo local</Link>
      </div>
      <p className="dica">Empreendimentos vistoriados. As inspeções já finalizadas guardam uma cópia dos dados do momento do fechamento.</p>
      {isLoading && <Carregando />}
      <MensagemErro erro={error} />
      {locais && locais.length === 0 && <Vazio texto='Nenhum local cadastrado. Use "Novo local" ou "Carregar exemplos" no Painel.' />}
      {locais && locais.length > 0 && (
        <div className="tabela-rolagem">
          <table>
            <thead>
              <tr><th>Nome</th><th>Município</th><th>Tipo</th><th>CAR</th><th>Proprietários</th><th>Coordenadas</th><th>Ações</th></tr>
            </thead>
            <tbody>
              {locais.map((l) => (
                <tr key={l.id}>
                  <td>{l.nome}</td>
                  <td>{l.municipio}</td>
                  <td>{l.tipo}</td>
                  <td>{l.numero_car ?? VAZIO}</td>
                  <td>
                    {l.proprietarios.length === 0
                      ? VAZIO
                      : l.proprietarios.map((p) => (
                          <div key={`${p.nome}-${p.telefone}`}>
                            {p.nome}{p.telefone_formatado ? ` — ${p.telefone_formatado}` : ""}
                          </div>
                        ))}
                  </td>
                  <td>{l.latitude}, {l.longitude}</td>
                  <td><Link to={`/locais/${l.id}/editar`} aria-label={`Editar ${l.nome}`}>Editar</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
