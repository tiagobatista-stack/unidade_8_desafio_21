import { useState } from "react";
import { Link } from "react-router-dom";
import { api, URL_CSV } from "../api/api";
import { paraErro } from "../api/cliente";
import { Carregando, MensagemErro, Modal } from "../components/Basicos";
import { useIndicadores, useInvalidarTudo } from "../hooks/useDados";

/** Cada cartão leva à lista da própria categoria (os grupos são resolvidos em InspecoesPage). */
function Cartao({ id, titulo, valor, filtro }: { id: string; titulo: string; valor: number; filtro: string }) {
  return (
    <Link
      className="indicador"
      data-testid={`indicador-${id}`}
      to={`/inspecoes?status=${filtro}`}
      aria-label={`${titulo}: ${valor}. Ver lista`}
    >
      <span className="indicador-valor">{valor}</span>
      <span className="indicador-titulo">{titulo}</span>
      <span className="indicador-acao">Ver lista →</span>
    </Link>
  );
}

export default function PainelPage() {
  const { data, isLoading, error } = useIndicadores();
  const invalidar = useInvalidarTudo();
  const [confirmando, setConfirmando] = useState(false);
  const [erroAcao, setErroAcao] = useState<unknown>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function carregarExemplos() {
    setCarregando(true);
    setErroAcao(null);
    try {
      const r = await api.carregarExemplos();
      setAviso(`Exemplos carregados: ${r.locais} locais, ${r.inspecoes} inspeções e ${r.fotos} fotos fictícias.`);
      invalidar();
    } catch (e) {
      setErroAcao(paraErro(e));
    } finally {
      setCarregando(false);
      setConfirmando(false);
    }
  }

  return (
    <section>
      <h1>Painel</h1>
      {isLoading && <Carregando />}
      <MensagemErro erro={error} />
      {data && (
        <div className="indicadores">
          <Cartao id="inspecoes" titulo="Inspeções" valor={data.inspecoes} filtro="ATIVAS" />
          <Cartao id="pendencias" titulo="Pendências" valor={data.pendencias} filtro="PENDENTES" />
          <Cartao id="finalizadas" titulo="Finalizadas" valor={data.finalizadas} filtro="FINALIZADA" />
        </div>
      )}
      <div className="acoes">
        <Link className="botao" to="/inspecoes/nova">Nova inspeção</Link>
        <Link className="botao secundario" to="/inspecoes?status=PENDENTES">Ver pendências</Link>
        <button type="button" className="secundario" onClick={() => setConfirmando(true)}>Carregar exemplos</button>
        <a className="botao secundario" href={URL_CSV} download="inspecoes.csv">Exportar CSV</a>
      </div>
      {aviso && <div role="status" className="alerta alerta-ok">{aviso}</div>}
      <MensagemErro erro={erroAcao} />
      {confirmando && (
        <Modal titulo="Carregar dados de exemplo" onFechar={() => setConfirmando(false)}>
          <p>Serão criados locais, inspeções e fotos <strong>fictícios</strong>. Só é possível em um banco sem dados.</p>
          <div className="acoes">
            <button type="button" disabled={carregando} onClick={carregarExemplos}>Confirmar</button>
            <button type="button" className="secundario" onClick={() => setConfirmando(false)}>Voltar</button>
          </div>
        </Modal>
      )}
    </section>
  );
}
