import { useState, type FormEvent } from "react";
import { api } from "../api/api";
import { paraErro } from "../api/cliente";
import type { Local } from "../api/tipos";
import { MensagemErro, Modal } from "./Basicos";

interface Props {
  onCriado: (local: Local) => void | Promise<void>;
  onCancelar: () => void;
}

/** Aceita vírgula ou ponto como separador decimal; devolve NaN se não for número. */
const numero = (texto: string) => (texto.trim() === "" ? NaN : Number(texto.trim().replace(",", ".")));

export function ModalNovoLocal({ onCriado, onCancelar }: Props) {
  const [campos, setCampos] = useState({ nome: "", municipio: "", tipo: "", latitude: "", longitude: "" });
  const [tentou, setTentou] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<unknown>(null);

  const mudar = (campo: keyof typeof campos, valor: string) => setCampos((c) => ({ ...c, [campo]: valor }));
  // Só presença e sintaxe numérica; a faixa de Mato Grosso é validada pela API (RN11).
  const faltando = {
    nome: !campos.nome.trim(),
    municipio: !campos.municipio.trim(),
    tipo: !campos.tipo.trim(),
    latitude: !Number.isFinite(numero(campos.latitude)),
    longitude: !Number.isFinite(numero(campos.longitude)),
  };

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setTentou(true);
    setErro(null);
    if (Object.values(faltando).some(Boolean)) return;
    setEnviando(true);
    try {
      const local = await api.criarLocal({
        nome: campos.nome,
        municipio: campos.municipio,
        tipo: campos.tipo,
        latitude: numero(campos.latitude),
        longitude: numero(campos.longitude),
      });
      await onCriado(local);
    } catch (e2) {
      setErro(paraErro(e2));
    } finally {
      setEnviando(false);
    }
  }

  const aviso = (campo: keyof typeof faltando, texto: string) =>
    tentou && faltando[campo] ? <span className="campo-erro">{texto}</span> : null;

  return (
    <Modal titulo="Novo local" onFechar={onCancelar}>
      <form onSubmit={salvar} noValidate className="formulario">
        <label>
          Nome *
          <input aria-label="Nome do local" value={campos.nome} onChange={(e) => mudar("nome", e.target.value)} />
          {aviso("nome", "Informe o nome.")}
        </label>
        <label>
          Município *
          <input aria-label="Município do local" value={campos.municipio} onChange={(e) => mudar("municipio", e.target.value)} />
          {aviso("municipio", "Informe o município.")}
        </label>
        <label>
          Tipo *
          <input aria-label="Tipo do local" placeholder="Ex.: Propriedade rural" value={campos.tipo} onChange={(e) => mudar("tipo", e.target.value)} />
          {aviso("tipo", "Informe o tipo.")}
        </label>
        <div className="duas-colunas">
          <label>
            Latitude *
            <input aria-label="Latitude do local" inputMode="decimal" placeholder="-10.42318" value={campos.latitude} onChange={(e) => mudar("latitude", e.target.value)} />
            {aviso("latitude", "Informe um número.")}
          </label>
          <label>
            Longitude *
            <input aria-label="Longitude do local" inputMode="decimal" placeholder="-58.71264" value={campos.longitude} onChange={(e) => mudar("longitude", e.target.value)} />
            {aviso("longitude", "Informe um número.")}
          </label>
        </div>
        <p className="dica">Coordenadas devem estar dentro de Mato Grosso (latitude −18,05 a −7,35; longitude −61,65 a −50,20).</p>
        <MensagemErro erro={erro} />
        <div className="acoes">
          <button type="submit" disabled={enviando}>Salvar local</button>
          <button type="button" className="secundario" onClick={onCancelar}>Cancelar</button>
        </div>
      </form>
    </Modal>
  );
}
