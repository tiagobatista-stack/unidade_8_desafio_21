import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/api";
import type { FiltrosLista } from "../api/tipos";

export const useIndicadores = () => useQuery({ queryKey: ["indicadores"], queryFn: api.indicadores });
export const useLocais = () => useQuery({ queryKey: ["locais"], queryFn: api.locais });
export const useLocal = (id: number, habilitado = true) =>
  useQuery({ queryKey: ["locais", id], queryFn: () => api.local(id), enabled: habilitado });
export const useRelatorio = (id: number) =>
  useQuery({ queryKey: ["inspecoes", "relatorio", id], queryFn: () => api.relatorio(id) });
export const useInspecoes = (f: FiltrosLista) =>
  useQuery({ queryKey: ["inspecoes", "lista", f], queryFn: () => api.inspecoes(f) });
export const useInspecao = (id: number) =>
  useQuery({ queryKey: ["inspecoes", "detalhe", id], queryFn: () => api.inspecao(id) });

/** Após qualquer gravação, invalida tudo: indicadores, listas e detalhe atualizam sem recarregar a página. */
export function useInvalidarTudo() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries();
}
