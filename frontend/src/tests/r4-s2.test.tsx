import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { inspecao, instalarApi, local, pagina, renderizar, rota } from "./ajuda";
import type { Local } from "../api/tipos";
import { mascararCep, mascararCpfCnpj, mascararGms } from "../utils/formatar";

describe("máscaras (R4)", () => {
  test("CPF e CNPJ progressivos, só dígitos, até 14", () => {
    expect(mascararCpfCnpj("5")).toBe("5");
    expect(mascararCpfCnpj("5299")).toBe("529.9");
    expect(mascararCpfCnpj("52998224725")).toBe("529.982.247-25");
    expect(mascararCpfCnpj("529.982.247-25")).toBe("529.982.247-25");
    expect(mascararCpfCnpj("11222333000181")).toBe("11.222.333/0001-81");
    expect(mascararCpfCnpj("1122233300018199")).toBe("11.222.333/0001-81");
    expect(mascararCpfCnpj("abc")).toBe("");
  });

  test("CEP 00.000-000", () => {
    expect(mascararCep("78320000")).toBe("78.320-000");
    expect(mascararCep("783")).toBe("78.3");
    expect(mascararCep("78.320-0009999")).toBe("78.320-000");
  });

  test("GMS de latitude: __° __' __\" S", () => {
    expect(mascararGms("11", "latitude")).toBe("11");
    expect(mascararGms("1146", "latitude")).toBe("11° 46");
    expect(mascararGms("11463", "latitude")).toBe("11° 46' 3");
    expect(mascararGms("114634s", "latitude")).toBe("11° 46' 34\" S");
    expect(mascararGms("11° 46' 34\" S", "latitude")).toBe("11° 46' 34\" S"); // idempotente
    expect(mascararGms("11° 46' 34\" ", "latitude")).toBe("11° 46' 34"); // apagar a letra não trava a digitação
    expect(mascararGms("1146349999", "latitude")).toBe("11° 46' 34");
  });

  test("GMS de longitude usa 3 dígitos de graus e aceita O como Oeste", () => {
    expect(mascararGms("059 05 12 W", "longitude")).toBe("059° 05' 12\" W");
    expect(mascararGms("05905 12 o", "longitude")).toBe("059° 05' 12\" W");
    expect(mascararGms("1146 N", "longitude")).toBe("114° 6"); // N não é hemisfério de longitude
  });
});

const fazenda: Local = {
  ...local, logradouro: "Zona Rural, Gleba Fictícia", uf: "MT", cep: "78320000", cep_formatado: "78.320-000",
  latitude_gms: "10° 25' 23\" S", longitude_gms: "58° 42' 46\" W",
  proprietarios: [
    { nome: "Responsável Fictício", telefone: null, telefone_formatado: null, cpf_cnpj: "52998224725", corr_logradouro: "Zona Rural, Gleba Fictícia", corr_municipio: "Vila Nova do Cerrado", corr_uf: "MT", corr_cep: "78320000" },
  ],
};

const novoLocalBasico = async () => {
  await userEvent.type(await screen.findByLabelText("Nome do local"), "Fazenda Fictícia");
  await userEvent.type(screen.getByLabelText("Município do local"), "Cidade Fictícia");
  await userEvent.type(screen.getByLabelText("Tipo do local"), "Propriedade rural");
};

describe("Locais: coordenadas em GMS", () => {
  test("digitando só números e a letra, a máscara completa e o envio vai em GMS (a API converte)", async () => {
    const chamadas = instalarApi(rota("GET", "/locais", pagina([])), rota("POST", "/locais", (c) => ({ status: 201, corpo: { id: 9, ativo: true, ...c.corpo } })));
    renderizar("/locais/novo");
    await novoLocalBasico();
    await userEvent.click(screen.getByLabelText("Graus, minutos e segundos (GMS)"));
    await userEvent.type(screen.getByLabelText("Latitude GMS do local"), "114634s");
    await userEvent.type(screen.getByLabelText("Longitude GMS do local"), "059 05 12 w");
    expect(screen.getByLabelText("Latitude GMS do local")).toHaveValue("11° 46' 34\" S");
    expect(screen.getByLabelText("Longitude GMS do local")).toHaveValue("059° 05' 12\" W");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar local" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "POST")).toBeTruthy());
    const corpo = chamadas.find((c) => c.metodo === "POST")!.corpo;
    expect(corpo.latitude_gms).toBe("11° 46' 34\" S");
    expect(corpo.longitude_gms).toBe("059° 05' 12\" W");
    expect(corpo).not.toHaveProperty("latitude"); // só o modo escolhido vai no corpo
  });

  test("em GMS, coordenada vazia impede o envio", async () => {
    const chamadas = instalarApi();
    renderizar("/locais/novo");
    await novoLocalBasico();
    await userEvent.click(screen.getByLabelText("Graus, minutos e segundos (GMS)"));
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar local" }));
    expect(screen.getByText("Informe a latitude em GMS.")).toBeInTheDocument();
    expect(chamadas.some((c) => c.metodo === "POST")).toBe(false);
  });

  test("na edição os dois formatos já vêm preenchidos pela API", async () => {
    instalarApi(rota("GET", "/locais/1", { corpo: fazenda }), rota("GET", "/locais", pagina([fazenda])));
    renderizar("/locais/1/editar");
    expect(await screen.findByLabelText("Latitude do local")).toHaveValue("-10.42318");
    await userEvent.click(screen.getByLabelText("Graus, minutos e segundos (GMS)"));
    expect(screen.getByLabelText("Latitude GMS do local")).toHaveValue("10° 25' 23\" S");
    expect(screen.getByLabelText("Longitude GMS do local")).toHaveValue("58° 42' 46\" W");
  });
});

describe("Locais: endereço, CPF/CNPJ e correspondência", () => {
  test("campos novos chegam preenchidos e com máscara na edição; mesmo endereço vem marcado", async () => {
    instalarApi(rota("GET", "/locais/1", { corpo: fazenda }), rota("GET", "/locais", pagina([fazenda])));
    renderizar("/locais/1/editar");
    expect(await screen.findByLabelText("Logradouro do empreendimento")).toHaveValue("Zona Rural, Gleba Fictícia");
    expect(screen.getByLabelText("UF do empreendimento")).toHaveValue("MT");
    expect(screen.getByLabelText("CEP do empreendimento")).toHaveValue("78.320-000");
    expect(screen.getByLabelText("CPF/CNPJ do proprietário 1")).toHaveValue("529.982.247-25");
    expect(screen.getByLabelText("Mesmo endereço do empreendimento")).toBeChecked();
    expect(screen.getByTestId("mesmo-endereco-1")).toBeInTheDocument();
    expect(screen.queryByLabelText("Logradouro de correspondência do proprietário 1")).not.toBeInTheDocument();
  });

  test("digitar com máscara e enviar: CPF/CNPJ, CEP e endereço de correspondência próprio", async () => {
    const chamadas = instalarApi(rota("GET", "/locais", pagina([])), rota("POST", "/locais", (c) => ({ status: 201, corpo: { id: 9, ativo: true, ...c.corpo } })));
    renderizar("/locais/novo");
    await novoLocalBasico();
    await userEvent.type(screen.getByLabelText("Latitude do local"), "-12.5");
    await userEvent.type(screen.getByLabelText("Longitude do local"), "-55.5");
    await userEvent.type(screen.getByLabelText("Logradouro do empreendimento"), "Zona Rural");
    await userEvent.type(screen.getByLabelText("CEP do empreendimento"), "78320000");
    expect(screen.getByLabelText("CEP do empreendimento")).toHaveValue("78.320-000");
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar proprietário" }));
    await userEvent.type(screen.getByLabelText("Nome do proprietário 1"), "Empresa Fictícia Ltda.");
    await userEvent.type(screen.getByLabelText("CPF/CNPJ do proprietário 1"), "11222333000181");
    expect(screen.getByLabelText("CPF/CNPJ do proprietário 1")).toHaveValue("11.222.333/0001-81");
    await userEvent.type(screen.getByLabelText("Logradouro de correspondência do proprietário 1"), "Rua das Palmeiras");
    await userEvent.type(screen.getByLabelText("Número de correspondência do proprietário 1"), "123");
    await userEvent.type(screen.getByLabelText("CEP de correspondência do proprietário 1"), "78320010");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar local" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "POST")).toBeTruthy());
    const corpo = chamadas.find((c) => c.metodo === "POST")!.corpo;
    expect(corpo).toMatchObject({ logradouro: "Zona Rural", uf: "MT", cep: "78.320-000" });
    expect(corpo.proprietarios[0]).toMatchObject({
      nome: "Empresa Fictícia Ltda.", cpf_cnpj: "11.222.333/0001-81", corr_logradouro: "Rua das Palmeiras", corr_numero: "123", corr_cep: "78.320-010",
    });
    expect(corpo.proprietarios[0]).not.toHaveProperty("correspondencia_mesmo_endereco");
  });

  test("atalho 'Mesmo endereço do empreendimento' envia a flag e esconde os campos que a API copia", async () => {
    const chamadas = instalarApi(rota("GET", "/locais", pagina([])), rota("POST", "/locais", (c) => ({ status: 201, corpo: { id: 9, ativo: true, ...c.corpo } })));
    renderizar("/locais/novo");
    await novoLocalBasico();
    await userEvent.type(screen.getByLabelText("Latitude do local"), "-12.5");
    await userEvent.type(screen.getByLabelText("Longitude do local"), "-55.5");
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar proprietário" }));
    await userEvent.type(screen.getByLabelText("Nome do proprietário 1"), "Responsável Fictício");
    await userEvent.click(screen.getByLabelText("Mesmo endereço do empreendimento"));
    expect(screen.queryByLabelText("Logradouro de correspondência do proprietário 1")).not.toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Número de correspondência do proprietário 1"), "S/N"); // número continua do usuário
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar local" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "POST")).toBeTruthy());
    expect(chamadas.find((c) => c.metodo === "POST")!.corpo.proprietarios[0]).toEqual({
      nome: "Responsável Fictício", telefone: null, corr_numero: "S/N", correspondencia_mesmo_endereco: true,
    });
  });

  test("rótulos: 'Nome fantasia / denominação' no local e 'Nome / Razão social' no responsável", async () => {
    instalarApi(rota("GET", "/locais", pagina([])));
    renderizar("/locais/novo");
    expect(await screen.findByText("Nome fantasia / denominação *")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar proprietário" }));
    expect(screen.getByText("Nome / Razão social *")).toBeInTheDocument();
  });
});

const MP = {
  interessado_orgao: "Ministério Público do Estado de Mato Grosso", interessado_unidade: "1ª Promotoria de Justiça Cível",
  interessado_comarca: "Comarca de Juína", interessado_requerente: "Promotor de Justiça",
};

describe("Nova inspeção: interessado, assunto, equipe e providências", () => {
  const preencherBasico = async () => {
    await userEvent.type(await screen.findByLabelText("Número do processo"), "212345/2030");
    await userEvent.selectOptions(screen.getByLabelText("Local"), "1");
    await userEvent.type(screen.getByLabelText("Data de agendamento"), "2026-10-28");
    await userEvent.type(screen.getByLabelText("Objetivo"), "Vistoria de rotina");
  };
  const rotas = () => [rota("GET", "/locais", pagina([local])), rota("POST", "/inspecoes", { status: 201, corpo: inspecao({ id: 9, codigo: "INS-009" }) })];

  test("os blocos aparecem e o envio leva só o que foi preenchido", async () => {
    const chamadas = instalarApi(...rotas());
    renderizar("/inspecoes/nova");
    await preencherBasico();
    for (const bloco of ["Interessado", "Assunto", "Equipe técnica", "Providências tomadas"]) expect(screen.getByRole("group", { name: bloco })).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Órgão / entidade"), MP.interessado_orgao);
    await userEvent.type(screen.getByLabelText("Unidade"), MP.interessado_unidade);
    await userEvent.type(screen.getByLabelText("Requerente"), MP.interessado_requerente);
    await userEvent.selectOptions(screen.getByLabelText("Tipo de vistoria"), "Atendimento a Denúncia");
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar membro" }));
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar membro" }));
    await userEvent.type(screen.getByLabelText("Nome do membro 1"), "Analista Fictício Um");
    await userEvent.type(screen.getByLabelText("Cargo / função do membro 1"), "Engenheiro Florestal");
    await userEvent.type(screen.getByLabelText("Nome do membro 2"), "Analista Fictícia Dois");
    await userEvent.type(screen.getByLabelText("Providências (texto livre)"), "Notificado o responsável.");
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar ato" }));
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar inspeção" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "POST" && c.caminho === "/inspecoes")).toBeTruthy());
    expect(chamadas.find((c) => c.metodo === "POST" && c.caminho === "/inspecoes")!.corpo).toEqual({
      numero_processo: "212345/2030", local_id: 1, data_agendamento: "2026-10-28", objetivo: "Vistoria de rotina",
      interessado_orgao: MP.interessado_orgao, interessado_unidade: MP.interessado_unidade, interessado_requerente: MP.interessado_requerente,
      assunto_tipo: "Atendimento a Denúncia",
      equipe: [{ nome: "Analista Fictício Um", cargo: "Engenheiro Florestal", orgao: null }, { nome: "Analista Fictícia Dois", cargo: null, orgao: null }],
      providencias_texto: "Notificado o responsável.",
      atos: [{ tipo: "Notificação", numero: null }],
    });
  });

  test("assunto 'Outro' abre o campo de texto livre; outro tipo o esconde", async () => {
    instalarApi(...rotas());
    renderizar("/inspecoes/nova");
    await screen.findByLabelText("Número do processo");
    expect(screen.queryByLabelText("Descreva o assunto")).not.toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Tipo de vistoria"), "Outro");
    await userEvent.type(screen.getByLabelText("Descreva o assunto"), "Vistoria especial");
    await userEvent.selectOptions(screen.getByLabelText("Tipo de vistoria"), "Vistoria de Embargo");
    expect(screen.queryByLabelText("Descreva o assunto")).not.toBeInTheDocument();
  });

  test("os cinco valores iniciais do assunto e o 'Outro' são oferecidos", async () => {
    instalarApi(...rotas());
    renderizar("/inspecoes/nova");
    const opcoes = within(await screen.findByLabelText("Tipo de vistoria")).getAllByRole("option").map((o) => o.textContent);
    expect(opcoes).toEqual([
      "Selecione…", "Vistoria de Constatação – Fiscalização Ambiental", "Atendimento a Denúncia", "Vistoria de Embargo",
      "Vistoria Técnica – Licenciamento", "Acompanhamento de Recuperação de Área", "Outro",
    ]);
  });

  test("remover membro e ato", async () => {
    instalarApi(rota("GET", "/locais", pagina([local])));
    renderizar("/inspecoes/nova");
    await screen.findByLabelText("Número do processo");
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar membro" }));
    await userEvent.click(screen.getByRole("button", { name: "+ Adicionar ato" }));
    expect(screen.getAllByTestId("linha-membro")).toHaveLength(1);
    await userEvent.click(screen.getByRole("button", { name: "Remover membro 1" }));
    await userEvent.click(screen.getByRole("button", { name: "Remover ato 1" }));
    expect(screen.queryAllByTestId("linha-membro")).toHaveLength(0);
    expect(screen.queryAllByTestId("linha-ato")).toHaveLength(0);
  });
});

describe("Editar inspeção: capa da SEMA", () => {
  const completa = (extra = {}) =>
    inspecao({
      status: "EM_ANDAMENTO", ...MP, assunto_tipo: "Vistoria de Embargo", providencias_texto: "Texto",
      equipe: [{ nome: "Analista Fictício Um", cargo: "Engenheiro", orgao: "SEMA-MT" }],
      atos: [{ id: 7, tipo: "Notificação", numero: null }], ...extra,
    });
  const rotas = (insp: any) => [rota("GET", "/inspecoes/4", { corpo: insp }), rota("GET", "/locais", pagina([local]))];

  test("carrega os dados e envia só o que mudou (equipe e atos por inteiro)", async () => {
    const chamadas = instalarApi(...rotas(completa()), rota("PATCH", "/inspecoes/4", { corpo: completa() }));
    renderizar("/inspecoes/4/editar");
    expect(await screen.findByLabelText("Órgão / entidade")).toHaveValue(MP.interessado_orgao);
    expect(screen.getByLabelText("Tipo de vistoria")).toHaveValue("Vistoria de Embargo");
    expect(screen.getByLabelText("Nome do membro 1")).toHaveValue("Analista Fictício Um");
    await userEvent.type(screen.getByLabelText("Número do ato 1"), "NOT-0001/2030");
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "PATCH")).toBeTruthy());
    expect(chamadas.find((c) => c.metodo === "PATCH")!.corpo).toEqual({ atos: [{ tipo: "Notificação", numero: "NOT-0001/2030" }] });
  });

  test("sem alterações não envia nada", async () => {
    const chamadas = instalarApi(...rotas(completa()));
    renderizar("/inspecoes/4/editar");
    await screen.findByLabelText("Órgão / entidade");
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    expect(await screen.findByText("Nenhuma alteração para salvar.")).toBeInTheDocument();
    expect(chamadas.some((c) => c.metodo === "PATCH")).toBe(false);
  });

  test("finalizada: só o número do ato e o nº SEMA são editáveis, o resto é leitura", async () => {
    const final = completa({
      status: "FINALIZADA", resultado: "APROVADA", campos_editaveis: ["atos", "numero_relatorio_sema"],
      atos: [{ id: 7, tipo: "Notificação", numero: null }, { id: 8, tipo: "Auto de Infração", numero: "AI-1" }],
    });
    const chamadas = instalarApi(...rotas(final), rota("PATCH", "/inspecoes/4", { corpo: final }));
    renderizar("/inspecoes/4/editar");
    await screen.findByLabelText("Nº do relatório na SEMA");
    expect(screen.queryByLabelText("Órgão / entidade")).not.toBeInTheDocument();
    expect(screen.getByTestId("leitura-interessado_orgao")).toHaveTextContent(MP.interessado_orgao);
    expect(screen.queryByLabelText("Tipo do ato 1")).not.toBeInTheDocument(); // o tipo não muda
    expect(screen.queryByRole("button", { name: "+ Adicionar ato" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Remover ato 1" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "+ Adicionar membro" })).not.toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Número do ato 1"), "NOT-0001/2030");
    await userEvent.type(screen.getByLabelText("Nº do relatório na SEMA"), "RT-9/2030");
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "PATCH")).toBeTruthy());
    expect(chamadas.find((c) => c.metodo === "PATCH")!.corpo).toEqual({
      numero_relatorio_sema: "RT-9/2030",
      atos: [{ id: 7, tipo: "Notificação", numero: "NOT-0001/2030" }, { id: 8, tipo: "Auto de Infração", numero: "AI-1" }],
    });
  });

  test("detalhe da finalizada mostra 'Registrar números da SEMA' quando a API libera esses campos", async () => {
    instalarApi(rota("GET", "/inspecoes/4", { corpo: completa({ status: "FINALIZADA", resultado: "APROVADA", campos_editaveis: ["atos", "numero_relatorio_sema"] }) }));
    renderizar("/inspecoes/4");
    expect(await screen.findByRole("link", { name: "Registrar números da SEMA" })).toHaveAttribute("href", "/inspecoes/4/editar");
  });
});
