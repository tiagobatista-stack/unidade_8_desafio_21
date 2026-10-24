import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync } from "node:fs";
import { erroApi, inspecao, instalarApi, relatorio, renderizar, rota } from "./ajuda";
import type { Relatorio } from "../api/tipos";

const comRelatorio = (r = relatorio()) => rota("GET", "/inspecoes/4/relatorio", () => ({ corpo: r }));
const comFotos = (r: Relatorio, fotos: Relatorio["constatacoes"]["fotos"]): Relatorio => ({ ...r, constatacoes: { ...r.constatacoes, fotos } });
const comRelato = (r: Relatorio, relato: Partial<Relatorio["constatacoes"]["relato"]>): Relatorio => ({
  ...r, constatacoes: { ...r.constatacoes, relato: { ...r.constatacoes.relato, ...relato } },
});

describe("Corpo do relatório finalizado (a partir do item 5)", () => {
  test("começa no item 5 e mostra 5, 6 e 7, sem os itens 1 a 4 da capa", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    await screen.findByTestId("cabecalho-relatorio");
    const secoes = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(secoes).toEqual(["5 – Constatações", "6 – Providências tomadas", "7 – Conclusão"]);
    const sub = screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent);
    expect(sub).toEqual(["5.1 Relato da vistoria", "5.2 Checklist", "5.3 Registro fotográfico"]);
    const texto = screen.getByTestId("relatorio").textContent ?? "";
    for (const fora of ["Interessado", "Equipe técnica", "Caracterização", "Empreendimento", "CAR", "Assinatura", "1. Identificação", "Objetivo"]) {
      expect(texto).not.toContain(fora);
    }
  });

  test("cabeçalho mínimo no formato da capa, sem título de capa, e rodapé com Ref. interna", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("cabecalho-relatorio")).toHaveTextContent(
      "Protocolo nº SEMA-PRO-2026/12345 | Inspeção INS-004 | Ref. interna 0004/2026");
    expect(screen.queryByText(/Relatório de Vistoria/)).not.toBeInTheDocument();
    expect(screen.queryByTestId("marca-dagua")).not.toBeInTheDocument();
    expect(screen.queryByTestId("faixa-previa")).not.toBeInTheDocument();
    expect(screen.getByTestId("rodape-relatorio")).toHaveTextContent("Ref. interna 0004/2026 · INS-004 · Sistema fictício/simulado");
  });

  test("com o número da SEMA informado o cabeçalho o mostra", async () => {
    const base = relatorio();
    instalarApi(comRelatorio({ ...base, cabecalho: { ...base.cabecalho, numero_relatorio_sema: "RT-0099/2030", linha: `${base.cabecalho.linha} | Relatório SEMA nº RT-0099/2030` } }));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("cabecalho-relatorio")).toHaveTextContent("| Relatório SEMA nº RT-0099/2030");
  });

  test("5.1 relato: data da vistoria e observações da vistoria em texto puro (HTML literal)", async () => {
    instalarApi(comRelatorio(comRelato(relatorio(), { observacoes_vistoria: "<script>alert(1)</script>\nlinha 2" })));
    const { container } = renderizar("/inspecoes/4/relatorio");
    const sec = (await screen.findByRole("region", { name: "5 – Constatações" })) as HTMLElement;
    expect(screen.getByTestId("rel-data-vistoria")).toHaveTextContent("21/10/2026");
    expect(sec).toHaveTextContent("<script>alert(1)</script>");
    expect(container.querySelector("script")).toBeNull();
  });

  test("5.1 sem data nem observações mostra traço", async () => {
    instalarApi(comRelatorio(comRelato(relatorio(), { data_realizacao: null, observacoes_vistoria: null })));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("rel-data-vistoria")).toHaveTextContent("—");
  });

  test("5.2 checklist numerado, crítico sim/não, situação, observação, totais e destaque do crítico não conforme", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    const linhas = await screen.findAllByTestId("linha-checklist");
    expect(linhas).toHaveLength(4);
    const cel = (l: HTMLElement) => within(l).getAllByRole("cell").map((c) => c.textContent);
    expect(cel(linhas[0])).toEqual(["1", "Licença ambiental", "Sim", "Conforme", "—"]);
    expect(cel(linhas[2])).toEqual(["3", "Sinalização", "Não", "Não conforme", "Placa gasta"]);
    expect(cel(linhas[3])[3]).toBe("Não se aplica");
    expect(linhas[1]).toHaveClass("linha-critica"); // crítico não conforme
    expect(linhas[1]).toHaveTextContent("CRÍTICO NÃO CONFORME");
    expect(linhas[2]).not.toHaveClass("linha-critica"); // não conforme, mas não crítico
    expect(screen.getByTestId("totais-checklist")).toHaveTextContent("4 de 4 respondidos · 1 conformes · 2 não conformes · 1 não aplicáveis");
  });

  test("totais mostram não respondidos quando existirem", async () => {
    const base = relatorio();
    const checklist = { ...base.constatacoes.checklist, totais: { ...base.constatacoes.checklist.totais, respondidos: 3, nao_respondidos: 1 } };
    instalarApi(comRelatorio({ ...base, constatacoes: { ...base.constatacoes, checklist } }));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("totais-checklist")).toHaveTextContent("1 não respondidos");
  });

  test("5.3 fotos numeradas com original, legenda, anotação, item vinculado, 'Sem vínculo' e data de captura", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    const fotos = await screen.findAllByTestId("foto-relatorio");
    expect(fotos).toHaveLength(3);
    expect(fotos[0]).toHaveTextContent("Foto 1 — Caixa separadora");
    expect(fotos[0]).toHaveTextContent("Transbordamento junto à base.");
    expect(fotos[0]).toHaveTextContent("Item do checklist: 2. Destinação de efluentes");
    expect(fotos[0]).toHaveTextContent("Data de captura: 21/10/2026 09:30");
    expect(fotos[1]).toHaveTextContent("Foto 2");
    expect(fotos[1]).toHaveTextContent("Sem vínculo");
    expect(fotos[1]).toHaveTextContent("Data de captura: Não informado");
    for (const f of fotos) expect(within(f).getByRole("img")).toHaveAttribute("src", expect.stringContaining("versao=original")); // nunca a miniatura
  });

  test("fotos agrupadas em pares (no máximo 2 por página na impressão)", async () => {
    instalarApi(comRelatorio());
    const { container } = renderizar("/inspecoes/4/relatorio");
    await screen.findAllByTestId("foto-relatorio");
    const pares = container.querySelectorAll(".par-fotos");
    expect(Array.from(pares).map((p) => p.querySelectorAll("figure").length)).toEqual([2, 1]);
  });

  test("sem fotos: mensagem e nenhuma figura", async () => {
    instalarApi(comRelatorio(comFotos(relatorio(), [])));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByText("Nenhuma foto anexada.")).toBeInTheDocument();
    expect(screen.queryByTestId("foto-relatorio")).not.toBeInTheDocument();
  });

  test("anotação com HTML aparece como texto nas fotos", async () => {
    const base = relatorio();
    instalarApi(comRelatorio(comFotos(base, [{ ...base.constatacoes.fotos[0], anotacao: "<img src=x onerror=alert(1)> literal" }])));
    const { container } = renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByText(/<img src=x onerror=alert\(1\)> literal/)).toBeInTheDocument();
    expect(container.querySelectorAll("figure img")).toHaveLength(1); // só a foto; nada injetado
  });

  test("6 providências: texto e atos, com 'nº a definir' quando não há número", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    const sec = (await screen.findByRole("region", { name: "6 – Providências tomadas" })) as HTMLElement;
    expect(sec).toHaveTextContent("Notificado o responsável.");
    const atos = within(screen.getByTestId("atos-relatorio")).getAllByRole("listitem").map((l) => l.textContent);
    expect(atos).toEqual(["Notificação – nº a definir", "Auto de Infração – nº AI-0001/2030"]);
  });

  test("6 providências vazias: aviso e nenhuma lista de atos", async () => {
    instalarApi(comRelatorio({ ...relatorio(), providencias: { texto: null, atos: [] } }));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("sem-providencias-texto")).toBeInTheDocument();
    expect(screen.queryByTestId("atos-relatorio")).not.toBeInTheDocument();
  });

  test("7 conclusão com o resultado e a regra", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("conclusao-resultado")).toHaveTextContent("Resultado: Reprovada");
    expect(screen.getByTestId("conclusao-regra")).toHaveTextContent("Regra aplicada: 1 item crítico não conforme");
  });
});

describe("Opção 'Incluir conclusão'", () => {
  test("vem ligada por padrão e a conclusão aparece", async () => {
    const chamadas = instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    const opcao = await screen.findByLabelText("Incluir conclusão");
    expect(opcao).toBeChecked();
    expect(screen.getByRole("region", { name: "7 – Conclusão" })).toBeInTheDocument();
    expect(chamadas.find((c) => c.caminho.endsWith("/relatorio"))!.consulta.has("incluir_conclusao")).toBe(false);
    expect(opcao.closest(".nao-imprimir")).not.toBeNull(); // o controle não vai para o papel
  });

  test("desligada, pede ao backend sem a conclusão e o item 7 some, sem recarregar as fotos", async () => {
    const base = relatorio();
    const chamadas = instalarApi(rota("GET", "/inspecoes/4/relatorio", (c) => ({
      corpo: c.consulta.get("incluir_conclusao") === "false" ? { ...base, conclusao: null } : base,
    })));
    renderizar("/inspecoes/4/relatorio");
    const opcao = await screen.findByLabelText("Incluir conclusão");
    const fotosAntes = screen.getAllByTestId("foto-relatorio");
    await userEvent.click(opcao);
    await waitFor(() => expect(screen.queryByRole("region", { name: "7 – Conclusão" })).not.toBeInTheDocument());
    expect(screen.queryByTestId("conclusao-resultado")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Incluir conclusão")).not.toBeChecked();
    expect(chamadas.filter((c) => c.caminho.endsWith("/relatorio")).at(-1)!.consulta.get("incluir_conclusao")).toBe("false");
    expect(screen.getAllByTestId("foto-relatorio")[0]).toBe(fotosAntes[0]); // o mesmo elemento: nada foi remontado
    await userEvent.click(screen.getByLabelText("Incluir conclusão")); // religa
    expect(await screen.findByRole("region", { name: "7 – Conclusão" })).toBeInTheDocument();
  });
});

describe("Relatório em prévia", () => {
  const previa = (): Relatorio => {
    const base = relatorio();
    return {
      ...base, previa: true, marca_dagua: "PRÉVIA, NÃO FINALIZADO",
      cabecalho: { ...base.cabecalho, ref_interna: null, linha: "Protocolo nº SEMA-PRO-2026/12345 | Inspeção INS-004 | Ref. interna: sem número (prévia)" },
      conclusao: { resultado: null, regra: "Resultado ainda não calculado: 2 itens não respondidos." },
    };
  };

  test("mostra a marca 'PRÉVIA, NÃO FINALIZADO' bem visível e a faixa de aviso", async () => {
    instalarApi(comRelatorio(previa()));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("marca-dagua")).toHaveTextContent("PRÉVIA, NÃO FINALIZADO");
    expect(screen.getByTestId("faixa-previa")).toHaveTextContent("PRÉVIA, NÃO FINALIZADO");
    expect(screen.getByTestId("faixa-previa")).toHaveTextContent("ainda não tem Ref. interna");
  });

  test("não mostra Ref. interna numerada em lugar nenhum", async () => {
    instalarApi(comRelatorio(previa()));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("cabecalho-relatorio")).toHaveTextContent("Ref. interna: sem número (prévia)");
    const texto = screen.getByTestId("relatorio").textContent ?? "";
    expect(texto).not.toMatch(/(^|\D)0\d{3}\/20\d{2}(\D|$)/); // nenhum número NNNN/AAAA
    expect(texto).toContain("SEMA-PRO-2026/12345"); // o protocolo continua aparecendo (é outra coisa)
    expect(screen.getByTestId("rodape-relatorio")).toHaveTextContent("Ref. interna: sem número (prévia) · INS-004");
  });

  test("conclusão sem resultado, com a regra da prévia", async () => {
    instalarApi(comRelatorio(previa()));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("conclusao-resultado")).toHaveTextContent("Ainda não calculado (prévia)");
    expect(screen.getByTestId("conclusao-regra")).toHaveTextContent("2 itens não respondidos");
  });

  test("inspeção cancelada mostra a marca de cancelada", async () => {
    instalarApi(comRelatorio({ ...previa(), marca_dagua: "CANCELADA, NÃO FINALIZADO" }));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("marca-dagua")).toHaveTextContent("CANCELADA, NÃO FINALIZADO");
  });
});

describe("Impressão e navegação", () => {
  test("botão Imprimir / Salvar PDF chama a impressão do navegador (sem fotos, já habilitado)", async () => {
    const imprimir = vi.spyOn(window, "print").mockImplementation(() => {});
    instalarApi(comRelatorio(comFotos(relatorio(), [])));
    renderizar("/inspecoes/4/relatorio");
    const botao = await screen.findByRole("button", { name: "Imprimir / Salvar PDF" });
    expect(botao).toBeEnabled();
    await userEvent.click(botao);
    expect(imprimir).toHaveBeenCalledTimes(1);
    imprimir.mockRestore();
  });

  test("com fotos, a impressão só é liberada depois de todas as imagens carregarem", async () => {
    const imprimir = vi.spyOn(window, "print").mockImplementation(() => {});
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    const botao = await screen.findByRole("button", { name: "Imprimir / Salvar PDF" });
    expect(botao).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent("Carregando imagens… 0/3");
    const imagens = screen.getAllByTestId("foto-relatorio").map((f) => within(f).getByRole("img"));
    imagens.slice(0, 2).forEach((i) => fireEvent.load(i));
    expect(botao).toBeDisabled();
    fireEvent.error(imagens[2]); // imagem que falhou não trava a impressão
    expect(botao).toBeEnabled();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    await userEvent.click(botao);
    expect(imprimir).toHaveBeenCalled();
    imprimir.mockRestore();
  });

  test("controles de tela ficam marcados para sumir na impressão", async () => {
    instalarApi(comRelatorio(comFotos(relatorio(), [])));
    renderizar("/inspecoes/4/relatorio");
    const botao = await screen.findByRole("button", { name: "Imprimir / Salvar PDF" });
    expect(botao.closest(".nao-imprimir")).not.toBeNull();
    expect(screen.getByRole("link", { name: "← Voltar à inspeção" }).closest(".nao-imprimir")).not.toBeNull();
    expect(screen.getByRole("link", { name: "← Voltar à inspeção" })).toHaveAttribute("href", "/inspecoes/4");
  });

  test("CSS de impressão: A4, esconde menu e botões, rodapé fixo, página X de Y e pares de fotos sem corte", () => {
    const css = readFileSync("src/estilos.css", "utf-8");
    expect(css).toMatch(/@page\s*{[^}]*size:\s*A4/);
    expect(css).toContain("counter(page)");
    expect(css).toContain("counter(pages)");
    expect(css).toMatch(/@media print[\s\S]*\.topo,\s*\.nao-imprimir\s*{\s*display:\s*none/);
    expect(css).not.toMatch(/\.rodape-relatorio\s*{[^}]*position:\s*fixed/); // fixed cobria o conteúdo no PDF
    expect(css).toMatch(/@media print[\s\S]*\.rodape-relatorio\s*{\s*display:\s*none/); // o rodapé impresso vem da caixa de margem
    expect(css).toMatch(/\.bloco-checklist\s*{[^}]*break-inside:\s*avoid/);
    expect(css).toMatch(/\.par-fotos\s*{[^}]*break-inside:\s*avoid/);
    expect(css).toMatch(/\.par-fotos \+ \.par-fotos\s*{[^}]*break-before:\s*page/);
  });

  test("rodapé de todas as páginas vem da regra @page (Ref. interna, INS e sistema fictício)", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    const regra = (await screen.findByTestId("regra-pagina")).textContent ?? "";
    expect(regra).toContain("@bottom-left");
    expect(regra).toContain("Ref. interna 0004/2026 · INS-004 · Sistema fictício/simulado");
    expect(regra).not.toContain("@top-center"); // finalizada: sem marca de prévia
  });

  test("prévia repete a marca no topo de todas as páginas e o rodapé diz 'sem número'", async () => {
    const base = relatorio();
    instalarApi(comRelatorio({ ...base, previa: true, marca_dagua: "PRÉVIA, NÃO FINALIZADO", cabecalho: { ...base.cabecalho, ref_interna: null } }));
    renderizar("/inspecoes/4/relatorio");
    const regra = (await screen.findByTestId("regra-pagina")).textContent ?? "";
    expect(regra).toContain('@top-center { content: "PRÉVIA, NÃO FINALIZADO"');
    expect(regra).toContain("Ref. interna: sem número (prévia) · INS-004");
    expect(regra).not.toMatch(/Ref\. interna\s*\d/);
  });

  test("aspas, barras e quebras de linha do texto são escapadas na regra @page", async () => {
    const base = relatorio();
    const codigo = 'INS-"4"\\x\ny'; // aspas, uma barra invertida e uma quebra de linha
    instalarApi(comRelatorio({ ...base, cabecalho: { ...base.cabecalho, codigo } }));
    renderizar("/inspecoes/4/relatorio");
    const regra = (await screen.findByTestId("regra-pagina")).textContent ?? "";
    expect(regra).toContain('INS-\\"4\\"\\\\x y'); // " -> \"   \ -> \\   quebra de linha -> espaço
    expect(regra.match(/content: "/g)).toHaveLength(1); // nada escapou da string
  });

  test("erro da API (404) aparece em vez do relatório", async () => {
    instalarApi(rota("GET", "/inspecoes/99/relatorio", erroApi(404, "NAO_ENCONTRADO", "Inspeção não encontrada.")));
    renderizar("/inspecoes/99/relatorio");
    expect(await screen.findByRole("alert")).toHaveTextContent("Inspeção não encontrada.");
  });
});

describe("Botão Gerar relatório no detalhe", () => {
  test.each(["ABERTA", "EM_ANDAMENTO", "FINALIZADA", "CANCELADA"])("existe quando a inspeção está %s", async (status) => {
    instalarApi(rota("GET", "/inspecoes/4", { corpo: inspecao({ status: status as any }) }));
    renderizar("/inspecoes/4");
    expect(await screen.findByRole("link", { name: "Gerar relatório" })).toHaveAttribute("href", "/inspecoes/4/relatorio");
  });

  test("finalizada mostra o número do relatório; as demais não", async () => {
    instalarApi(rota("GET", "/inspecoes/4", { corpo: inspecao({ status: "FINALIZADA", resultado: "APROVADA", numero_relatorio: "0007/2026" }) }));
    const { unmount } = renderizar("/inspecoes/4");
    expect(await screen.findByTestId("numero-relatorio")).toHaveTextContent("nº 0007/2026");
    unmount();
    instalarApi(rota("GET", "/inspecoes/4", { corpo: inspecao({ status: "EM_ANDAMENTO" }) }));
    renderizar("/inspecoes/4");
    await screen.findByRole("link", { name: "Gerar relatório" });
    expect(screen.queryByTestId("numero-relatorio")).not.toBeInTheDocument();
  });
});
