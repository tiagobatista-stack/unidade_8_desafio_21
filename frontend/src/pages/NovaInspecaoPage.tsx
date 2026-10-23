import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/api";
import { paraErro } from "../api/cliente";
import { Carregando, MensagemErro } from "../components/Basicos";
import { ModalNovoLocal } from "../components/ModalNovoLocal";
import { useInvalidarTudo, useLocais } from "../hooks/useDados";

export default function NovaInspecaoPage() {
  const navegar = useNavigate();
  const invalidar = useInvalidarTudo();
  const locais = useLocais();
  const [numeroProcesso, setNumeroProcesso] = useState("");
  const [localId, setLocalId] = useState("");
  const [novoLocal, setNovoLocal] = useState(false);
  const [agendamento, setAgendamento] = useState("");
  const [objetivo, setObjetivo] = useState("");
  const [observacoes, setObservacoes] = useState("");
  const [tentou, setTentou] = useState(false);
  const [erro, setErro] = useState<unknown>(null);
  const [enviando, setEnviando] = useState(false);

  const local = locais.data?.dados.find((l) => String(l.id) === localId);
  // Só presença de campos obrigatórios; as regras de negócio ficam na API.
  const faltando = { processo: !numeroProcesso.trim(), local: !localId, agendamento: !agendamento, objetivo: !objetivo.trim() };

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setTentou(true);
    setErro(null);
    if (faltando.processo || faltando.local || faltando.agendamento || faltando.objetivo) return;
    setEnviando(true);
    try {
      const nova = await api.criarInspecao({
        numero_processo: numeroProcesso,
        local_id: Number(localId),
        data_agendamento: agendamento,
        objetivo,
        observacoes: observacoes || undefined,
      });
      invalidar();
      navegar(`/inspecoes/${nova.id}`);
    } catch (e2) {
      setErro(paraErro(e2));
    } finally {
      setEnviando(false);
    }
  }

  if (locais.isLoading) return <Carregando />;
  return (
    <section>
      <h1>Nova inspeção</h1>
      <MensagemErro erro={locais.error} />
      <form onSubmit={enviar} noValidate className="formulario">
        <label>
          Número do processo *
          <input aria-label="Número do processo" placeholder="SEMA-PRO-2026/12345" value={numeroProcesso} onChange={(e) => setNumeroProcesso(e.target.value)} />
          {tentou && faltando.processo && <span className="campo-erro">Informe o número do processo.</span>}
        </label>
        <label>
          Local *
          <select aria-label="Local" value={localId} onChange={(e) => setLocalId(e.target.value)}>
            <option value="">Selecione…</option>
            {locais.data?.dados.map((l) => (
              <option key={l.id} value={l.id}>{l.nome} — {l.municipio}</option>
            ))}
          </select>
          {tentou && faltando.local && <span className="campo-erro">Selecione um local.</span>}
        </label>
        <div className="acoes">
          <button type="button" className="secundario" onClick={() => setNovoLocal(true)}>+ Novo local</button>
          {locais.data && locais.data.dados.length === 0 && (
            <span className="dica">Nenhum local cadastrado: crie um com "Novo local" ou use "Carregar exemplos" no Painel.</span>
          )}
        </div>
        <div className="duas-colunas">
          <label>
            Latitude
            <input aria-label="Latitude" readOnly value={local ? local.latitude : ""} />
          </label>
          <label>
            Longitude
            <input aria-label="Longitude" readOnly value={local ? local.longitude : ""} />
          </label>
        </div>
        <label>
          Data de agendamento *
          <input type="date" aria-label="Data de agendamento" value={agendamento} onChange={(e) => setAgendamento(e.target.value)} />
          {tentou && faltando.agendamento && <span className="campo-erro">Informe a data de agendamento.</span>}
        </label>
        <label>
          Objetivo *
          <input aria-label="Objetivo" value={objetivo} onChange={(e) => setObjetivo(e.target.value)} />
          {tentou && faltando.objetivo && <span className="campo-erro">Informe o objetivo.</span>}
        </label>
        <label>
          Observações
          <textarea aria-label="Observações" rows={3} value={observacoes} onChange={(e) => setObservacoes(e.target.value)} />
        </label>
        <MensagemErro erro={erro} />
        <div className="acoes">
          <button type="submit" disabled={enviando}>Cadastrar inspeção</button>
        </div>
      </form>
      {novoLocal && (
        <ModalNovoLocal
          onCancelar={() => setNovoLocal(false)}
          onCriado={async (local) => {
            await invalidar(); // recarrega a lista de locais e seleciona o novo
            setLocalId(String(local.id));
            setNovoLocal(false);
          }}
        />
      )}
    </section>
  );
}
