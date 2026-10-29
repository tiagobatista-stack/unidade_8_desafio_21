import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { empreendimentoDe, erroApi, inspecao, instalarApi, local, pagina, renderizar, rota } from "./ajuda";
import type { Local } from "../api/tipos";

const CAR_FICTICIO = "MT-5107925-00000000000000000000000000000001";
const fazenda: Local = {
  ...local, id: 1, numero_car: CAR_FICTICIO,
  proprietarios: [
    { nome: "Proprietário Fictício Um", telefone: "65900000001", telefone_formatado: "(65) 90000-0001" },
    { nome: "Proprietária Fictícia Dois", telefone: null, telefone_formatado: null },
  ],
};
const serraria: Local = { ...local, id: 2, nome: "Serraria Fictícia", municipio: "Cidade Fictícia", tipo: "Indústria", numero_car: null, proprietarios: [] };

describe("Tela Locais (lista)", () => {
  test("lista com CAR, proprietários com telefone formatado e traço quando não há", async () => {
    instalarApi(rota("GET", "/locais", pagina([fazenda, serraria])));
    renderizar("/locais");
    const linhaFazenda = (await screen.findByText("Fazenda Horizonte Azul")).closest("tr")!;
    expect(linhaFazenda).toHaveTextContent(CAR_FICTICIO);
    expect(linhaFazenda).toHaveTextContent("Proprietário Fictício Um — (65) 90000-0001");
    expect(linhaFazenda).toHaveTextContent("Proprietária Fictícia Dois");
    const colunas = within(screen.getByText("Serraria Fictícia").closest("tr")!).getAllByRole("cell").map((c) => c.textContent);
    expect(colunas.slice(3, 5)).toEqual(["—", "—"]); // sem CAR e sem proprietários
    expect(screen.getByRole("link", { name: "Editar Serraria Fictícia" })).toHaveAttribute("href", "/locais/2/editar");
    expect(screen.getByRole("link", { name: "Novo local" })).toHaveAttribute("href", "/locais/novo");
  });

  test("menu tem o link Locais; estados vazio e erro", async () => {
    instalarApi(rota("GET", "/locais", pagina([])));
    const { unmount } = renderizar("/locais");
    expect(await screen.findByText(/Nenhum local cadastrado/)).toBeInTheDocument();
    expect(within(screen.getByRole("navigation", { name: "Principal" })).getByRole("link", { name: "Locais" })).toHaveAttribute("href", "/locais");
    unmount();
    instalarApi(rota("GET", "/locais", erroApi(500, "ERRO_INTERNO", "Erro interno.")));
    renderizar("/locais");
    expect(await screen.findByRole("alert")).toHaveTextContent("Erro interno.");
  });
});

describe("Cadastrar local", () => {
  const preencherBasico = async () => {
    await userEvent.type(screen.getByLabelText("Nome do local"), "Fazenda Nova Fictícia");
    await userEvent.type(screen.getByLabelText("Município do local"), "Cidade Fictícia");
    await userEvent.type(screen.getByLabelText("Tipo do local"), "Propriedade rural");
    await userEvent.type(screen.getByLabelText("Latitude do local"), "-12,5");
    await userEvent.type(screen.getByLabelText("Longitude do local"), "-55.5");
  };

  test("campos obrigatórios impedem o envio", async () => {
    const chamadas = instalarApi();
    renderizar("/locais/novo");
    await userEvent.click(await screen.findByRole("button", { name: "Cadastrar local" }));
    for (const t of ["Informe o nome.", "Informe o município.", "Informe o tipo."]) expect(screen.getByText(t)).toBeInTheDocument();
    expect(screen.getAllByText("Informe um número.")).toHaveLength(2);
    expect(chamadas.some((c) => c.metodo === "POST")).toBe(false);
  });

  test("CAR, adicionar e remover proprietários, telefone formatado ao sair do campo e payload enviado", async () => {
    const chamadas = instalarApi(
      rota("GET", "/locais", pagina([])),
      rota("POST", "/locais", (c) => ({ status: 201, corpo: { id: 9, ativo: true, ...c.corpo } })),
    );
    renderizar("/locais/novo");
    await screen.findByLabelText("Nome do local");
    await preencherBasico();
    await userEvent.type(screen.getByLabelText("Número do CAR"), "  mt-5107925-abc  ");
    expect(screen.queryByTestId("aviso-car")).not.toBeInTheDocument(); // já segue UF-código IBGE-código: sem aviso
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar proprietário" }));
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar proprietário" }));
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar proprietário" }));
    expect(screen.getAllByTestId("linha-proprietario")).toHaveLength(3);
    await userEvent.type(screen.getByLabelText("Nome do proprietário 1"), "Fulano Fictício");
    await userEvent.type(screen.getByLabelText("Telefone do proprietário 1"), "65900000001");
    await userEvent.tab(); // sai do campo
    expect(screen.getByLabelText("Telefone do proprietário 1")).toHaveValue("(65) 90000-0001");
    await userEvent.type(screen.getByLabelText("Nome do proprietário 2"), "Beltrana Fictícia");
    await userEvent.click(screen.getByRole("button", { name: "Remover proprietário 3" })); // linha vazia
    expect(screen.getAllByTestId("linha-proprietario")).toHaveLength(2);
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar local" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "POST")).toBeTruthy());
    expect(chamadas.find((c) => c.metodo === "POST")!.corpo).toEqual({
      nome: "Fazenda Nova Fictícia", municipio: "Cidade Fictícia", tipo: "Propriedade rural", latitude: -12.5, longitude: -55.5, uf: "MT",
      numero_car: "mt-5107925-abc",
      proprietarios: [{ nome: "Fulano Fictício", telefone: "(65) 90000-0001" }, { nome: "Beltrana Fictícia", telefone: null }],
    });
    expect(await screen.findByRole("heading", { name: "Locais" })).toBeInTheDocument(); // volta à lista
  });

  test("aviso suave quando o CAR foge do modelo SICAR e some quando segue o modelo", async () => {
    instalarApi();
    renderizar("/locais/novo");
    const car = await screen.findByLabelText("Número do CAR");
    expect(screen.queryByTestId("aviso-car")).not.toBeInTheDocument(); // vazio: sem aviso
    await userEvent.type(car, "MT-123456/2020");
    expect(screen.getByTestId("aviso-car")).toHaveTextContent("Será aceito mesmo assim");
    await userEvent.clear(car);
    await userEvent.type(car, CAR_FICTICIO);
    expect(screen.queryByTestId("aviso-car")).not.toBeInTheDocument();
  });

  test("proprietário com telefone mas sem nome não é enviado", async () => {
    const chamadas = instalarApi();
    renderizar("/locais/novo");
    await screen.findByLabelText("Nome do local");
    await preencherBasico();
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar proprietário" }));
    await userEvent.type(screen.getByLabelText("Telefone do proprietário 1"), "65900000001");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar local" }));
    expect(screen.getByText("Informe o nome.")).toBeInTheDocument();
    expect(chamadas.some((c) => c.metodo === "POST")).toBe(false);
  });

  test("erro da API (telefone inválido) aparece e o formulário mantém o que foi digitado", async () => {
    instalarApi(rota("POST", "/locais", erroApi(422, "VALIDACAO_CAMPO", "Dados inválidos.", [
      { campo: "proprietarios.0.telefone", mensagem: "Informe o telefone com DDD (10 ou 11 dígitos)." }])));
    renderizar("/locais/novo");
    await screen.findByLabelText("Nome do local");
    await preencherBasico();
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar proprietário" }));
    await userEvent.type(screen.getByLabelText("Nome do proprietário 1"), "Fulano Fictício");
    await userEvent.type(screen.getByLabelText("Telefone do proprietário 1"), "123");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar local" }));
    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("proprietarios.0.telefone");
    expect(alerta).toHaveTextContent("10 ou 11 dígitos");
    expect(screen.getByLabelText("Nome do proprietário 1")).toHaveValue("Fulano Fictício");
    expect(screen.getByLabelText("Nome do local")).toHaveValue("Fazenda Nova Fictícia");
  });

  test("cancelar volta para a lista sem gravar", async () => {
    const chamadas = instalarApi(rota("GET", "/locais", pagina([])));
    renderizar("/locais/novo");
    await userEvent.click(await screen.findByRole("button", { name: "Cancelar" }));
    expect(await screen.findByRole("heading", { name: "Locais" })).toBeInTheDocument();
    expect(chamadas.some((c) => c.metodo === "POST" || c.metodo === "PUT")).toBe(false);
  });
});

describe("Editar local", () => {
  test("carrega CAR e proprietários (telefone formatado) e envia PUT com a lista alterada", async () => {
    const chamadas = instalarApi(
      rota("GET", "/locais/1", { corpo: fazenda }),
      rota("GET", "/locais", pagina([fazenda])),
      rota("PUT", "/locais/1", { corpo: fazenda }),
    );
    renderizar("/locais/1/editar");
    expect(await screen.findByLabelText("Nome do local")).toHaveValue("Fazenda Horizonte Azul");
    expect(screen.getByLabelText("Número do CAR")).toHaveValue(CAR_FICTICIO);
    expect(screen.getByLabelText("Telefone do proprietário 1")).toHaveValue("(65) 90000-0001");
    expect(screen.getAllByTestId("linha-proprietario")).toHaveLength(2);

    await userEvent.click(screen.getByRole("button", { name: "Remover proprietário 1" })); // a lista vira só a "Dois"
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar proprietário" }));
    await userEvent.type(screen.getByLabelText("Nome do proprietário 2"), "Novo Proprietário Fictício");
    await userEvent.type(screen.getByLabelText("Telefone do proprietário 2"), "6533334444");
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "PUT")).toBeTruthy());
    const corpo = chamadas.find((c) => c.metodo === "PUT")!.corpo;
    expect(corpo.proprietarios).toEqual([{ nome: "Proprietária Fictícia Dois", telefone: null }, { nome: "Novo Proprietário Fictício", telefone: "(65) 3333-4444" }]);
    expect(corpo.numero_car).toBe(CAR_FICTICIO);
  });

  test("limpar o CAR envia nulo; local inexistente mostra o erro", async () => {
    const chamadas = instalarApi(rota("GET", "/locais/1", { corpo: fazenda }), rota("GET", "/locais", pagina([])), rota("PUT", "/locais/1", { corpo: fazenda }));
    const { unmount } = renderizar("/locais/1/editar");
    await userEvent.clear(await screen.findByLabelText("Número do CAR"));
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "PUT")!.corpo.numero_car).toBeNull());
    unmount();
    instalarApi(rota("GET", "/locais/99", erroApi(404, "NAO_ENCONTRADO", "Local não encontrado.")));
    renderizar("/locais/99/editar");
    expect(await screen.findByRole("alert")).toHaveTextContent("Local não encontrado.");
  });
});

describe("Detalhe da inspeção: Empreendimento", () => {
  const detalhe = (extra = {}) => rota("GET", "/inspecoes/4", () => ({ corpo: inspecao({ status: "EM_ANDAMENTO", ...extra }) }));

  test("mostra nome, tipo, coordenadas, CAR e proprietários com telefone formatado", async () => {
    instalarApi(detalhe({ empreendimento: empreendimentoDe(fazenda) }));
    renderizar("/inspecoes/4");
    const cartao = await screen.findByTestId("empreendimento");
    expect(cartao).toHaveTextContent("Fazenda Horizonte Azul — Vila Nova do Cerrado");
    expect(cartao).toHaveTextContent("Propriedade rural");
    expect(cartao).toHaveTextContent("-10.42318, -58.71264");
    expect(screen.getByTestId("numero-car")).toHaveTextContent(CAR_FICTICIO);
    expect(screen.getByTestId("proprietarios")).toHaveTextContent("Proprietário Fictício Um — (65) 90000-0001");
    expect(screen.getByTestId("proprietarios")).toHaveTextContent("Proprietária Fictícia Dois");
  });

  test("CAR vazio aparece como 'Não informado'; sem proprietários também", async () => {
    instalarApi(detalhe({ empreendimento: empreendimentoDe(serraria) }));
    renderizar("/inspecoes/4");
    expect(await screen.findByTestId("numero-car")).toHaveTextContent("Não informado");
    expect(screen.getByTestId("proprietarios")).toHaveTextContent("Não informado");
  });
});


describe("Detalhe da inspeção: origem dos dados do empreendimento (C2)", () => {
  const com = (status: any, extra = {}) =>
    rota("GET", "/inspecoes/4", () => ({ corpo: inspecao({ status, empreendimento: empreendimentoDe(fazenda), ...extra }) }));

  test("finalizada informa que é a cópia do fechamento", async () => {
    instalarApi(com("FINALIZADA", { resultado: "APROVADA" }));
    renderizar("/inspecoes/4");
    expect(await screen.findByTestId("origem-empreendimento")).toHaveTextContent("Cópia dos dados registrada no fechamento");
    expect(screen.getByTestId("origem-empreendimento")).toHaveTextContent("não mudam esta inspeção");
  });

  test.each(["ABERTA", "EM_ANDAMENTO"])("%s informa que usa os dados atuais e que serão copiados", async (status) => {
    instalarApi(com(status));
    renderizar("/inspecoes/4");
    expect(await screen.findByTestId("origem-empreendimento")).toHaveTextContent("serão copiados quando a inspeção for fechada");
  });

  test("cancelada usa os dados atuais, sem promessa de cópia", async () => {
    instalarApi(com("CANCELADA", { motivo_cancelamento: "x" }));
    renderizar("/inspecoes/4");
    const texto = await screen.findByTestId("origem-empreendimento");
    expect(texto).toHaveTextContent("Dados atuais do cadastro do local.");
    expect(texto).not.toHaveTextContent("copiados");
  });
});
