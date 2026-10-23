import { api } from "../api/api";
import type { Local } from "../api/tipos";
import { FormularioLocal } from "./FormularioLocal";
import { Modal } from "./Basicos";

interface Props {
  onCriado: (local: Local) => void | Promise<void>;
  onCancelar: () => void;
}

/** "Novo local" dentro de Nova inspeção; o formulário é o mesmo da tela Locais. */
export function ModalNovoLocal({ onCriado, onCancelar }: Props) {
  return (
    <Modal titulo="Novo local" onFechar={onCancelar}>
      <FormularioLocal rotuloSalvar="Salvar local" salvar={api.criarLocal} onSalvo={onCriado} onCancelar={onCancelar} />
    </Modal>
  );
}
