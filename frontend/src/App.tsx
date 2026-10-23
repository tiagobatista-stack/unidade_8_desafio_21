import { useQuery } from "@tanstack/react-query";

export default function App() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const r = await fetch("/api/v1/health");
      if (!r.ok) throw new Error("falha");
      return (await r.json()) as { status: string };
    },
  });

  return (
    <main>
      <h1>Inspeções Simuladas</h1>
      <p>
        API:{" "}
        {health.isLoading ? "verificando…" : health.isError ? "indisponível" : health.data?.status}
      </p>
    </main>
  );
}
