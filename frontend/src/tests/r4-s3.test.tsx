import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { erroApi, inspecao, instalarApi, renderizar, rota } from "./ajuda";
import type { DadosParaCapa } from "../api/tipos";

const campo = (rotulo: string, valor: string | null, opcional = false) => ({
  rotulo, valor: valor ?? "Não informado", copiar: valor ?? "", ausente: valor === null, faltando: valor === null && !opcional,
});

function capa(parcial: Partial<DadosParaCapa> = {}): DadosParaCapa {
  const blocos = [
    {
      chave: "interessado", titulo: "1 – Interessado",
      texto: "1 – Interessado:\nMinistério Público do Estado de Mato Grosso - 1ª Promotoria de Justiça Cível\nProtocolo nº 212345/2030\nRequerente: Promotor de Justiça",
      campos: [campo("Órgão / entidade", "Ministério Público do Estado de Mato Grosso"), campo("Comarca", null, true), campo("Requerente", "Promotor de Justiça")],
    },
    {
      chave: "empreendimento", titulo: "3 – Caracterização do empreendimento",
      texto: "3 – Caracterização do empreendimento:\nNome fantasia: Fazenda Fictícia\nCAR: Não informado",
      campos: [campo("Nome fantasia / denominação", "Fazenda Fictícia"), campo("CAR", null), campo("Responsável – CPF/CNPJ", null)],
    },
  ];
  return {
    codigo: "INS-004", protocolo: "212345/2030", blocos, campos_faltando: 2,
    texto_completo: blocos.map((b) => b.texto).join("\n\n"), ...parcial,
  };
}

const abrir = async (dados = capa()) => {
  const user = userEvent.setup(); // instala a área de transferência de teste
  instalarApi(rota("GET", "/inspecoes/4/dados-capa", { corpo: dados }));
  renderizar("/inspecoes/4/capa");
  await screen.findByRole("heading", { name: /Dados para a capa e lavratura — INS-004/ });
  return user;
};

describe("Página Dados para a capa e lavratura", () => {
  test("mostra os blocos na ordem recebida, com título e campos", async () => {
    await abrir();
    const titulos = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(titulos).toEqual(["1 – Interessado", "3 – Caracterização do empreendimento"]);
    const bloco = screen.getByTestId("bloco-interessado");
    expect(bloco).toHaveTextContent("Ministério Público do Estado de Mato Grosso");
    expect(bloco).toHaveTextContent("Promotor de Justiça");
  });

  test("campo vazio aparece como 'Não informado' e destacado; o resumo conta os que faltam", async () => {
    await abrir();
    expect(screen.getByTestId("resumo-faltando")).toHaveTextContent("2 campos não informados");
    const faltando = screen.getAllByTestId("campo-faltando");
    expect(faltando).toHaveLength(2);
    for (const f of faltando) expect(f).toHaveTextContent("Não informado");
    expect(faltando[0]).toHaveTextContent("CAR");
    expect(faltando[0]).toHaveClass("campo-faltando");
  });

  test("campo opcional vazio aparece 'Não informado' sem destaque de pendência", async () => {
    await abrir();
    const comarca = screen.getByText("Comarca").closest("div")!;
    expect(comarca).toHaveTextContent("Não informado");
    expect(comarca).not.toHaveClass("campo-faltando");
    expect(comarca).toHaveClass("campo-ausente");
  });

  test("não há o que copiar em campo vazio: o botão fica desabilitado", async () => {
    await abrir();
    expect(screen.getByRole("button", { name: "Copiar CAR" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Copiar Comarca" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Copiar Requerente" })).toBeEnabled();
  });

  test("Copiar em um campo leva só o valor", async () => {
    const user = await abrir();
    await user.click(screen.getByRole("button", { name: "Copiar Requerente" }));
    expect(await navigator.clipboard.readText()).toBe("Promotor de Justiça");
    expect(screen.getByTestId("aviso-copia")).toHaveTextContent("Copiado: Requerente.");
  });

  test("Copiar bloco leva o texto do bloco, como veio da API", async () => {
    const user = await abrir();
    await user.click(screen.getByRole("button", { name: "Copiar bloco 3 – Caracterização do empreendimento" }));
    expect(await navigator.clipboard.readText()).toBe("3 – Caracterização do empreendimento:\nNome fantasia: Fazenda Fictícia\nCAR: Não informado");
  });

  test("Copiar tudo leva o texto completo", async () => {
    const dados = capa();
    const user = await abrir(dados);
    await user.click(screen.getByRole("button", { name: "Copiar tudo" }));
    expect(await navigator.clipboard.readText()).toBe(dados.texto_completo);
    expect(screen.getByTestId("aviso-copia")).toHaveTextContent("Copiado: todos os dados.");
  });

  test("quando a cópia falha, a tela avisa", async () => {
    const user = await abrir();
    vi.spyOn(navigator.clipboard, "writeText").mockRejectedValue(new Error("bloqueado"));
    await user.click(screen.getByRole("button", { name: "Copiar tudo" }));
    expect(await screen.findByText(/Não foi possível copiar todos os dados/)).toBeInTheDocument();
  });

  test("tudo preenchido: sem destaque e com a confirmação", async () => {
    await abrir(capa({
      campos_faltando: 0,
      blocos: [{ chave: "equipe", titulo: "4 – Equipe técnica", texto: "4 – Equipe técnica:\nAna", campos: [campo("Membro 1", "Ana")] }],
    }));
    expect(screen.getByTestId("resumo-faltando")).toHaveTextContent("Todos os campos estão preenchidos.");
    expect(screen.queryAllByTestId("campo-faltando")).toHaveLength(0);
  });

  test("um único campo faltando usa o singular e o link leva a Editar inspeção", async () => {
    await abrir(capa({ campos_faltando: 1 }));
    const aviso = screen.getByTestId("resumo-faltando");
    expect(aviso).toHaveTextContent("1 campo não informado");
    expect(within(aviso).getByRole("link", { name: "Editar inspeção" })).toHaveAttribute("href", "/inspecoes/4/editar");
    expect(within(aviso).getByRole("link", { name: "Locais" })).toHaveAttribute("href", "/locais");
  });

  test("inspeção inexistente mostra o erro da API", async () => {
    instalarApi(rota("GET", "/inspecoes/4/dados-capa", erroApi(404, "NAO_ENCONTRADO", "Inspeção não encontrada.")));
    renderizar("/inspecoes/4/capa");
    expect(await screen.findByRole("alert")).toHaveTextContent("Inspeção não encontrada.");
  });

  test("o detalhe da inspeção tem o link para a página", async () => {
    instalarApi(rota("GET", "/inspecoes/4", { corpo: inspecao({ status: "EM_ANDAMENTO" }) }));
    renderizar("/inspecoes/4");
    expect(await screen.findByRole("link", { name: "Dados para capa e lavratura" })).toHaveAttribute("href", "/inspecoes/4/capa");
  });
});
