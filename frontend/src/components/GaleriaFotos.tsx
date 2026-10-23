import { useState } from "react";
import type { Foto, Item } from "../api/tipos";
import { Selo } from "./Basicos";
import { VisualizadorFoto } from "./VisualizadorFoto";

interface Props {
  inspecaoId: number;
  fotos: Foto[];
  itens: Item[];
  editavel: boolean;
  onMudou: () => void;
}

const trecho = (t: string, n = 90) => (t.length > n ? t.slice(0, n) + "…" : t);

export function GaleriaFotos({ inspecaoId, fotos, itens, editavel, onMudou }: Props) {
  const [aberta, setAberta] = useState<number | null>(null);
  if (fotos.length === 0) return <p className="estado vazio">Nenhuma foto anexada.</p>;
  const item = (id: number | null) => itens.find((i) => i.id === id);
  return (
    <>
      <ul className="galeria">
        {fotos.map((f, idx) => (
          <li key={f.id} data-testid="foto-galeria">
            <button type="button" className="foto-botao" onClick={() => setAberta(idx)} aria-label={`Abrir foto ${idx + 1}`}>
              <img src={f.url_miniatura} alt={f.legenda ?? `Foto ${idx + 1}`} loading="lazy" />
            </button>
            {f.legenda && <p className="legenda">{f.legenda}</p>}
            <p className="texto-puro anotacao-trecho">{trecho(f.anotacao)}</p>
            {item(f.item_id) && <Selo tipo="item">{trecho(item(f.item_id)!.descricao, 36)}</Selo>}
          </li>
        ))}
      </ul>
      {aberta !== null && fotos[aberta] && (
        <VisualizadorFoto
          inspecaoId={inspecaoId}
          fotos={fotos}
          itens={itens}
          indice={aberta}
          editavel={editavel}
          onIndice={setAberta}
          onFechar={() => setAberta(null)}
          onMudou={onMudou}
        />
      )}
    </>
  );
}
