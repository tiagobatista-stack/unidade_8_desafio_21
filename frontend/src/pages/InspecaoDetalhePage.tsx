import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/api";
import { ApiErro, paraErro } from "../api/cliente";
import type { Situacao } from "../api/tipos";
import { BlocoObservacoesVistoria } from "../components/BlocoObservacoesVistoria";
import { Carregando, MensagemErro, Selo, TextoPuro } from "../components/Basicos";
import { GaleriaFotos } from "../components/GaleriaFotos";
import { ItemChecklist } from "../components/ItemChecklist";
import { ModalCancelar, ModalFechar } from "../components/ModaisInspecao";
import { UploadFotos } from "../components/UploadFotos";
import { useInspecao, useInvalidarTudo } from "../hooks/useDados";
import { formatarData, rotuloResultado, rotuloStatus, somenteLeitura } from "../utils/formatar";

export default function InspecaoDetalhePage() {
  const id = Number(useParams().id);
  const { data: insp, isLoading, error } = useInspecao(id);
  const invalidar = useInvalidarTudo();
  const [erroAcao, setErroAcao] = useState<unknown>(null);
  const [modal, setModal] = useState<"fechar" | "cancelar" | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [novoItem, setNovoItem] = useState("");

  async function executar(acao: () => Promise<unknown>, aoSucesso?: () => void) {
    setErroAcao(null);
    setOcupado(true);
    try {
      await acao();
      aoSucesso?.();
      invalidar();
    } catch (e) {
      setErroAcao(paraErro(e));
      invalidar(); // o estado real pode ter mudado (ex.: reagendamento necessário)
      setModal(null);
    } finally {
      setOcupado(false);
    }
  }

  if (isLoading) return <Carregando />;
  if (error) return <MensagemErro erro={error} />;
  if (!insp) return null;

  const leitura = somenteLeitura(insp.status);
  // Itens citados em um fechamento bloqueado são destacados.
  const bloqueio = erroAcao instanceof ApiErro && erroAcao.codigo === "FECHAMENTO_BLOQUEADO" ? erroAcao : null;
  const motivoPorItem = new Map<number, string>();
  bloqueio?.detalhes.forEach((d) => {
    const m = /^itens\.(\d+)$/.exec(d.campo);
    if (m) motivoPorItem.set(Number(m[1]), d.mensagem);
  });

  return (
    <section>
      <p><Link to="/inspecoes">← Inspeções</Link></p>
      <header className="cabecalho-inspecao">
        <h1>{insp.codigo}</h1>
        <Selo tipo={insp.status}>{rotuloStatus(insp.status)}</Selo>
        {leitura && <span className="dica">Somente leitura</span>}
      </header>

      <dl className="dados">
        <div><dt>Local</dt><dd>{insp.local.nome} — {insp.local.municipio}</dd></div>
        <div><dt>Coordenadas</dt><dd>{insp.local.latitude}, {insp.local.longitude}</dd></div>
        <div><dt>Agendamento</dt><dd>{formatarData(insp.data_agendamento)}</dd></div>
        <div><dt>Realização</dt><dd>{formatarData(insp.data_realizacao)}</dd></div>
        <div><dt>Resultado</dt><dd>{rotuloResultado(insp.resultado)}</dd></div>
        <div><dt>Objetivo</dt><dd className="texto-puro">{insp.objetivo}</dd></div>
        <div><dt>Observações</dt><dd><TextoPuro valor={insp.observacoes} /></dd></div>
        {insp.status === "CANCELADA" && (
          <div><dt>Motivo do cancelamento</dt><dd><TextoPuro valor={insp.motivo_cancelamento} /></dd></div>
        )}
      </dl>

      <MensagemErro erro={erroAcao} />

      {!leitura && (
        <div className="acoes">
          <button type="button" onClick={() => { setErroAcao(null); setModal("fechar"); }}>Fechar inspeção</button>
          <button type="button" className="perigo" onClick={() => { setErroAcao(null); setModal("cancelar"); }}>Cancelar inspeção</button>
        </div>
      )}

      <section aria-labelledby="titulo-checklist" className="cartao">
        <h2 id="titulo-checklist">
          Checklist <small>({insp.resumo_itens.respondidos}/{insp.resumo_itens.total} respondidos, {insp.resumo_itens.nao_conformes} não conformes)</small>
        </h2>
        <ul className="itens">
          {insp.itens.map((it) => (
            <ItemChecklist
              key={it.id}
              item={it}
              editavel={!leitura}
              destacado={motivoPorItem.get(it.id)}
              onSituacao={(s: Situacao) => executar(() => api.atualizarItem(id, it.id, { situacao: s }))}
              onObservacao={(o) => executar(() => api.atualizarItem(id, it.id, { observacao: o }))}
              onRemover={() => executar(() => api.removerItem(id, it.id))}
            />
          ))}
        </ul>
        {!leitura && (
          <form
            className="linha-entre"
            onSubmit={(e) => {
              e.preventDefault();
              if (novoItem.trim()) executar(() => api.adicionarItem(id, novoItem), () => setNovoItem(""));
            }}
          >
            <input aria-label="Descrição do item avulso" placeholder="Novo item avulso" value={novoItem} onChange={(e) => setNovoItem(e.target.value)} />
            <button type="submit" disabled={!novoItem.trim() || ocupado}>Adicionar item</button>
          </form>
        )}
      </section>

      <BlocoObservacoesVistoria
        valor={insp.observacoes_vistoria}
        editavel={!leitura}
        salvando={ocupado}
        onSalvar={(t) => executar(() => api.editarInspecao(id, { observacoes_vistoria: t }))}
      />

      <section aria-labelledby="titulo-fotos" className="cartao">
        <h2 id="titulo-fotos">Fotos da vistoria ({insp.fotos.length})</h2>
        {!leitura && <UploadFotos inspecaoId={id} itens={insp.itens} onEnviada={invalidar} />}
        <GaleriaFotos inspecaoId={id} fotos={insp.fotos} itens={insp.itens} editavel={!leitura} onMudou={invalidar} />
      </section>

      {modal === "fechar" && (
        <ModalFechar
          inspecao={insp}
          enviando={ocupado}
          onCancelar={() => setModal(null)}
          onConfirmar={() => executar(() => api.fechar(id), () => setModal(null))}
        />
      )}
      {modal === "cancelar" && (
        <ModalCancelar
          codigo={insp.codigo}
          enviando={ocupado}
          onCancelar={() => setModal(null)}
          onConfirmar={(motivo) => executar(() => api.cancelar(id, motivo), () => setModal(null))}
        />
      )}
    </section>
  );
}
