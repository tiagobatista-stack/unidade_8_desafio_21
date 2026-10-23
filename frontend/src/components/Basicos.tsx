import type { ReactNode } from "react";
import { ApiErro } from "../api/cliente";

export function MensagemErro({ erro }: { erro: unknown }) {
  if (!erro) return null;
  const e = erro instanceof ApiErro ? erro : new ApiErro(0, "ERRO", "Ocorreu um erro inesperado.");
  return (
    <div role="alert" className="alerta alerta-erro">
      <strong>{e.message}</strong>
      {e.detalhes.length > 0 && (
        <ul>
          {e.detalhes.map((d, i) => (
            <li key={i}>
              {d.campo ? <code>{d.campo}</code> : null} {d.mensagem}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export const Carregando = ({ texto = "Carregando…" }: { texto?: string }) => (
  <p role="status" className="estado">{texto}</p>
);

export const Vazio = ({ texto }: { texto: string }) => <p className="estado vazio">{texto}</p>;

export function Modal({ titulo, onFechar, children }: { titulo: string; onFechar: () => void; children: ReactNode }) {
  return (
    <div className="modal-fundo" onClick={onFechar}>
      <div role="dialog" aria-modal="true" aria-label={titulo} className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{titulo}</h2>
        {children}
      </div>
    </div>
  );
}

/** Texto puro com quebras preservadas; o React já escapa qualquer HTML. */
export const TextoPuro = ({ valor }: { valor: string | null | undefined }) =>
  valor ? <p className="texto-puro">{valor}</p> : <p className="texto-puro">—</p>;

export const Selo = ({ tipo, children }: { tipo: string; children: ReactNode }) => (
  <span className={`selo selo-${tipo.toLowerCase()}`}>{children}</span>
);
