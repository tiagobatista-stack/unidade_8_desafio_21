import { useEffect, useState } from "react";
import { TextoPuro } from "./Basicos";

export const LIMITE_OBS = 2000;

interface Props {
  valor: string | null;
  editavel: boolean;
  salvando?: boolean;
  onSalvar: (texto: string) => void;
}

export function BlocoObservacoesVistoria({ valor, editavel, salvando, onSalvar }: Props) {
  const [texto, setTexto] = useState(valor ?? "");
  useEffect(() => setTexto(valor ?? ""), [valor]);
  return (
    <section aria-labelledby="titulo-obs-vistoria" className="cartao">
      <h2 id="titulo-obs-vistoria">Observações da vistoria (o que foi visualizado)</h2>
      {editavel ? (
        <>
          <label htmlFor="obs-vistoria" className="sr-only">Observações da vistoria</label>
          <textarea id="obs-vistoria" name="obs-vistoria"
            aria-label="Observações da vistoria"
            rows={5}
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
          />
          <div className="linha-entre">
            <span data-testid="contador-obs" className={texto.length > LIMITE_OBS ? "contador excedido" : "contador"}>
              {texto.length}/{LIMITE_OBS}
            </span>
            <button type="button" disabled={salvando || texto === (valor ?? "")} onClick={() => onSalvar(texto)}>
              Salvar observações
            </button>
          </div>
        </>
      ) : (
        <TextoPuro valor={valor} />
      )}
    </section>
  );
}
