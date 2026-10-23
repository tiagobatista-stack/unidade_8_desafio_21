export const VAZIO = "—";

/** "2026-10-20" -> "20/10/2026" (sem passar por Date, para não sofrer com fuso). */
export function formatarData(iso: string | null | undefined): string {
  if (!iso) return VAZIO;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : VAZIO;
}

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
