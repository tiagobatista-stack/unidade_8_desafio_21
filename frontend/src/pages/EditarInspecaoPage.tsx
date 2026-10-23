import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/api";
import { paraErro } from "../api/cliente";
import type { InspecaoDetalhe } from "../api/tipos";
import { Carregando, MensagemErro } from "../components/Basicos";
import { useInspecao, useInvalidarTudo, useLocais } from "../hooks/useDados";
import { VAZIO, formatarData, rotuloStatus } from "../utils/formatar";

type Valores = {
  numero_processo: string;
  local_id: string;
  data_agendamento: string;
  objetivo: string;
  observacoes: string;
  data_realizacao: string;
  observacoes_vistoria: string;
};

const deInspecao = (i: InspecaoDetalhe): Valores => ({
  numero_processo: i.numero_processo ?? "",
  local_id: String(i.local.id),
  data_agendamento: i.data_agendamento,
  objetivo: i.objetivo,
  observacoes: i.observacoes ?? "",
  data_realizacao: i.data_realizacao ?? "",
  observacoes_vistoria: i.observacoes_vistoria ?? "",
});

export default function EditarInspecaoPage() {
  const id = Number(useParams().id);
  const navegar = useNavigate();
  const invalidar = useInvalidarTudo();
  const { data: insp, isLoading, error } = useInspecao(id);
  const locais = useLocais();
  const [v, setV] = useState<Valores | null>(null);
  const [erro, setErro] = useState<unknown>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (insp) setV(deInspecao(insp));
  }, [insp]);

  if (isLoading) return <Carregando />;
  if (error) return <MensagemErro erro={error} />;
  if (!insp || !v) return null;

  // Quem decide o que é editável é a API (campos_editaveis); aqui só se renderiza.
  const pode = (campo: keyof Valores) => insp.campos_editaveis.includes(campo);
  const mudar = (campo: keyof Valores, valor: string) => setV({ ...v, [campo]: valor });
  const original = deInspecao(insp);

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setAviso(null);
    const alterados = (Object.keys(v!) as (keyof Valores)[]).filter((c) => pode(c) && v![c] !== original[c]);
    if (alterados.length === 0) {
      setAviso("Nenhuma alteração para salvar.");
      return;
    }
    const corpo: Record<string, unknown> = {};
    for (const c of alterados) {
      if (c === "local_id") corpo[c] = Number(v![c]);
      else if (c === "data_agendamento" || c === "data_realizacao") corpo[c] = v![c] || null;
      else corpo[c] = v![c];
    }
    setEnviando(true);
    try {
      await api.editarInspecao(id, corpo);
      await invalidar();
      navegar(`/inspecoes/${id}`);
    } catch (e2) {
      setErro(paraErro(e2));
    } finally {
      setEnviando(false);
    }
  }

  const campo = (rotulo: string, nome: keyof Valores, entrada: JSX.Element, leitura: string) => (
    <label key={nome} htmlFor={pode(nome) ? `editar-${nome}` : undefined}>
      {rotulo}
      {pode(nome) ? entrada : <span className="somente-leitura" data-testid={`leitura-${nome}`}>{leitura || VAZIO}</span>}
    </label>
  );

  const nenhum = insp.campos_editaveis.length === 0;
  return (
    <section>
      <p><Link to={`/inspecoes/${id}`}>← {insp.codigo}</Link></p>
      <h1>Editar {insp.codigo}</h1>
      <p className="dica">Status: {rotuloStatus(insp.status)}. Campos bloqueados não podem ser alterados neste status.</p>
      {nenhum && (
        <div role="note" className="alerta alerta-aviso">
          Esta inspeção está {rotuloStatus(insp.status).toLowerCase()} e não pode mais ser editada.
        </div>
      )}
      <form onSubmit={salvar} noValidate className="formulario">
        {campo("Número do processo", "numero_processo",
          <input id="editar-numero_processo" name="editar-numero_processo" aria-label="Número do processo" placeholder="SEMA-PRO-2026/12345" value={v.numero_processo} onChange={(e) => mudar("numero_processo", e.target.value)} />,
          original.numero_processo)}
        {campo("Local", "local_id",
          <select id="editar-local_id" name="editar-local_id" aria-label="Local" value={v.local_id} onChange={(e) => mudar("local_id", e.target.value)}>
            {locais.data?.dados.map((l) => (
              <option key={l.id} value={l.id}>{l.nome} — {l.municipio}</option>
            ))}
          </select>,
          `${insp.local.nome} — ${insp.local.municipio}`)}
        {campo("Data de agendamento (planejada)", "data_agendamento",
          <input id="editar-data_agendamento" name="editar-data_agendamento" type="date" aria-label="Data de agendamento" value={v.data_agendamento} onChange={(e) => mudar("data_agendamento", e.target.value)} />,
          formatarData(insp.data_agendamento))}
        {pode("data_realizacao") && (
          <p className="dica" data-testid="ajuda-realizacao">
            A data de realização é o dia em que a vistoria foi feita em campo. Você pode corrigi-la para o dia real; ela não pode
            ser futura nem anterior à data de agendamento.
          </p>
        )}
        {campo("Data de realização (vistoria em campo)", "data_realizacao",
          <input id="editar-data_realizacao" name="editar-data_realizacao" type="date" aria-label="Data de realização" value={v.data_realizacao} onChange={(e) => mudar("data_realizacao", e.target.value)} />,
          formatarData(insp.data_realizacao))}
        {campo("Objetivo", "objetivo",
          <input id="editar-objetivo" name="editar-objetivo" aria-label="Objetivo" value={v.objetivo} onChange={(e) => mudar("objetivo", e.target.value)} />,
          insp.objetivo)}
        {campo("Observações", "observacoes",
          <textarea id="editar-observacoes" name="editar-observacoes" aria-label="Observações" rows={3} value={v.observacoes} onChange={(e) => mudar("observacoes", e.target.value)} />,
          original.observacoes)}
        {campo("Observações da vistoria", "observacoes_vistoria",
          <textarea id="editar-observacoes_vistoria" name="editar-observacoes_vistoria" aria-label="Observações da vistoria" rows={4} value={v.observacoes_vistoria} onChange={(e) => mudar("observacoes_vistoria", e.target.value)} />,
          original.observacoes_vistoria)}
        {aviso && <div role="status" className="alerta alerta-aviso">{aviso}</div>}
        <MensagemErro erro={erro} />
        <div className="acoes">
          <button type="submit" disabled={enviando || nenhum}>Salvar alterações</button>
          <Link className="botao secundario" to={`/inspecoes/${id}`}>Voltar</Link>
        </div>
      </form>
    </section>
  );
}
