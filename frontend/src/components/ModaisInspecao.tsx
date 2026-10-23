import { useState } from "react";
import type { InspecaoDetalhe } from "../api/tipos";
import { Modal, TextoPuro } from "./Basicos";

interface PropsFechar {
  inspecao: InspecaoDetalhe;
  enviando: boolean;
  onConfirmar: () => void;
  onCancelar: () => void;
}

export function ModalFechar({ inspecao, enviando, onConfirmar, onCancelar }: PropsFechar) {
  // Aviso não bloqueante: item NÃO CONFORME sem foto (RN25). É só exibição; quem bloqueia é a API.
  const semFoto = inspecao.itens.filter((i) => i.situacao === "NAO_CONFORME" && i.qtd_fotos === 0);
  return (
    <Modal titulo={`Fechar inspeção ${inspecao.codigo}`} onFechar={onCancelar}>
      <h3>Observações da vistoria</h3>
      <TextoPuro valor={inspecao.observacoes_vistoria} />
      <p>Fotos anexadas: <strong>{inspecao.fotos.length}</strong></p>
      {semFoto.length > 0 && (
        <div role="note" className="alerta alerta-aviso">
          Itens não conformes sem foto: {semFoto.map((i) => i.descricao).join("; ")}. O fechamento não é bloqueado.
        </div>
      )}
      <p>O resultado será calculado ao fechar e a inspeção ficará somente leitura.</p>
      <div className="acoes">
        <button type="button" disabled={enviando} onClick={onConfirmar}>Confirmar fechamento</button>
        <button type="button" className="secundario" onClick={onCancelar}>Voltar</button>
      </div>
    </Modal>
  );
}

interface PropsCancelar {
  codigo: string;
  enviando: boolean;
  onConfirmar: (motivo: string) => void;
  onCancelar: () => void;
}

export function ModalCancelar({ codigo, enviando, onConfirmar, onCancelar }: PropsCancelar) {
  const [motivo, setMotivo] = useState("");
  return (
    <Modal titulo={`Cancelar inspeção ${codigo}`} onFechar={onCancelar}>
      <label>
        Motivo do cancelamento *
        <textarea aria-label="Motivo do cancelamento" rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
      </label>
      <div className="acoes">
        <button type="button" className="perigo" disabled={enviando || !motivo.trim()} onClick={() => onConfirmar(motivo)}>
          Confirmar cancelamento
        </button>
        <button type="button" className="secundario" onClick={onCancelar}>Voltar</button>
      </div>
    </Modal>
  );
}
