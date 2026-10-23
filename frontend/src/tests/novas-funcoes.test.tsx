import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { erroApi, inspecao, instalarApi, local, pagina, renderizar, resumo, rota } from "./ajuda";

const INDICADORES = { inspecoes: 5, pendencias: 2, finalizadas: 3, gerado_em: "x" };

describe("Painel: contadores clicáveis", () => {
  test("cada cartão é um link para a lista da própria categoria", async () => {
    instalarApi(rota("GET", "/indicadores", { corpo: INDICADORES }));
    renderizar("/");
    expect(await screen.findByTestId("indicador-inspecoes")).toHaveAttribute("href", "/inspecoes?status=ATIVAS");
    expect(screen.getByTestId("indicador-pendencias")).toHaveAttribute("href", "/inspecoes?status=PENDENTES");
    expect(screen.getByTestId("indicador-finalizadas")).toHaveAttribute("href", "/inspecoes?status=FINALIZADA");
    expect(screen.getByRole("link", { name: "Pendências: 2. Ver lista" })).toBeInTheDocument();
  });

  test.each([
    ["indicador-inspecoes", ["ABERTA", "EM_ANDAMENTO", "FINALIZADA"], "Todas, exceto canceladas"],
    ["indicador-pendencias", ["ABERTA", "EM_ANDAMENTO"], "Pendências"],
    ["indicador-finalizadas", ["FINALIZADA"], "Finalizada"],
  ])("clicar em %s lista a categoria certa", async (testid, statusEsperado, rotulo) => {
    const chamadas = instalarApi(
      rota("GET", "/indicadores", { corpo: INDICADORES }),
      rota("GET", "/inspecoes", pagina([resumo(1, { status: "FINALIZADA", resultado: "APROVADA" })])),
    );
    renderizar("/");
    await userEvent.click(await screen.findByTestId(testid));
    expect(await screen.findByRole("link", { name: "INS-001" })).toBeInTheDocument();
    const consulta = chamadas.filter((c) => c.caminho === "/inspecoes").at(-1)!;
    expect(consulta.consulta.getAll("status")).toEqual(statusEsperado);
    expect(screen.getByTestId("filtro-ativo")).toHaveTextContent(rotulo);
    expect(screen.getByLabelText("Filtrar por status")).toHaveValue(testid === "indicador-finalizadas" ? "FINALIZADA" : testid === "indicador-inspecoes" ? "ATIVAS" : "PENDENTES");
  });

  test("o contador do cartão coincide com o total listado ('Inspeções' exclui canceladas)", async () => {
    instalarApi(
      rota("GET", "/indicadores", { corpo: INDICADORES }),
      rota("GET", "/inspecoes", (c) => {
        const status = c.consulta.getAll("status");
        const todas = [resumo(1, { status: "FINALIZADA" }), resumo(2, { status: "ABERTA" }), resumo(3, { status: "CANCELADA" })];
        const dados = status.length ? todas.filter((r) => status.includes(r.status)) : todas;
        return { corpo: { dados, total: dados.length, pagina: 1, tamanho: 100 } };
      }),
    );
    renderizar("/");
    await userEvent.click(await screen.findByTestId("indicador-inspecoes"));
    await screen.findByRole("link", { name: "INS-001" });
    expect(screen.queryByRole("link", { name: "INS-003" })).not.toBeInTheDocument(); // cancelada fica de fora
    expect(screen.getByTestId("filtro-ativo")).toHaveTextContent("2 inspeção(ões)");
  });
});

describe("Lista: processo, busca e botão Editar", () => {
  test("busca por número envia numero_processo e mantém o filtro de status", async () => {
    const chamadas = instalarApi(rota("GET", "/inspecoes", pagina([resumo(1)])));
    renderizar("/inspecoes?status=FINALIZADA");
    await screen.findByRole("link", { name: "INS-001" });
    await userEvent.type(screen.getByLabelText("Buscar por número do processo"), "12345");
    await waitFor(() =>
      expect(chamadas.some((c) => c.consulta.get("numero_processo") === "12345" && c.consulta.getAll("status")[0] === "FINALIZADA")).toBe(true),
    );
  });

  test("botão Editar só aparece em inspeções editáveis e leva à página de edição", async () => {
    instalarApi(rota("GET", "/inspecoes", pagina([
      resumo(5, { status: "ABERTA" }), resumo(4, { status: "EM_ANDAMENTO" }),
      resumo(1, { status: "FINALIZADA" }), resumo(2, { status: "CANCELADA" }),
    ])));
    renderizar("/inspecoes");
    await screen.findByRole("link", { name: "INS-005" });
    expect(screen.getByRole("link", { name: "Editar INS-005" })).toHaveAttribute("href", "/inspecoes/5/editar");
    expect(screen.getByRole("link", { name: "Editar INS-004" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Editar INS-001" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Editar INS-002" })).not.toBeInTheDocument();
  });

  test("inspeção antiga sem número mostra traço", async () => {
    instalarApi(rota("GET", "/inspecoes", pagina([resumo(1, { numero_processo: null })])));
    renderizar("/inspecoes");
    const linha = (await screen.findByRole("link", { name: "INS-001" })).closest("tr")!;
    expect(within(linha).getAllByRole("cell")[1]).toHaveTextContent("—");
  });
});

describe("Editar inspeção", () => {
  const rotas = (status: any = "ABERTA", extra = {}) => [
    rota("GET", "/locais", pagina([local, { ...local, id: 2, nome: "Serraria Ipê Dourado" }])),
    rota("GET", "/inspecoes/4", () => ({ corpo: inspecao({ status, ...extra }) })),
  ];

  test("botão Editar no detalhe só aparece quando a API informa campos editáveis", async () => {
    instalarApi(...rotas("ABERTA"));
    const { unmount } = renderizar("/inspecoes/4");
    expect(await screen.findByRole("link", { name: "Editar inspeção" })).toHaveAttribute("href", "/inspecoes/4/editar");
    unmount();
    instalarApi(...rotas("FINALIZADA"));
    renderizar("/inspecoes/4");
    await screen.findByText("Somente leitura");
    expect(screen.queryByRole("link", { name: "Editar inspeção" })).not.toBeInTheDocument();
  });

  test("detalhe mostra o número do processo", async () => {
    instalarApi(...rotas("ABERTA"));
    renderizar("/inspecoes/4");
    expect(await screen.findByTestId("numero-processo")).toHaveTextContent("SEMA-PRO-2026/12345");
  });

  test("Aberta: todos os campos de cadastro editáveis; realização bloqueada", async () => {
    instalarApi(...rotas("ABERTA"));
    renderizar("/inspecoes/4/editar");
    expect(await screen.findByLabelText("Número do processo")).toHaveValue("SEMA-PRO-2026/12345");
    for (const nome of ["Local", "Data de agendamento", "Objetivo", "Observações", "Observações da vistoria"]) {
      expect(screen.getByLabelText(nome)).toBeEnabled();
    }
    expect(screen.queryByLabelText("Data de realização")).not.toBeInTheDocument(); // bloqueado: aparece só como texto
    expect(screen.getByTestId("leitura-data_realizacao")).toHaveTextContent("—");
  });

  test("Em andamento: agendamento, local e objetivo viram texto; processo e realização editáveis", async () => {
    instalarApi(...rotas("EM_ANDAMENTO", { data_realizacao: "2026-10-20" }));
    renderizar("/inspecoes/4/editar");
    expect(await screen.findByLabelText("Número do processo")).toBeInTheDocument();
    expect(screen.getByLabelText("Data de realização")).toHaveValue("2026-10-20");
    expect(screen.queryByLabelText("Data de agendamento")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Local")).not.toBeInTheDocument();
    expect(screen.getByTestId("leitura-data_agendamento")).toHaveTextContent("20/10/2026");
    expect(screen.getByTestId("leitura-local_id")).toHaveTextContent("Fazenda Horizonte Azul");
  });

  test("Finalizada: aviso, nada editável e salvar desabilitado", async () => {
    instalarApi(...rotas("FINALIZADA", { resultado: "APROVADA" }));
    renderizar("/inspecoes/4/editar");
    expect(await screen.findByRole("note")).toHaveTextContent("não pode mais ser editada");
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Salvar alterações" })).toBeDisabled();
  });

  test("salvar envia só o que mudou (PATCH) e volta ao detalhe", async () => {
    const chamadas = instalarApi(...rotas("ABERTA"), rota("PATCH", "/inspecoes/4", { corpo: inspecao() }));
    renderizar("/inspecoes/4/editar");
    const processo = await screen.findByLabelText("Número do processo");
    await userEvent.clear(processo);
    await userEvent.type(processo, "SEMA-PRO-2026/99999");
    await userEvent.selectOptions(screen.getByLabelText("Local"), "2");
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "PATCH")!.corpo).toEqual({ numero_processo: "SEMA-PRO-2026/99999", local_id: 2 }));
    expect(await screen.findByRole("heading", { name: "INS-004" })).toBeInTheDocument(); // voltou ao detalhe
  });

  test("sem alterações não chama a API", async () => {
    const chamadas = instalarApi(...rotas("ABERTA"));
    renderizar("/inspecoes/4/editar");
    await userEvent.click(await screen.findByRole("button", { name: "Salvar alterações" }));
    expect(screen.getByRole("status")).toHaveTextContent("Nenhuma alteração");
    expect(chamadas.some((c) => c.metodo === "PATCH")).toBe(false);
  });

  test("erro da API (422 e 409) aparece e a edição continua na tela", async () => {
    instalarApi(...rotas("ABERTA"), rota("PATCH", "/inspecoes/4", (c) =>
      c.corpo.numero_processo === "" ? erroApi(422, "VALIDACAO_CAMPO", "Dados inválidos.", [{ campo: "numero_processo", mensagem: "Campo obrigatório." }])
        : erroApi(409, "CAMPO_NAO_EDITAVEL_NO_STATUS", "Campos não editáveis na inspeção EM_ANDAMENTO: data_agendamento.")));
    renderizar("/inspecoes/4/editar");
    const processo = await screen.findByLabelText("Número do processo");
    await userEvent.clear(processo);
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Campo obrigatório.");
    await userEvent.type(processo, "X");
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Campos não editáveis"));
    expect(screen.getByLabelText("Número do processo")).toHaveValue("X"); // não perdeu o que foi digitado
  });

  test("404 da inspeção mostra o erro", async () => {
    instalarApi(rota("GET", "/inspecoes/4", erroApi(404, "NAO_ENCONTRADO", "Inspeção não encontrada.")), rota("GET", "/locais", pagina([local])));
    renderizar("/inspecoes/4/editar");
    expect(await screen.findByRole("alert")).toHaveTextContent("Inspeção não encontrada.");
  });
});

describe("Nova inspeção: novo local", () => {
  const preencherLocal = async (v: Record<string, string>) => {
    for (const [rotulo, valor] of Object.entries(v)) await userEvent.type(screen.getByLabelText(rotulo), valor);
  };

  test("lista vazia orienta e permite criar o primeiro local", async () => {
    let criado: any = null;
    const chamadas = instalarApi(
      rota("GET", "/locais", () => pagina(criado ? [criado] : [])),
      rota("POST", "/locais", (c) => { criado = { id: 7, ativo: true, ...c.corpo }; return { status: 201, corpo: criado }; }),
    );
    renderizar("/inspecoes/nova");
    expect(await screen.findByText(/Nenhum local cadastrado/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "+ Novo local" }));
    const dialogo = screen.getByRole("dialog", { name: "Novo local" });
    await preencherLocal({ "Nome do local": "Fazenda Nova", "Município do local": "Sinop", "Tipo do local": "Propriedade rural", "Latitude do local": "-11,85", "Longitude do local": "-55.5" });
    await userEvent.click(within(dialogo).getByRole("button", { name: "Salvar local" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(chamadas.find((c) => c.metodo === "POST")!.corpo).toEqual({ nome: "Fazenda Nova", municipio: "Sinop", tipo: "Propriedade rural", latitude: -11.85, longitude: -55.5, numero_car: null, proprietarios: [] }); // vírgula decimal aceita; CAR e proprietários vazios
    expect(screen.getByLabelText("Local")).toHaveValue("7"); // já selecionado
    expect(screen.getByLabelText("Latitude")).toHaveValue("-11.85");
    expect(screen.getByRole("option", { name: "Fazenda Nova — Sinop" })).toBeInTheDocument();
  });

  test("campos obrigatórios e números inválidos não chegam à API", async () => {
    const chamadas = instalarApi(rota("GET", "/locais", pagina([local])));
    renderizar("/inspecoes/nova");
    await userEvent.click(await screen.findByRole("button", { name: "+ Novo local" }));
    await userEvent.click(screen.getByRole("button", { name: "Salvar local" }));
    for (const t of ["Informe o nome.", "Informe o município.", "Informe o tipo."]) expect(screen.getByText(t)).toBeInTheDocument();
    expect(screen.getAllByText("Informe um número.")).toHaveLength(2);
    await preencherLocal({ "Latitude do local": "abc" });
    await userEvent.click(screen.getByRole("button", { name: "Salvar local" }));
    expect(chamadas.some((c) => c.metodo === "POST")).toBe(false);
  });

  test("coordenada fora de MT é recusada pela API e o modal permanece aberto", async () => {
    instalarApi(
      rota("GET", "/locais", pagina([local])),
      rota("POST", "/locais", erroApi(422, "COORDENADA_FORA_DE_MT", "Coordenada fora de Mato Grosso.", [{ campo: "latitude", mensagem: "Deve estar entre -18.05 e -7.35." }])),
    );
    renderizar("/inspecoes/nova");
    await userEvent.click(await screen.findByRole("button", { name: "+ Novo local" }));
    await preencherLocal({ "Nome do local": "Fora", "Município do local": "X", "Tipo do local": "Y", "Latitude do local": "-25", "Longitude do local": "-58" });
    await userEvent.click(screen.getByRole("button", { name: "Salvar local" }));
    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("Coordenada fora de Mato Grosso.");
    expect(alerta).toHaveTextContent("latitude");
    expect(screen.getByRole("dialog", { name: "Novo local" })).toBeInTheDocument();
    expect(screen.getByLabelText("Nome do local")).toHaveValue("Fora"); // não perde o que foi digitado
  });

  test("cancelar fecha o modal sem criar nada", async () => {
    const chamadas = instalarApi(rota("GET", "/locais", pagina([local])));
    renderizar("/inspecoes/nova");
    await userEvent.click(await screen.findByRole("button", { name: "+ Novo local" }));
    await userEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(chamadas.some((c) => c.metodo === "POST")).toBe(false);
  });

  test("fluxo completo: criar local, informar processo e cadastrar a inspeção com ele", async () => {
    let criado: any = null;
    const chamadas = instalarApi(
      rota("GET", "/locais", () => pagina(criado ? [criado] : [])),
      rota("POST", "/locais", (c) => { criado = { id: 9, ativo: true, ...c.corpo }; return { status: 201, corpo: criado }; }),
      rota("POST", "/inspecoes", { status: 201, corpo: inspecao({ id: 3, codigo: "INS-003" }) }),
      rota("GET", "/inspecoes/3", { corpo: inspecao({ id: 3, codigo: "INS-003" }) }),
    );
    renderizar("/inspecoes/nova");
    await userEvent.click(await screen.findByRole("button", { name: "+ Novo local" }));
    await preencherLocal({ "Nome do local": "Posto Novo", "Município do local": "Lucas", "Tipo do local": "Posto", "Latitude do local": "-13.05", "Longitude do local": "-55.9" });
    await userEvent.click(screen.getByRole("button", { name: "Salvar local" }));
    await waitFor(() => expect(screen.getByLabelText("Local")).toHaveValue("9"));
    await userEvent.type(screen.getByLabelText("Número do processo"), "SEMA-PRO-2026/12345");
    await userEvent.type(screen.getByLabelText("Data de agendamento"), "2026-10-30");
    await userEvent.type(screen.getByLabelText("Objetivo"), "Vistoria");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar inspeção" }));
    await screen.findByRole("heading", { name: "INS-003" });
    expect(chamadas.filter((c) => c.metodo === "POST" && c.caminho === "/inspecoes")[0].corpo).toEqual({
      numero_processo: "SEMA-PRO-2026/12345", local_id: 9, data_agendamento: "2026-10-30", objetivo: "Vistoria",
    });
  });
});
