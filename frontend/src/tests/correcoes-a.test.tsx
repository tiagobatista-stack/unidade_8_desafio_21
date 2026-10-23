import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MSG_NAO_INICIADA, erroApi, foto, inspecao, instalarApi, item, local, pagina, renderizar, rota } from "./ajuda";

const AVISO_FUTURO =
  "Vistoria agendada para 30/10/2026. Para registrar o checklist antes dessa data, reagende em Editar inspeção.";
const detalhe = (extra = {}) => rota("GET", "/inspecoes/4", () => ({ corpo: inspecao(extra) }));

describe("A1: fechar inspeção Aberta", () => {
  test("botão desabilitado com a orientação ao lado, sem depender do erro da API", async () => {
    const chamadas = instalarApi(detalhe({ status: "ABERTA" }));
    renderizar("/inspecoes/4");
    const botao = await screen.findByRole("button", { name: "Fechar inspeção" });
    expect(botao).toBeDisabled();
    expect(screen.getByTestId("motivo-fechar")).toHaveTextContent(MSG_NAO_INICIADA);
    expect(botao).toHaveAccessibleDescription(MSG_NAO_INICIADA);
    await userEvent.click(botao);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(chamadas.some((c) => c.caminho.endsWith("/fechar"))).toBe(false);
  });

  test("em andamento o botão está habilitado e não há orientação", async () => {
    instalarApi(detalhe({ status: "EM_ANDAMENTO" }));
    renderizar("/inspecoes/4");
    expect(await screen.findByRole("button", { name: "Fechar inspeção" })).toBeEnabled();
    expect(screen.queryByTestId("motivo-fechar")).not.toBeInTheDocument();
  });

  test("se a API ainda assim recusar, a mensagem orientativa aparece", async () => {
    instalarApi(
      detalhe({ status: "EM_ANDAMENTO" }),
      rota("POST", "/inspecoes/4/fechar", erroApi(409, "TRANSICAO_INVALIDA", MSG_NAO_INICIADA)),
    );
    renderizar("/inspecoes/4");
    await userEvent.click(await screen.findByRole("button", { name: "Fechar inspeção" }));
    await userEvent.click(screen.getByRole("button", { name: "Confirmar fechamento" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Registre a situação de pelo menos um item");
  });
});

describe("A2: aviso de que só a situação inicia a inspeção", () => {
  test("aparece acima do checklist quando Aberta", async () => {
    instalarApi(detalhe({ status: "ABERTA" }));
    renderizar("/inspecoes/4");
    const aviso = await screen.findByTestId("aviso-inicio");
    expect(aviso).toHaveTextContent("A inspeção passa para Em andamento quando você registrar a situação do primeiro item.");
    expect(aviso).toHaveTextContent("Salvar só uma observação não inicia a inspeção.");
    const checklist = screen.getByRole("region", { name: /Checklist/ });
    const posAviso = aviso.compareDocumentPosition(screen.getAllByTestId(/^item-/)[0]);
    expect(checklist).toContainElement(aviso);
    expect(posAviso & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy(); // o aviso vem antes dos itens
  });

  test("não aparece em andamento nem finalizada", async () => {
    instalarApi(detalhe({ status: "EM_ANDAMENTO" }));
    const { unmount } = renderizar("/inspecoes/4");
    await screen.findByRole("button", { name: "Fechar inspeção" });
    expect(screen.queryByTestId("aviso-inicio")).not.toBeInTheDocument();
    unmount();
    instalarApi(detalhe({ status: "FINALIZADA", resultado: "APROVADA" }));
    renderizar("/inspecoes/4");
    await screen.findByText("Somente leitura");
    expect(screen.queryByTestId("aviso-inicio")).not.toBeInTheDocument();
  });
});

describe("A3: aviso preventivo de agendamento futuro", () => {
  const futuro = { status: "ABERTA" as const, data_agendamento: "2026-10-30", registro_bloqueado_motivo: AVISO_FUTURO };

  test("alerta com link para editar, antes de qualquer tentativa", async () => {
    const chamadas = instalarApi(detalhe(futuro));
    renderizar("/inspecoes/4");
    const alerta = await screen.findByTestId("aviso-agendamento-futuro");
    expect(alerta).toHaveTextContent("Vistoria agendada para 30/10/2026.");
    expect(within(alerta).getByRole("link", { name: "Editar inspeção" })).toHaveAttribute("href", "/inspecoes/4/editar");
    expect(chamadas.every((c) => c.metodo === "GET")).toBe(true); // nenhuma tentativa de gravação
  });

  test("seletores de Situação ficam desabilitados e a observação segue editável", async () => {
    instalarApi(detalhe({ ...futuro, itens: [item(1), item(2)] }));
    renderizar("/inspecoes/4");
    expect(await screen.findByLabelText("Situação de Item 1")).toBeDisabled();
    expect(screen.getByLabelText("Situação de Item 2")).toBeDisabled();
    expect(screen.getByLabelText("Observação de Item 1")).toBeEnabled();
  });

  test("sem agendamento futuro não há alerta e os seletores funcionam", async () => {
    instalarApi(detalhe({ status: "ABERTA", data_agendamento: "2026-10-20" }));
    renderizar("/inspecoes/4");
    expect(await screen.findByLabelText("Situação de Item 1")).toBeEnabled();
    expect(screen.queryByTestId("aviso-agendamento-futuro")).not.toBeInTheDocument();
  });

  test("o aviso some depois de reagendar (a API deixa de enviar o motivo)", async () => {
    let reagendada = false;
    instalarApi(
      rota("GET", "/inspecoes/4", () => ({ corpo: inspecao(reagendada ? { status: "ABERTA", data_agendamento: "2026-10-22" } : futuro) })),
      rota("GET", "/locais", pagina([local])),
      rota("PATCH", "/inspecoes/4", () => { reagendada = true; return { corpo: inspecao() }; }),
    );
    renderizar("/inspecoes/4");
    const links = await screen.findAllByRole("link", { name: "Editar inspeção" }); // alerta + barra de ações
    expect(links).toHaveLength(2);
    await userEvent.click(links[0]);
    const data = await screen.findByLabelText("Data de agendamento");
    await userEvent.clear(data);
    await userEvent.type(data, "2026-10-22");
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    await screen.findByRole("heading", { name: "INS-004" });
    await waitFor(() => expect(screen.queryByTestId("aviso-agendamento-futuro")).not.toBeInTheDocument());
    expect(screen.getByLabelText("Situação de Item 1")).toBeEnabled();
  });
});

describe("A5: rótulos das datas", () => {
  test("detalhe explica cada data e mostra quando o checklist foi concluído", async () => {
    instalarApi(detalhe({
      status: "FINALIZADA", resultado: "APROVADA", data_agendamento: "2026-10-20", data_realizacao: "2026-10-21",
      fechado_em: "2026-10-23T17:05:00",
    }));
    renderizar("/inspecoes/4");
    expect(await screen.findByText("Data de agendamento (planejada)")).toBeInTheDocument();
    expect(screen.getByText("Data de realização (vistoria em campo)").closest("div")).toHaveTextContent("21/10/2026");
    expect(screen.getByTestId("concluido-em")).toHaveTextContent("Checklist concluído em 23/10/2026 17:05");
  });

  test("não mostra 'concluído em' antes de finalizar", async () => {
    instalarApi(detalhe({ status: "EM_ANDAMENTO", fechado_em: null }));
    renderizar("/inspecoes/4");
    await screen.findByRole("button", { name: "Fechar inspeção" });
    expect(screen.queryByTestId("concluido-em")).not.toBeInTheDocument();
  });

  test("edição em andamento explica a data de realização; em aberta não há data de realização", async () => {
    const rotas = (status: any) => [detalhe({ status, data_realizacao: status === "EM_ANDAMENTO" ? "2026-10-20" : null }), rota("GET", "/locais", pagina([local]))];
    instalarApi(...rotas("EM_ANDAMENTO"));
    const { unmount } = renderizar("/inspecoes/4/editar");
    expect(await screen.findByTestId("ajuda-realizacao")).toHaveTextContent("futura nem anterior");
    expect(screen.getByLabelText("Data de realização")).toHaveValue("2026-10-20");
    unmount();
    instalarApi(...rotas("ABERTA"));
    renderizar("/inspecoes/4/editar");
    await screen.findByLabelText("Data de agendamento");
    expect(screen.queryByTestId("ajuda-realizacao")).not.toBeInTheDocument();
    expect(screen.getByText("Data de agendamento (planejada)")).toBeInTheDocument();
  });
});

// ---------- A4: id, name e label em todos os campos ----------
/** Todo input/select/textarea precisa de id, name, id único e um <label for> apontando para ele. */
function verificarCampos(origem: string) {
  const campos = Array.from(document.querySelectorAll<HTMLElement>("input, select, textarea"));
  expect(campos.length, `${origem}: nenhum campo encontrado`).toBeGreaterThan(0);
  const ids = new Set<string>();
  const problemas: string[] = [];
  for (const el of campos) {
    const nome = `${el.tagName.toLowerCase()}#${el.id || "(sem id)"}`;
    if (!el.id) problemas.push(`${nome} sem id`);
    if (!(el as HTMLInputElement).name) problemas.push(`${nome} sem name`);
    if (el.id && ids.has(el.id)) problemas.push(`${nome} id duplicado`);
    ids.add(el.id);
    if (el.id && !document.querySelector(`label[for="${CSS.escape(el.id)}"]`)) problemas.push(`${nome} sem label for`);
  }
  expect(problemas, `${origem}: ${problemas.join("; ")}`).toEqual([]);
}

describe("A4: campos de formulário com id, name e label", () => {
  const locais = rota("GET", "/locais", pagina([local]));

  test("Nova inspeção (e o modal Novo local)", async () => {
    instalarApi(locais);
    renderizar("/inspecoes/nova");
    await screen.findByLabelText("Número do processo");
    verificarCampos("Nova inspeção");
    await userEvent.click(screen.getByRole("button", { name: "+ Novo local" }));
    verificarCampos("Nova inspeção + modal Novo local");
  });

  test("Lista de inspeções (filtros)", async () => {
    instalarApi(rota("GET", "/inspecoes", pagina([])));
    renderizar("/inspecoes");
    await screen.findByLabelText("Filtrar por status");
    verificarCampos("Lista");
  });

  test.each(["ABERTA", "EM_ANDAMENTO"])("Editar inspeção (%s)", async (status) => {
    instalarApi(detalhe({ status, data_realizacao: status === "EM_ANDAMENTO" ? "2026-10-20" : null }), locais);
    renderizar("/inspecoes/4/editar");
    await screen.findByLabelText("Número do processo");
    verificarCampos(`Editar ${status}`);
  });

  test("Detalhe: checklist, item avulso, observações, fotos pendentes, visualizador e cancelamento", async () => {
    instalarApi(detalhe({
      status: "EM_ANDAMENTO", itens: [item(1), item(2, { origem: "AVULSO", modelo_item_id: null } as any)],
      fotos: [foto(1, { anotacao: "x" })],
    }));
    renderizar("/inspecoes/4");
    await screen.findByLabelText("Situação de Item 1");
    verificarCampos("Detalhe (checklist/avulso/observações)");
    expect(document.getElementById("item-1-situacao")).toBeTruthy(); // ids derivados do id do item
    expect(document.getElementById("item-2-observacao")).toBeTruthy();

    await userEvent.upload(screen.getByLabelText("Selecionar fotos"), [
      new File([new Uint8Array([1])], "a.jpg", { type: "image/jpeg" }),
      new File([new Uint8Array([2])], "b.jpg", { type: "image/jpeg" }),
    ]);
    await screen.findAllByTestId("foto-pendente");
    verificarCampos("Detalhe + fotos pendentes");

    await userEvent.click(screen.getByRole("button", { name: "Abrir foto 1" }));
    await userEvent.click(screen.getByRole("button", { name: "Editar" }));
    verificarCampos("Detalhe + visualizador em edição");
    await userEvent.click(screen.getByRole("button", { name: "Fechar" }));

    await userEvent.click(screen.getByRole("button", { name: "Cancelar inspeção" }));
    verificarCampos("Detalhe + modal cancelar");
  });

  test("os testes continuam achando os campos pelo label visível", async () => {
    instalarApi(locais);
    renderizar("/inspecoes/nova");
    await screen.findByLabelText("Número do processo");
    expect(screen.getByLabelText("Local")).toHaveAttribute("id", "nova-local");
    expect(screen.getByLabelText("Objetivo")).toHaveAttribute("name", "nova-objetivo");
  });
});
