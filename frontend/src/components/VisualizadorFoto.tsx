import { useEffect, useState } from "react";
import { api } from "../api/api";
import { paraErro, urlApi } from "../api/cliente";
import type { Foto, Item } from "../api/tipos";
import { MensagemErro, Modal, TextoPuro } from "./Basicos";
import { LIMITE_ANOTACAO } from "./UploadFotos";

interface Props {
  inspecaoId: number;
  fotos: Foto[];
  itens: Item[];
  indice: number;
  editavel: boolean;
  onIndice: (i: number) => void;
  onFechar: () => void;
  onMudou: () => void;
}

export function VisualizadorFoto({ inspecaoId, fotos, itens, indice, editavel, onIndice, onFechar, onMudou }: Props) {
  const foto = fotos[indice];
  const [editando, setEditando] = useState(false);
  const [anotacao, setAnotacao] = useState(foto.anotacao);
  const [legenda, setLegenda] = useState(foto.legenda ?? "");
  const [itemId, setItemId] = useState(foto.item_id ? String(foto.item_id) : "");
  const [confirmando, setConfirmando] = useState(false);
  const [erro, setErro] = useState<unknown>(null);

  useEffect(() => {
    setEditando(false);
    setConfirmando(false);
    setErro(null);
    setAnotacao(foto.anotacao);
    setLegenda(foto.legenda ?? "");
    setItemId(foto.item_id ? String(foto.item_id) : "");
  }, [foto.id, foto.anotacao, foto.legenda, foto.item_id]);

  async function salvar() {
    setErro(null);
    try {
      await api.editarFoto(inspecaoId, foto.id, {
        anotacao,
        legenda: legenda.trim() ? legenda : null,
        item_id: itemId ? Number(itemId) : null,
      });
      setEditando(false);
      onMudou();
    } catch (e) {
      setErro(paraErro(e));
    }
  }

  async function excluir() {
    setErro(null);
    try {
      await api.excluirFoto(inspecaoId, foto.id);
      onMudou();
      if (fotos.length <= 1) onFechar();
      else onIndice(Math.max(0, indice - (indice === fotos.length - 1 ? 1 : 0)));
    } catch (e) {
      setErro(paraErro(e));
      setConfirmando(false);
    }
  }

  const vinculo = itens.find((i) => i.id === foto.item_id);
  return (
    <Modal titulo={`Foto ${indice + 1} de ${fotos.length}`} onFechar={onFechar}>
      <img src={urlApi(foto.url_original)} alt={foto.legenda ?? foto.nome_original} className="foto-grande" />
      {!editando ? (
        <>
          {foto.legenda && <p className="legenda"><strong>{foto.legenda}</strong></p>}
          <h3>Anotação</h3>
          <TextoPuro valor={foto.anotacao} />
          <p className="dica">Item: {vinculo ? vinculo.descricao : "sem vínculo"} · Arquivo: {foto.nome_original}</p>
        </>
      ) : (
        <div className="item-campos coluna">
          <label htmlFor="foto-editar-anotacao">
            Anotação *
            <textarea id="foto-editar-anotacao" name="foto-editar-anotacao" aria-label="Editar anotação" rows={4} value={anotacao} onChange={(e) => setAnotacao(e.target.value)} />
          </label>
          <span className={anotacao.length > LIMITE_ANOTACAO ? "contador excedido" : "contador"}>
            {anotacao.length}/{LIMITE_ANOTACAO}
          </span>
          <label htmlFor="foto-editar-legenda">
            Legenda
            <input id="foto-editar-legenda" name="foto-editar-legenda" aria-label="Editar legenda" value={legenda} onChange={(e) => setLegenda(e.target.value)} />
          </label>
          <label htmlFor="foto-editar-vinculo">
            Item
            <select id="foto-editar-vinculo" name="foto-editar-vinculo" aria-label="Editar vínculo" value={itemId} onChange={(e) => setItemId(e.target.value)}>
              <option value="">Sem vínculo</option>
              {itens.map((i) => (
                <option key={i.id} value={i.id}>{i.descricao}</option>
              ))}
            </select>
          </label>
        </div>
      )}
      <MensagemErro erro={erro} />
      <div className="acoes">
        <button type="button" className="secundario" disabled={indice === 0} onClick={() => onIndice(indice - 1)}>Anterior</button>
        <button type="button" className="secundario" disabled={indice === fotos.length - 1} onClick={() => onIndice(indice + 1)}>Próxima</button>
        {editavel && !editando && !confirmando && (
          <>
            <button type="button" onClick={() => setEditando(true)}>Editar</button>
            <button type="button" className="perigo" onClick={() => setConfirmando(true)}>Excluir</button>
          </>
        )}
        {editavel && editando && (
          <>
            <button type="button" onClick={salvar}>Salvar</button>
            <button type="button" className="secundario" onClick={() => setEditando(false)}>Cancelar edição</button>
          </>
        )}
        {editavel && confirmando && (
          <>
            <span>Excluir esta foto definitivamente?</span>
            <button type="button" className="perigo" onClick={excluir}>Confirmar exclusão</button>
            <button type="button" className="secundario" onClick={() => setConfirmando(false)}>Voltar</button>
          </>
        )}
        <button type="button" className="secundario" onClick={onFechar}>Fechar</button>
      </div>
    </Modal>
  );
}
