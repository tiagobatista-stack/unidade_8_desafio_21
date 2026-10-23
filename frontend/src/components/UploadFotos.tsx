import { useEffect, useRef, useState } from "react";
import { api } from "../api/api";
import { paraErro, ApiErro } from "../api/cliente";
import type { Item } from "../api/tipos";
import { MensagemErro } from "./Basicos";

export const LIMITE_ANOTACAO = 1000;
export const LIMITE_LEGENDA = 200;

interface Pendente {
  id: number;
  arquivo: File;
  preview: string;
  anotacao: string;
  legenda: string;
  itemId: string;
  estado: "pendente" | "enviando" | "erro";
  erro?: ApiErro;
}

interface Props {
  inspecaoId: number;
  itens: Item[];
  onEnviada: () => void;
}

let proximoId = 1;

export function UploadFotos({ inspecaoId, itens, onEnviada }: Props) {
  const [pendentes, setPendentes] = useState<Pendente[]>([]);
  const [progresso, setProgresso] = useState<{ atual: number; total: number } | null>(null);
  const [arrastando, setArrastando] = useState(false);
  const entrada = useRef<HTMLInputElement>(null);
  const previews = useRef<string[]>([]);

  useEffect(() => () => previews.current.forEach((u) => URL.revokeObjectURL?.(u)), []);

  const adicionar = (arquivos: FileList | File[]) => {
    const novos = Array.from(arquivos).map<Pendente>((arquivo) => {
      const preview = URL.createObjectURL?.(arquivo) ?? "";
      previews.current.push(preview);
      return { id: proximoId++, arquivo, preview, anotacao: "", legenda: "", itemId: "", estado: "pendente" };
    });
    setPendentes((p) => [...p, ...novos]);
  };

  const alterar = (id: number, parcial: Partial<Pendente>) =>
    setPendentes((p) => p.map((x) => (x.id === id ? { ...x, ...parcial } : x)));
  const remover = (id: number) => setPendentes((p) => p.filter((x) => x.id !== id));

  const todasAnotadas = pendentes.length > 0 && pendentes.every((p) => p.anotacao.trim().length > 0);
  const enviando = progresso !== null;

  async function enviar() {
    const fila = pendentes.filter((p) => p.anotacao.trim());
    setProgresso({ atual: 0, total: fila.length });
    let n = 0;
    for (const p of fila) {
      n += 1;
      setProgresso({ atual: n, total: fila.length });
      alterar(p.id, { estado: "enviando", erro: undefined });
      const form = new FormData();
      form.append("arquivo", p.arquivo);
      form.append("anotacao", p.anotacao);
      if (p.legenda.trim()) form.append("legenda", p.legenda);
      if (p.itemId) form.append("item_id", p.itemId);
      try {
        await api.enviarFoto(inspecaoId, form); // uma foto por requisição
        remover(p.id);
      } catch (e) {
        alterar(p.id, { estado: "erro", erro: paraErro(e) }); // mantém a anotação digitada
      }
    }
    setProgresso(null);
    onEnviada();
  }

  return (
    <div className="upload">
      <div
        className={`soltar${arrastando ? " ativo" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setArrastando(true); }}
        onDragLeave={() => setArrastando(false)}
        onDrop={(e) => { e.preventDefault(); setArrastando(false); adicionar(e.dataTransfer.files); }}
      >
        <p>Arraste imagens (JPEG, PNG ou WebP) aqui ou</p>
        <input
          ref={entrada}
          type="file"
          multiple
          accept="image/jpeg,image/png,image/webp"
          aria-label="Selecionar fotos"
          onChange={(e) => { if (e.target.files) adicionar(e.target.files); e.target.value = ""; }}
        />
      </div>

      {pendentes.length > 0 && (
        <>
          <h3>Fotos pendentes ({pendentes.length})</h3>
          <ul className="pendentes">
            {pendentes.map((p) => (
              <li key={p.id} className={`pendente pendente-${p.estado}`} data-testid="foto-pendente">
                {p.preview && <img src={p.preview} alt="" className="miniatura-pendente" />}
                <div className="pendente-campos">
                  <p className="nome-arquivo">{p.arquivo.name}</p>
                  <label>
                    O que foi observado nesta foto? *
                    <textarea
                      aria-label={`Anotação de ${p.arquivo.name}`}
                      rows={2}
                      value={p.anotacao}
                      disabled={p.estado === "enviando"}
                      onChange={(e) => alterar(p.id, { anotacao: e.target.value })}
                    />
                  </label>
                  <span className={p.anotacao.length > LIMITE_ANOTACAO ? "contador excedido" : "contador"}>
                    {p.anotacao.length}/{LIMITE_ANOTACAO}
                  </span>
                  <label>
                    Legenda (opcional)
                    <input
                      aria-label={`Legenda de ${p.arquivo.name}`}
                      value={p.legenda}
                      onChange={(e) => alterar(p.id, { legenda: e.target.value })}
                    />
                  </label>
                  <label>
                    Item (opcional)
                    <select
                      aria-label={`Item de ${p.arquivo.name}`}
                      value={p.itemId}
                      onChange={(e) => alterar(p.id, { itemId: e.target.value })}
                    >
                      <option value="">Sem vínculo</option>
                      {itens.map((i) => (
                        <option key={i.id} value={i.id}>{i.descricao}</option>
                      ))}
                    </select>
                  </label>
                  {p.erro && <MensagemErro erro={p.erro} />}
                </div>
                <button type="button" className="secundario" disabled={p.estado === "enviando"} onClick={() => remover(p.id)}>
                  Descartar
                </button>
              </li>
            ))}
          </ul>
          <div className="linha-entre">
            {enviando ? (
              <span role="status">Enviando {progresso!.atual} de {progresso!.total}…</span>
            ) : !todasAnotadas ? (
              <span className="dica">Preencha a anotação de todas as fotos para enviar.</span>
            ) : (
              <span />
            )}
            <button type="button" disabled={!todasAnotadas || enviando} onClick={enviar}>
              Enviar
            </button>
          </div>
        </>
      )}
    </div>
  );
}
