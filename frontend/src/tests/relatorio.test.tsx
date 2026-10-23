import { fireEvent, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync } from "node:fs";
import { erroApi, inspecao, instalarApi, relatorio, renderizar, rota } from "./ajuda";

const comRelatorio = (r = relatorio()) => rota("GET", "/inspecoes/4/relatorio", () => ({ corpo: r }));

describe("Relatório finalizado", () => {
  test("mostra as 6 seções numeradas, na ordem", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    await screen.findByTestId("titulo-relatorio");
    const secoes = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(secoes).toEqual(["1. Identificação", "2. Empreendimento", "3. Objetivo e observações", "4. Checklist", "5. Registro fotográfico", "6. Conclusão"]);
  });

  test("título numerado, sem marca de prévia e com rodapé do número, da inspeção e do aviso de sistema fictício", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("titulo-relatorio")).toHaveTextContent("Relatório de Vistoria nº 0004/2026");
    expect(screen.queryByTestId("marca-dagua")).not.toBeInTheDocument();
    expect(screen.queryByTestId("faixa-previa")).not.toBeInTheDocument();
    expect(screen.getByTestId("rodape-relatorio")).toHaveTextContent("Relatório nº 0004/2026 · INS-004 · Sistema fictício/simulado");
    expect(screen.getByTestId("rel-numero")).toHaveTextContent("0004/2026");
  });

  test("identificação: processo, status, resultado, datas e conclusão com data e hora", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    const ident = (await screen.findByRole("region", { name: "1. Identificação" })) as HTMLElement;
    for (const t of ["INS-004", "SEMA-PRO-2026/12345", "Finalizada", "Reprovada", "20/10/2026", "21/10/2026"]) {
      expect(ident).toHaveTextContent(t);
    }
    expect(screen.getByTestId("rel-fechado-em")).toHaveTextContent("23/10/2026 17:05");
  });

  test("empreendimento: nome, município, tipo, coordenadas, CAR e proprietários com telefone", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    const emp = (await screen.findByRole("region", { name: "2. Empreendimento" })) as HTMLElement;
    for (const t of ["Fazenda Horizonte Azul", "Vila Nova do Cerrado", "Propriedade rural", "-10.42318, -58.71264"]) expect(emp).toHaveTextContent(t);
    expect(screen.getByTestId("rel-car")).toHaveTextContent("MT-5107925-00000000000000000000000000000001");
    expect(screen.getByTestId("rel-proprietarios")).toHaveTextContent("Proprietário Fictício Um — (65) 90000-0001");
  });

  test("CAR vazio e sem proprietários aparecem como 'Não informado'", async () => {
    const base = relatorio();
    instalarApi(comRelatorio(relatorio({ empreendimento: { ...base.empreendimento, numero_car: null, proprietarios: [] } })));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("rel-car")).toHaveTextContent("Não informado");
    expect(screen.getByTestId("rel-proprietarios")).toHaveTextContent("Não informado");
  });

  test("objetivo e observações em texto puro (HTML aparece literal)", async () => {
    const base = relatorio();
    instalarApi(comRelatorio(relatorio({ objetivo: { ...base.objetivo, observacoes_vistoria: "<script>alert(1)</script>\nlinha 2" } })));
    const { container } = renderizar("/inspecoes/4/relatorio");
    const sec = (await screen.findByRole("region", { name: "3. Objetivo e observações" })) as HTMLElement;
    expect(sec).toHaveTextContent("<script>alert(1)</script>");
    expect(sec).toHaveTextContent("Vistoria de rotina");
    expect(sec).toHaveTextContent("Observação geral");
    expect(container.querySelector("script")).toBeNull();
  });

  test("checklist numerado, crítico sim/não, situação, observação, totais e destaque do crítico não conforme", async () => {
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
    instalarApi(comRelatorio(relatorio({ checklist: { ...base.checklist, totais: { ...base.checklist.totais, respondidos: 3, nao_respondidos: 1 } } })));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("totais-checklist")).toHaveTextContent("1 não respondidos");
  });

  test("fotos numeradas com original, legenda, anotação, item vinculado, 'Sem vínculo' e data de captura", async () => {
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
    instalarApi(comRelatorio(relatorio({ fotos: [] })));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByText("Nenhuma foto anexada.")).toBeInTheDocument();
    expect(screen.queryByTestId("foto-relatorio")).not.toBeInTheDocument();
  });

  test("anotação com HTML aparece como texto nas fotos", async () => {
    const base = relatorio();
    const fotos = [{ ...base.fotos[0], anotacao: "<img src=x onerror=alert(1)> literal" }];
    instalarApi(comRelatorio(relatorio({ fotos })));
    const { container } = renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByText(/<img src=x onerror=alert\(1\)> literal/)).toBeInTheDocument();
    expect(container.querySelectorAll("figure img")).toHaveLength(1); // só a foto; nada injetado
  });

  test("conclusão com o resultado e a regra", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("conclusao-resultado")).toHaveTextContent("Resultado: Reprovada");
    expect(screen.getByTestId("conclusao-regra")).toHaveTextContent("Regra aplicada: 1 item crítico não conforme");
  });
});

describe("Relatório em prévia", () => {
  const previa = () =>
    relatorio({
      previa: true, marca_dagua: "PRÉVIA, NÃO FINALIZADO", numero_relatorio: null, titulo: "Relatório de Vistoria (sem número)",
      identificacao: { ...relatorio().identificacao, status: "EM_ANDAMENTO", resultado: null, fechado_em: null },
      conclusao: { resultado: null, regra: "Resultado ainda não calculado: 2 itens não respondidos." },
    });

  test("mostra a marca 'PRÉVIA, NÃO FINALIZADO' bem visível e a faixa de aviso", async () => {
    instalarApi(comRelatorio(previa()));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("marca-dagua")).toHaveTextContent("PRÉVIA, NÃO FINALIZADO");
    expect(screen.getByTestId("faixa-previa")).toHaveTextContent("PRÉVIA, NÃO FINALIZADO");
    expect(screen.getByTestId("faixa-previa")).toHaveTextContent("ainda não tem número");
  });

  test("não mostra número de relatório em lugar nenhum", async () => {
    instalarApi(comRelatorio(previa()));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("titulo-relatorio")).toHaveTextContent("Relatório de Vistoria (sem número)");
    expect(screen.getByTestId("rel-numero")).toHaveTextContent("— (prévia)");
    const texto = screen.getByTestId("relatorio").textContent ?? "";
    expect(texto).not.toMatch(/Relatório nº\s*\d/); // o rótulo "Relatório nº" existe, mas nunca seguido de um número
    expect(texto).not.toMatch(/(^|\D)0\d{3}\/20\d{2}(\D|$)/); // nenhum número NNNN/AAAA de relatório
    expect(texto).toContain("SEMA-PRO-2026/12345"); // o número do processo continua aparecendo (é outra coisa)
    expect(screen.getByTestId("rodape-relatorio")).toHaveTextContent("Relatório sem número (prévia) · INS-004");
    expect(screen.getByTestId("rel-fechado-em")).toHaveTextContent("—");
  });

  test("conclusão sem resultado, com a regra da prévia", async () => {
    instalarApi(comRelatorio(previa()));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("conclusao-resultado")).toHaveTextContent("Ainda não calculado (prévia)");
    expect(screen.getByTestId("conclusao-regra")).toHaveTextContent("2 itens não respondidos");
  });

  test("inspeção cancelada mostra a marca de cancelada", async () => {
    instalarApi(comRelatorio(relatorio({ previa: true, marca_dagua: "CANCELADA, NÃO FINALIZADO", numero_relatorio: null, titulo: "Relatório de Vistoria (sem número)" })));
    renderizar("/inspecoes/4/relatorio");
    expect(await screen.findByTestId("marca-dagua")).toHaveTextContent("CANCELADA, NÃO FINALIZADO");
  });
});

describe("Impressão e navegação", () => {
  test("botão Imprimir / Salvar PDF chama a impressão do navegador (sem fotos, já habilitado)", async () => {
    const imprimir = vi.spyOn(window, "print").mockImplementation(() => {});
    instalarApi(comRelatorio(relatorio({ fotos: [] })));
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
    instalarApi(comRelatorio(relatorio({ fotos: [] })));
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

  test("rodapé de todas as páginas vem da regra @page (nº do relatório, INS e sistema fictício)", async () => {
    instalarApi(comRelatorio());
    renderizar("/inspecoes/4/relatorio");
    const regra = (await screen.findByTestId("regra-pagina")).textContent ?? "";
    expect(regra).toContain("@bottom-left");
    expect(regra).toContain("Relatório nº 0004/2026 · INS-004 · Sistema fictício/simulado");
    expect(regra).not.toContain("@top-center"); // finalizada: sem marca de prévia
  });

  test("prévia repete a marca no topo de todas as páginas e o rodapé diz 'sem número'", async () => {
    instalarApi(comRelatorio(relatorio({ previa: true, marca_dagua: "PRÉVIA, NÃO FINALIZADO", numero_relatorio: null, titulo: "Relatório de Vistoria (sem número)" })));
    renderizar("/inspecoes/4/relatorio");
    const regra = (await screen.findByTestId("regra-pagina")).textContent ?? "";
    expect(regra).toContain('@top-center { content: "PRÉVIA, NÃO FINALIZADO"');
    expect(regra).toContain("Relatório sem número (prévia) · INS-004");
    expect(regra).not.toMatch(/Relatório nº\s*\d/);
  });

  test("aspas, barras e quebras de linha do texto são escapadas na regra @page", async () => {
    const base = relatorio();
    const codigo = 'INS-"4"\\x\ny'; // aspas, uma barra invertida e uma quebra de linha
    instalarApi(comRelatorio(relatorio({ identificacao: { ...base.identificacao, codigo } })));
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
