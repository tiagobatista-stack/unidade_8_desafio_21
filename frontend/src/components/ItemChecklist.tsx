import { useEffect, useState } from "react";
import type { Item, Situacao } from "../api/tipos";
import { ROTULO_SITUACAO, VAZIO } from "../utils/formatar";
import { Selo } from "./Basicos";

interface Props {
  item: Item;
  editavel: boolean;
  destacado?: string;
  onSituacao: (situacao: Situacao) => void;
  onObservacao: (observacao: string) => void;
  onRemover: () => void;
}

export function ItemChecklist({ item, editavel, destacado, onSituacao, onObservacao, onRemover }: Props) {
  const [obs, setObs] = useState(item.observacao ?? "");
  useEffect(() => setObs(item.observacao ?? ""), [item.observacao]);
  const alterada = obs !== (item.observacao ?? "");
  return (
    <li className={`item${destacado ? " item-destacado" : ""}`} data-testid={`item-${item.id}`}>
      <div className="item-topo">
        <span className="item-descricao">{item.descricao}</span>
        {item.critico && <Selo tipo="critico">Crítico</Selo>}
        {item.origem === "AVULSO" && <Selo tipo="avulso">Avulso</Selo>}
        {item.qtd_fotos > 0 && <Selo tipo="fotos">{item.qtd_fotos} foto(s)</Selo>}
      </div>
      {destacado && <p className="item-motivo" role="note">{destacado}</p>}
      {editavel ? (
        <div className="item-campos">
          <label>
            Situação
            <select
              aria-label={`Situação de ${item.descricao}`}
              value={item.situacao}
              onChange={(e) => onSituacao(e.target.value as Situacao)}
            >
              {Object.entries(ROTULO_SITUACAO).map(([v, r]) => (
                <option key={v} value={v}>{r}</option>
              ))}
            </select>
          </label>
          <label className="campo-largo">
            Observação
            <textarea
              aria-label={`Observação de ${item.descricao}`}
              rows={2}
              value={obs}
              onChange={(e) => setObs(e.target.value)}
            />
          </label>
          <button type="button" disabled={!alterada} onClick={() => onObservacao(obs)}>Salvar observação</button>
          {item.origem === "AVULSO" && (
            <button type="button" className="perigo" onClick={onRemover}>Remover item</button>
          )}
        </div>
      ) : (
        <p className="item-leitura">
          <strong>{ROTULO_SITUACAO[item.situacao]}</strong> · Observação: <span className="texto-puro">{item.observacao || VAZIO}</span>
        </p>
      )}
    </li>
  );
}
