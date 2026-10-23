import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { formatarData, rotuloResultado, somenteLeitura } from "../utils/formatar";
import { erroApi, inspecao, instalarApi, item, local, pagina, renderizar, resumo, rota } from "./ajuda";

describe("formatação", () => {
  test("datas em dd/mm/aaaa e vazio como traço", () => {
    expect(formatarData("2026-10-20")).toBe("20/10/2026");
    expect(formatarData(null)).toBe("—");
    expect(rotuloResultado(null)).toBe("—");
    expect(rotuloResultado("APROVADA_COM_RESSALVAS")).toBe("Aprovada com ressalvas");
    expect(somenteLeitura("FINALIZADA") && somenteLeitura("CANCELADA") && !somenteLeitura("ABERTA")).toBe(true);
  });
});

describe("Painel", () => {
  test("mostra os 3 indicadores e os atalhos", async () => {
    instalarApi(rota("GET", "/indicadores", { corpo: { inspecoes: 5, pendencias: 2, finalizadas: 3, gerado_em: "x" } }));
    renderizar("/");
    expect(await screen.findByTestId("indicador-inspecoes")).toHaveTextContent("5");
    expect(screen.getByTestId("indicador-pendencias")).toHaveTextContent("2");
    expect(screen.getByTestId("indicador-finalizadas")).toHaveTextContent("3");
    expect(screen.getByRole("link", { name: "Ver pendências" })).toHaveAttribute("href", "/inspecoes?status=PENDENTES");
    expect(screen.getByRole("link", { name: "Exportar CSV" })).toHaveAttribute("href", "/api/v1/exportacao/inspecoes.csv");
  });

  test("estado de carregamento e de erro", async () => {
    instalarApi(rota("GET", "/indicadores", erroApi(500, "ERRO_INTERNO", "Erro interno.")));
    renderizar("/");
    expect(screen.getByRole("status")).toHaveTextContent("Carregando");
    expect(await screen.findByRole("alert")).toHaveTextContent("Erro interno.");
  });

  test("carregar exemplos pede confirmação e trata 409", async () => {
    const chamadas = instalarApi(
      rota("GET", "/indicadores", { corpo: { inspecoes: 1, pendencias: 1, finalizadas: 0, gerado_em: "x" } }),
      rota("POST", "/utilitarios/carregar-exemplos", erroApi(409, "BANCO_JA_POVOADO", "O banco já contém dados; exemplos não foram carregados.")),
    );
    renderizar("/");
    await userEvent.click(await screen.findByRole("button", { name: "Carregar exemplos" }));
    expect(chamadas.some((c) => c.metodo === "POST")).toBe(false); // nada sem confirmar
    await userEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("O banco já contém dados");
  });

  test("exemplos carregados invalidam os indicadores", async () => {
    let carregado = false;
    instalarApi(
      rota("GET", "/indicadores", () => ({ corpo: carregado ? { inspecoes: 5, pendencias: 2, finalizadas: 3, gerado_em: "x" } : { inspecoes: 0, pendencias: 0, finalizadas: 0, gerado_em: "x" } })),
      rota("POST", "/utilitarios/carregar-exemplos", () => { carregado = true; return { status: 201, corpo: { locais: 4, inspecoes: 5, fotos: 9 } }; }),
    );
    renderizar("/");
    expect(await screen.findByTestId("indicador-inspecoes")).toHaveTextContent("0");
    await userEvent.click(screen.getByRole("button", { name: "Carregar exemplos" }));
    await userEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    await waitFor(() => expect(screen.getByTestId("indicador-inspecoes")).toHaveTextContent("5")); // sem recarregar a página
    expect(screen.getByRole("status")).toHaveTextContent("9 fotos fictícias");
  });
});

describe("Lista de inspeções", () => {
  test("linhas com datas formatadas, traço para vazio e fotos", async () => {
    instalarApi(
      rota("GET", "/inspecoes", pagina([
        resumo(2, { status: "FINALIZADA", resultado: "REPROVADA", data_realizacao: "2026-10-21", qtd_fotos: 2 }),
        resumo(5, { data_agendamento: "2026-10-28" }),
      ])),
    );
    renderizar("/inspecoes");
    const linha5 = (await screen.findByRole("link", { name: "INS-005" })).closest("tr")!;
    const c5 = within(linha5).getAllByRole("cell").map((c) => c.textContent);
    expect(c5).toEqual(["INS-005", "SEMA-PRO-2026/10005", "Fazenda Horizonte Azul", "28/10/2026", "—", "Aberta", "—", "0", "Editar"]);
    const c2 = within(screen.getByRole("link", { name: "INS-002" }).closest("tr")!).getAllByRole("cell").map((c) => c.textContent);
    expect(c2).toEqual(["INS-002", "SEMA-PRO-2026/10002", "Fazenda Horizonte Azul", "20/10/2026", "21/10/2026", "Finalizada", "Reprovada", "2", "—"]);
  });

  test("vazio e erro", async () => {
    instalarApi(rota("GET", "/inspecoes", pagina([])));
    const { unmount } = renderizar("/inspecoes");
    expect(await screen.findByText("Nenhuma inspeção encontrada.")).toBeInTheDocument();
    unmount();
    instalarApi(rota("GET", "/inspecoes", erroApi(422, "VALIDACAO_CAMPO", "Dados inválidos.", [{ campo: "data_inicio", mensagem: "Deve ser anterior ou igual a data_fim." }])));
    renderizar("/inspecoes");
    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("Dados inválidos.");
    expect(alerta).toHaveTextContent("data_inicio");
  });

  test("filtros de status e período vão para a API", async () => {
    const chamadas = instalarApi(rota("GET", "/inspecoes", pagina([resumo(1)])));
    renderizar("/inspecoes");
    await screen.findByRole("link", { name: "INS-001" });
    await userEvent.selectOptions(screen.getByLabelText("Filtrar por status"), "FINALIZADA");
    await waitFor(() => expect(chamadas.some((c) => c.consulta.get("status") === "FINALIZADA")).toBe(true));
    await userEvent.type(screen.getByLabelText("Data inicial"), "2026-10-13");
    await userEvent.type(screen.getByLabelText("Data final"), "2026-10-20");
    await waitFor(() =>
      expect(chamadas.some((c) => c.consulta.get("data_inicio") === "2026-10-13" && c.consulta.get("data_fim") === "2026-10-20" && c.consulta.get("status") === "FINALIZADA")).toBe(true),
    );
  });

  test("pendências: uma única consulta com status repetido (ordem e paginação vêm da API)", async () => {
    const chamadas = instalarApi(rota("GET", "/inspecoes", pagina([resumo(5), resumo(4, { status: "EM_ANDAMENTO" })])));
    renderizar("/inspecoes?status=PENDENTES");
    await screen.findByRole("link", { name: "INS-004" });
    const consultas = chamadas.filter((c) => c.caminho === "/inspecoes");
    expect(consultas).toHaveLength(1);
    expect(consultas[0].consulta.getAll("status")).toEqual(["ABERTA", "EM_ANDAMENTO"]);
  });
});

describe("Nova inspeção", () => {
  const rotas = () => [
    rota("GET", "/locais", pagina([local, { ...local, id: 2, nome: "Serraria Ipê Dourado", latitude: -11.21456, longitude: -58.30977 }])),
  ];

  test("obrigatórios: não envia e mostra os avisos", async () => {
    const chamadas = instalarApi(...rotas());
    renderizar("/inspecoes/nova");
    await userEvent.click(await screen.findByRole("button", { name: "Cadastrar inspeção" }));
    expect(screen.getByText("Selecione um local.")).toBeInTheDocument();
    expect(screen.getByText("Informe a data de agendamento.")).toBeInTheDocument();
    expect(screen.getByText("Informe o objetivo.")).toBeInTheDocument();
    expect(screen.getByText("Informe o número do processo.")).toBeInTheDocument();
    expect(chamadas.some((c) => c.metodo === "POST")).toBe(false);
  });

  test("local mostra latitude/longitude somente leitura e envia o payload", async () => {
    const chamadas = instalarApi(
      ...rotas(),
      rota("POST", "/inspecoes", { status: 201, corpo: inspecao({ id: 9, codigo: "INS-009" }) }),
      rota("GET", "/inspecoes/9", { corpo: inspecao({ id: 9, codigo: "INS-009" }) }),
    );
    renderizar("/inspecoes/nova");
    await screen.findByRole("option", { name: /Serraria/ });
    await userEvent.selectOptions(screen.getByLabelText("Local"), "2");
    expect(screen.getByLabelText("Latitude")).toHaveValue("-11.21456");
    expect(screen.getByLabelText("Longitude")).toHaveAttribute("readonly");
    await userEvent.type(screen.getByLabelText("Número do processo"), "SEMA-PRO-2026/12345");
    await userEvent.type(screen.getByLabelText("Data de agendamento"), "2026-10-28"); // agendamento futuro aceito
    await userEvent.type(screen.getByLabelText("Objetivo"), "Vistoria de rotina");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar inspeção" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "INS-009" })).toBeInTheDocument());
    const post = chamadas.find((c) => c.metodo === "POST")!;
    expect(post.corpo).toEqual({ numero_processo: "SEMA-PRO-2026/12345", local_id: 2, data_agendamento: "2026-10-28", objetivo: "Vistoria de rotina" });
  });

  test("erro da API aparece com mensagem e detalhes", async () => {
    instalarApi(...rotas(), rota("POST", "/inspecoes", erroApi(422, "VALIDACAO_CAMPO", "Dados inválidos.", [{ campo: "objetivo", mensagem: "Máximo de 200 caracteres." }])));
    renderizar("/inspecoes/nova");
    await screen.findByRole("option", { name: /Fazenda/ });
    await userEvent.selectOptions(screen.getByLabelText("Local"), "1");
    await userEvent.type(screen.getByLabelText("Número do processo"), "SEMA-PRO-2026/12345");
    await userEvent.type(screen.getByLabelText("Data de agendamento"), "2026-10-20");
    await userEvent.type(screen.getByLabelText("Objetivo"), "x");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar inspeção" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Máximo de 200 caracteres.");
  });
});

describe("Detalhe e checklist", () => {
  test("cabeçalho com status, duas datas e local; traço quando vazio", async () => {
    instalarApi(rota("GET", "/inspecoes/4", { corpo: inspecao({ status: "ABERTA" }) }));
    renderizar("/inspecoes/4");
    expect(await screen.findByRole("heading", { name: "INS-004" })).toBeInTheDocument();
    const dados = screen.getByText("Data de agendamento (planejada)").closest("div")!;
    expect(dados).toHaveTextContent("20/10/2026");
    expect(screen.getByText("Data de realização (vistoria em campo)").closest("div")).toHaveTextContent("—");
    expect(screen.getByText("Resultado").closest("div")).toHaveTextContent("—");
    expect(screen.getByText(/-10.42318, -58.71264/)).toBeInTheDocument();
    expect(screen.getAllByTestId(/^item-/)).toHaveLength(3);
  });

  test("registrar situação envia PATCH e recarrega", async () => {
    let situacao = "NAO_RESPONDIDO";
    const chamadas = instalarApi(
      rota("GET", "/inspecoes/4", () => ({ corpo: inspecao({ itens: [item(1, { situacao: situacao as any }), item(2)] }) })),
      rota("PATCH", "/inspecoes/4/itens/1", (c) => { situacao = c.corpo.situacao; return { corpo: item(1, { situacao: situacao as any }) }; }),
    );
    renderizar("/inspecoes/4");
    await userEvent.selectOptions(await screen.findByLabelText("Situação de Item 1"), "CONFORME");
    await waitFor(() => expect(screen.getByLabelText("Situação de Item 1")).toHaveValue("CONFORME"));
    expect(chamadas.find((c) => c.metodo === "PATCH")!.corpo).toEqual({ situacao: "CONFORME" });
  });

  test("P1: mensagem da API aparece ao registrar item de vistoria agendada para o futuro", async () => {
    instalarApi(
      rota("GET", "/inspecoes/5", { corpo: inspecao({ id: 5, codigo: "INS-005", data_agendamento: "2026-10-28" }) }),
      rota("PATCH", "/inspecoes/5/itens/1", erroApi(422, "DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO", "Vistoria agendada para 28/10/2026; reagende (inspeção Aberta) ou aguarde.")),
    );
    renderizar("/inspecoes/5");
    await userEvent.selectOptions(await screen.findByLabelText("Situação de Item 1"), "CONFORME");
    expect(await screen.findByRole("alert")).toHaveTextContent("Vistoria agendada para 28/10/2026");
  });

  test("fechamento bloqueado destaca os itens citados", async () => {
    instalarApi(
      rota("GET", "/inspecoes/4", { corpo: inspecao({ status: "EM_ANDAMENTO", itens: [item(1, { situacao: "CONFORME" }), item(2), item(3, { situacao: "NAO_CONFORME" })] }) }),
      rota("POST", "/inspecoes/4/fechar", erroApi(422, "FECHAMENTO_BLOQUEADO", "Há itens pendentes que impedem o fechamento.", [
        { campo: "itens.2", mensagem: "Item não respondido: Item 2" },
        { campo: "itens.3", mensagem: "Item não conforme exige observação: Item 3" },
      ])),
    );
    renderizar("/inspecoes/4");
    await userEvent.click(await screen.findByRole("button", { name: "Fechar inspeção" }));
    await userEvent.click(screen.getByRole("button", { name: "Confirmar fechamento" }));
    await waitFor(() => expect(screen.getByTestId("item-2")).toHaveClass("item-destacado"));
    expect(screen.getByTestId("item-3")).toHaveClass("item-destacado");
    expect(screen.getByTestId("item-1")).not.toHaveClass("item-destacado");
    expect(within(screen.getByTestId("item-2")).getByRole("note")).toHaveTextContent("Item não respondido");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  test("modal Fechar: resumo, fotos anexadas e aviso não bloqueante de NC sem foto", async () => {
    instalarApi(rota("GET", "/inspecoes/4", { corpo: inspecao({
      status: "EM_ANDAMENTO", observacoes_vistoria: "Resumo da vistoria.",
      itens: [item(1, { situacao: "NAO_CONFORME", qtd_fotos: 0 }), item(2, { situacao: "NAO_CONFORME", qtd_fotos: 1 })],
      fotos: [{ ...(await import("./ajuda")).foto(1), item_id: 2 }],
    }) }));
    renderizar("/inspecoes/4");
    await userEvent.click(await screen.findByRole("button", { name: "Fechar inspeção" }));
    const modal = screen.getByRole("dialog");
    expect(modal).toHaveTextContent("Resumo da vistoria.");
    expect(modal).toHaveTextContent("Fotos anexadas: 1");
    expect(within(modal).getByRole("note")).toHaveTextContent("Item 1");
    expect(within(modal).getByRole("note")).not.toHaveTextContent("Item 2");
    expect(within(modal).getByRole("button", { name: "Confirmar fechamento" })).toBeEnabled();
  });

  test("fechar com sucesso atualiza para somente leitura", async () => {
    let fechada = false;
    instalarApi(
      rota("GET", "/inspecoes/4", () => ({ corpo: fechada ? inspecao({ status: "FINALIZADA", resultado: "APROVADA", itens: [item(1, { situacao: "CONFORME" })] }) : inspecao({ status: "EM_ANDAMENTO", itens: [item(1, { situacao: "CONFORME" })] }) })),
      rota("POST", "/inspecoes/4/fechar", () => { fechada = true; return { corpo: {} }; }),
    );
    renderizar("/inspecoes/4");
    await userEvent.click(await screen.findByRole("button", { name: "Fechar inspeção" }));
    await userEvent.click(screen.getByRole("button", { name: "Confirmar fechamento" }));
    await waitFor(() => expect(screen.getByText("Somente leitura")).toBeInTheDocument());
    expect(screen.getByText("Resultado").closest("div")).toHaveTextContent("Aprovada");
    expect(screen.queryByRole("button", { name: "Fechar inspeção" })).not.toBeInTheDocument();
  });

  test("cancelar exige motivo e envia", async () => {
    const chamadas = instalarApi(
      rota("GET", "/inspecoes/5", { corpo: inspecao({ id: 5, codigo: "INS-005" }) }),
      rota("POST", "/inspecoes/5/cancelar", { corpo: {} }),
    );
    renderizar("/inspecoes/5");
    await userEvent.click(await screen.findByRole("button", { name: "Cancelar inspeção" }));
    const confirmar = screen.getByRole("button", { name: "Confirmar cancelamento" });
    expect(confirmar).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Motivo do cancelamento"), "Local inacessível");
    await userEvent.click(confirmar);
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "POST")!.corpo).toEqual({ motivo: "Local inacessível" }));
  });

  test("somente leitura em FINALIZADA: sem botões de edição, upload ou campos", async () => {
    instalarApi(rota("GET", "/inspecoes/1", { corpo: inspecao({
      id: 1, codigo: "INS-001", status: "FINALIZADA", resultado: "REPROVADA", observacoes_vistoria: "Texto final",
      itens: [item(1, { situacao: "NAO_CONFORME", observacao: "Obs do item" })],
    }) }));
    renderizar("/inspecoes/1");
    await screen.findByText("Somente leitura");
    expect(screen.queryByRole("button", { name: /Fechar inspeção|Cancelar inspeção|Adicionar item|Salvar/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Selecionar fotos")).not.toBeInTheDocument();
    expect(screen.getByText("Texto final")).toBeInTheDocument();
    expect(screen.getByText("Obs do item")).toBeInTheDocument();
  });

  test("CANCELADA mostra o motivo e fica somente leitura", async () => {
    instalarApi(rota("GET", "/inspecoes/5", { corpo: inspecao({ id: 5, status: "CANCELADA", motivo_cancelamento: "Sem acesso" }) }));
    renderizar("/inspecoes/5");
    expect(await screen.findByText("Sem acesso")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Fechar inspeção" })).not.toBeInTheDocument();
  });

  test("404 do detalhe mostra o erro", async () => {
    instalarApi(rota("GET", "/inspecoes/99", erroApi(404, "NAO_ENCONTRADO", "Inspeção não encontrada.")));
    renderizar("/inspecoes/99");
    expect(await screen.findByRole("alert")).toHaveTextContent("Inspeção não encontrada.");
  });
});

describe("URLs da API", () => {
  test("urlApi mantém caminhos relativos na mesma origem e preserva URLs absolutas", async () => {
    const { urlApi } = await import("../api/cliente");
    expect(urlApi("/api/v1/x")).toBe("/api/v1/x"); // sem VITE_API_URL
    expect(urlApi("https://exemplo.test/a.png")).toBe("https://exemplo.test/a.png");
  });
});
