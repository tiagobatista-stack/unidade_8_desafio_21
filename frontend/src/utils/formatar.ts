export const VAZIO = "—";

/** "2026-10-20" -> "20/10/2026" (sem passar por Date, para não sofrer com fuso). */
export function formatarData(iso: string | null | undefined): string {
  if (!iso) return VAZIO;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : VAZIO;
}

/** "2026-10-23T17:05:00" -> "23/10/2026 17:05" (sem passar por Date, para não sofrer com fuso). */
export function formatarDataHora(iso: string | null | undefined): string {
  if (!iso) return VAZIO;
  const m = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/.exec(iso);
  return m ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}` : VAZIO;
}

/** "65900000001" -> "(65) 90000-0001" (só apresentação; a validação do telefone é do backend). */
export function formatarTelefone(valor: string | null | undefined): string {
  const d = (valor ?? "").replace(/\D/g, "");
  if (d.length !== 10 && d.length !== 11) return valor ?? "";
  const cabeca = d.length === 11 ? 5 : 4;
  return `(${d.slice(0, 2)}) ${d.slice(2, 2 + cabeca)}-${d.slice(2 + cabeca)}`;
}

/** Só informativo: UF-código IBGE-código (padrão SICAR). Outros formatos continuam aceitos. */
export const segueModeloSicar = (car: string) => /^[A-Za-z]{2}-\d{7}-[A-Za-z0-9]+$/.test(car.trim());

export const ROTULO_STATUS: Record<string, string> = {
  ABERTA: "Aberta",
  EM_ANDAMENTO: "Em andamento",
  FINALIZADA: "Finalizada",
  CANCELADA: "Cancelada",
};

export const ROTULO_SITUACAO: Record<string, string> = {
  NAO_RESPONDIDO: "Não respondido",
  CONFORME: "Conforme",
  NAO_CONFORME: "Não conforme",
  NAO_SE_APLICA: "Não se aplica",
};

export const ROTULO_RESULTADO: Record<string, string> = {
  APROVADA: "Aprovada",
  APROVADA_COM_RESSALVAS: "Aprovada com ressalvas",
  REPROVADA: "Reprovada",
};

export const rotuloStatus = (s: string) => ROTULO_STATUS[s] ?? s;
export const rotuloResultado = (r: string | null) => (r ? (ROTULO_RESULTADO[r] ?? r) : VAZIO);
export const rotuloSituacao = (s: string) => ROTULO_SITUACAO[s] ?? s;

export const somenteLeitura = (status: string) => status === "FINALIZADA" || status === "CANCELADA";
