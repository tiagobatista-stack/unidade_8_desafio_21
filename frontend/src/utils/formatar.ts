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

/** Máscara progressiva: 11 dígitos = CPF (000.000.000-00); mais que isso = CNPJ (00.000.000/0000-00). */
export function mascararCpfCnpj(valor: string): string {
  const d = valor.replace(/\D/g, "").slice(0, 14);
  if (d.length <= 11) {
    return d.replace(/^(\d{3})(\d)/, "$1.$2").replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3").replace(/\.(\d{3})(\d)/, ".$1-$2");
  }
  return d.replace(/^(\d{2})(\d)/, "$1.$2").replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3").replace(/\.(\d{3})(\d)/, ".$1/$2").replace(/(\d{4})(\d)/, "$1-$2");
}

/** Máscara progressiva do CEP: 00.000-000. */
export function mascararCep(valor: string): string {
  const d = valor.replace(/\D/g, "").slice(0, 8);
  return d.replace(/^(\d{2})(\d)/, "$1.$2").replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2-$3");
}

/**
 * Máscara progressiva de coordenada em graus, minutos e segundos: `11° 46' 34" S` (latitude) ou `59° 05' 12" W`
 * (longitude, graus com 3 dígitos). Só formata a digitação; minutos e segundos < 60 são conferidos pela API.
 */
export function mascararGms(texto: string, eixo: "latitude" | "longitude"): string {
  const nGraus = eixo === "latitude" ? 2 : 3;
  const letras = eixo === "latitude" ? "NS" : "EWO";
  const d = texto.replace(/\D/g, "").slice(0, nGraus + 4);
  const letra = [...texto.toUpperCase()].reverse().find((c) => letras.includes(c));
  const graus = d.slice(0, nGraus), min = d.slice(nGraus, nGraus + 2), seg = d.slice(nGraus + 2);
  let saida = graus;
  if (min) saida += `° ${min}`;
  if (seg) saida += `' ${seg}`;
  if (letra) saida += `${seg.length === 2 ? '"' : ""} ${letra === "O" ? "W" : letra}`;
  return saida;
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
