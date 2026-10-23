import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/api";
import { Carregando, MensagemErro } from "../components/Basicos";
import { FormularioLocal } from "../components/FormularioLocal";
import { useInvalidarTudo, useLocal } from "../hooks/useDados";

/** /locais/novo e /locais/:id/editar */
export default function LocalFormPage() {
  const params = useParams();
  const id = params.id ? Number(params.id) : null;
  const navegar = useNavigate();
  const invalidar = useInvalidarTudo();
  const { data: local, isLoading, error } = useLocal(id ?? 0, id !== null);

  if (id !== null && (isLoading || !local) && !error) return <Carregando />;
  if (id !== null && error) return <MensagemErro erro={error} />;

  return (
    <section>
      <p><Link to="/locais">← Locais</Link></p>
      <h1>{id === null ? "Novo local" : `Editar ${local?.nome ?? "local"}`}</h1>
      {id !== null && (
        <p className="dica">
          Alterações valem para as próximas consultas e para inspeções ainda não finalizadas. As finalizadas mantêm a cópia dos
          dados do fechamento.
        </p>
      )}
      <FormularioLocal
        key={local?.id ?? "novo"}
        inicial={id === null ? undefined : local}
        rotuloSalvar={id === null ? "Cadastrar local" : "Salvar alterações"}
        salvar={(dados) => (id === null ? api.criarLocal(dados) : api.atualizarLocal(id, dados))}
        onSalvo={async () => {
          await invalidar();
          navegar("/locais");
        }}
        onCancelar={() => navegar("/locais")}
      />
    </section>
  );
}
