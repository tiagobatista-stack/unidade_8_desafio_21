import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { erroApi, foto, inspecao, instalarApi, item, renderizar, rota } from "./ajuda";

const imagem = (nome: string) => new File([new Uint8Array([1, 2, 3])], nome, { type: "image/jpeg" });
const detalhe = (extra = {}) => rota("GET", "/inspecoes/4", () => ({ corpo: inspecao({ status: "EM_ANDAMENTO", ...extra }) }));

describe("Observações da vistoria", () => {
  test("contador x/2000 acompanha a digitação e salva sem mudar status", async () => {
    const chamadas = instalarApi(detalhe(), rota("PATCH", "/inspecoes/4", { corpo: {} }));
    renderizar("/inspecoes/4");
    const area = await screen.findByLabelText("Observações da vistoria");
    expect(screen.getByTestId("contador-obs")).toHaveTextContent("0/2000");
    await userEvent.type(area, "Trecho norte percorrido.");
    expect(screen.getByTestId("contador-obs")).toHaveTextContent("24/2000");
    await userEvent.click(screen.getByRole("button", { name: "Salvar observações" }));
    await waitFor(() => expect(chamadas.find((c) => c.metodo === "PATCH")!.corpo).toEqual({ observacoes_vistoria: "Trecho norte percorrido." }));
  });

  test("passar de 2000 marca o contador como excedido e a API devolve o erro", async () => {
    instalarApi(detalhe({ observacoes_vistoria: "a".repeat(2000) }), rota("PATCH", "/inspecoes/4", erroApi(422, "VALIDACAO_CAMPO", "Dados inválidos.", [{ campo: "observacoes_vistoria", mensagem: "Máximo de 2000 caracteres." }])));
    renderizar("/inspecoes/4");
    const area = await screen.findByLabelText("Observações da vistoria");
    expect(screen.getByTestId("contador-obs")).toHaveTextContent("2000/2000");
    expect(screen.getByTestId("contador-obs")).not.toHaveClass("excedido");
    await userEvent.type(area, "b");
    expect(screen.getByTestId("contador-obs")).toHaveClass("excedido");
    await userEvent.click(screen.getByRole("button", { name: "Salvar observações" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Máximo de 2000 caracteres.");
  });

  test("somente leitura: vazio mostra traço e <script> aparece literal com quebras", async () => {
    instalarApi(rota("GET", "/inspecoes/1", { corpo: inspecao({ id: 1, status: "FINALIZADA", resultado: "APROVADA", observacoes_vistoria: "<script>alert(1)</script>\nsegunda linha" }) }));
    const { container, unmount } = renderizar("/inspecoes/1");
    const bloco = (await screen.findByRole("region", { name: /Observações da vistoria/ }));
    expect(bloco).toHaveTextContent("<script>alert(1)</script>");
    expect(bloco.querySelector("p.texto-puro")!.textContent).toBe("<script>alert(1)</script>\nsegunda linha"); // quebra preservada
    expect(container.querySelector("script")).toBeNull();
    unmount();
    instalarApi(rota("GET", "/inspecoes/1", { corpo: inspecao({ id: 1, status: "CANCELADA", motivo_cancelamento: "x", observacoes_vistoria: null }) }));
    renderizar("/inspecoes/1");
    expect(await screen.findByRole("region", { name: /Observações da vistoria/ })).toHaveTextContent("—");
  });
});

describe("Envio de fotos", () => {
  test("CA69: Enviar fica desabilitado enquanto faltar anotação em qualquer foto", async () => {
    instalarApi(detalhe());
    renderizar("/inspecoes/4");
    await userEvent.upload(await screen.findByLabelText("Selecionar fotos"), [imagem("a.jpg"), imagem("b.jpg")]);
    const enviar = screen.getByRole("button", { name: "Enviar" });
    expect(screen.getAllByTestId("foto-pendente")).toHaveLength(2);
    expect(enviar).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Anotação de a.jpg"), "Vista da nascente");
    expect(enviar).toBeDisabled(); // b.jpg ainda sem anotação
    await userEvent.type(screen.getByLabelText("Anotação de b.jpg"), "   ");
    expect(enviar).toBeDisabled(); // só espaços não vale
    await userEvent.type(screen.getByLabelText("Anotação de b.jpg"), "Estrada de acesso");
    expect(enviar).toBeEnabled();
  });

  test("CA70: falha parcial grava as válidas e preserva a anotação da que falhou", async () => {
    const chamadas = instalarApi(
      detalhe(),
      rota("POST", "/inspecoes/4/fotos", (c) => {
        const arquivo = (c.corpo as FormData).get("arquivo") as File;
        return arquivo.name === "ruim.gif"
          ? erroApi(415, "FOTO_FORMATO_INVALIDO", "Envie uma imagem JPEG, PNG ou WebP válida.")
          : { status: 201, corpo: foto(1) };
      }),
    );
    renderizar("/inspecoes/4");
    await userEvent.upload(await screen.findByLabelText("Selecionar fotos"), [imagem("ok1.jpg"), imagem("ruim.gif"), imagem("ok2.jpg")]);
    await userEvent.type(screen.getByLabelText("Anotação de ok1.jpg"), "Primeira");
    await userEvent.type(screen.getByLabelText("Anotação de ruim.gif"), "Esta anotação deve sobreviver");
    await userEvent.type(screen.getByLabelText("Anotação de ok2.jpg"), "Terceira");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));

    await waitFor(() => expect(screen.getAllByTestId("foto-pendente")).toHaveLength(1));
    const restante = screen.getByTestId("foto-pendente");
    expect(within(restante).getByLabelText("Anotação de ruim.gif")).toHaveValue("Esta anotação deve sobreviver");
    expect(within(restante).getByRole("alert")).toHaveTextContent("Envie uma imagem JPEG, PNG ou WebP válida.");
    const posts = chamadas.filter((c) => c.metodo === "POST");
    expect(posts).toHaveLength(3); // uma foto por requisição
    expect(posts.map((p) => ((p.corpo as FormData).get("arquivo") as File).name)).toEqual(["ok1.jpg", "ruim.gif", "ok2.jpg"]);
    expect(posts.map((p) => (p.corpo as FormData).get("anotacao"))).toEqual(["Primeira", "Esta anotação deve sobreviver", "Terceira"]);
  });

  test("envia legenda e item quando informados", async () => {
    const chamadas = instalarApi(detalhe({ itens: [item(1), item(2)] }), rota("POST", "/inspecoes/4/fotos", { status: 201, corpo: foto(1) }));
    renderizar("/inspecoes/4");
    await userEvent.upload(await screen.findByLabelText("Selecionar fotos"), imagem("x.jpg"));
    await userEvent.type(screen.getByLabelText("Anotação de x.jpg"), "Nota");
    await userEvent.type(screen.getByLabelText("Legenda de x.jpg"), "Legenda curta");
    await userEvent.selectOptions(screen.getByLabelText("Item de x.jpg"), "2");
    await userEvent.click(screen.getByRole("button", { name: "Enviar" }));
    await waitFor(() => expect(chamadas.some((c) => c.metodo === "POST")).toBe(true));
    const form = chamadas.find((c) => c.metodo === "POST")!.corpo as FormData;
    expect([form.get("anotacao"), form.get("legenda"), form.get("item_id")]).toEqual(["Nota", "Legenda curta", "2"]);
  });

  test("descartar remove a foto pendente", async () => {
    instalarApi(detalhe());
    renderizar("/inspecoes/4");
    await userEvent.upload(await screen.findByLabelText("Selecionar fotos"), imagem("x.jpg"));
    await userEvent.click(screen.getByRole("button", { name: "Descartar" }));
    expect(screen.queryByTestId("foto-pendente")).not.toBeInTheDocument();
  });
});

describe("Galeria e visualizador", () => {
  const comFotos = (status = "EM_ANDAMENTO") =>
    rota("GET", "/inspecoes/4", () => ({ corpo: inspecao({
      status: status as any,
      itens: [item(1, { descricao: "Sinalização de segurança visível", situacao: "NAO_CONFORME", qtd_fotos: 1 })],
      fotos: [
        foto(1, { anotacao: "<script>alert(1)</script>\nlinha dois", item_id: 1, legenda: "Placa" }),
        foto(2, { anotacao: "Segunda foto com anotação bem longa ".repeat(6) }),
      ],
    }) }));

  test("CA71: galeria e visualizador mostram <script> literal; selo do item e trecho", async () => {
    instalarApi(comFotos());
    const { container } = renderizar("/inspecoes/4");
    const cards = await screen.findAllByTestId("foto-galeria");
    expect(cards).toHaveLength(2);
    expect(cards[0]).toHaveTextContent("<script>alert(1)</script>");
    expect(cards[0]).toHaveTextContent("Sinalização de segurança visível");
    expect(cards[1].textContent!.endsWith("…")).toBe(true); // trecho
    await userEvent.click(within(cards[0]).getByRole("button", { name: "Abrir foto 1" }));
    const dialogo = screen.getByRole("dialog");
    expect(dialogo.querySelector("p.texto-puro")!.textContent).toBe("<script>alert(1)</script>\nlinha dois");
    expect(within(dialogo).getByRole("img")).toHaveAttribute("src", expect.stringContaining("versao=original"));
    expect(container.querySelector("script")).toBeNull();
  });

  test("anterior/próxima navegam entre as fotos", async () => {
    instalarApi(comFotos());
    renderizar("/inspecoes/4");
    await userEvent.click(await screen.findByRole("button", { name: "Abrir foto 1" }));
    expect(screen.getByRole("dialog", { name: "Foto 1 de 2" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Próxima" }));
    expect(screen.getByRole("dialog", { name: "Foto 2 de 2" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Próxima" })).toBeDisabled();
  });

  test("editar anotação envia PATCH; anotação vazia é recusada pela API e o erro aparece", async () => {
    const chamadas = instalarApi(comFotos(), rota("PATCH", "/inspecoes/4/fotos/1", (c) =>
      !String(c.corpo.anotacao).trim() ? erroApi(422, "VALIDACAO_CAMPO", "Dados inválidos.", [{ campo: "anotacao", mensagem: "Campo obrigatório." }]) : { corpo: foto(1) }));
    renderizar("/inspecoes/4");
    await userEvent.click(await screen.findByRole("button", { name: "Abrir foto 1" }));
    await userEvent.click(screen.getByRole("button", { name: "Editar" }));
    const campo = screen.getByLabelText("Editar anotação");
    await userEvent.clear(campo);
    await userEvent.click(screen.getByRole("button", { name: "Salvar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Campo obrigatório.");
    await userEvent.type(campo, "Nova anotação");
    await userEvent.click(screen.getByRole("button", { name: "Salvar" }));
    await waitFor(() => expect(chamadas.filter((c) => c.metodo === "PATCH")).toHaveLength(2));
    expect(chamadas.filter((c) => c.metodo === "PATCH")[1].corpo).toEqual({ anotacao: "Nova anotação", legenda: "Placa", item_id: 1 });
  });

  test("excluir pede confirmação antes de chamar a API", async () => {
    const chamadas = instalarApi(comFotos(), rota("DELETE", "/inspecoes/4/fotos/1", { status: 204 }));
    renderizar("/inspecoes/4");
    await userEvent.click(await screen.findByRole("button", { name: "Abrir foto 1" }));
    await userEvent.click(screen.getByRole("button", { name: "Excluir" }));
    expect(chamadas.some((c) => c.metodo === "DELETE")).toBe(false);
    expect(screen.getByText("Excluir esta foto definitivamente?")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Confirmar exclusão" }));
    await waitFor(() => expect(chamadas.some((c) => c.metodo === "DELETE")).toBe(true));
  });

  test("selo de quantidade de fotos no checklist", async () => {
    instalarApi(comFotos());
    renderizar("/inspecoes/4");
    expect(await screen.findByTestId("item-1")).toHaveTextContent("1 foto(s)");
  });

  test("FINALIZADA: galeria consultável, sem envio, edição ou exclusão", async () => {
    instalarApi(comFotos("FINALIZADA"));
    renderizar("/inspecoes/4");
    await userEvent.click(await screen.findByRole("button", { name: "Abrir foto 1" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("<script>alert(1)</script>");
    expect(screen.queryByRole("button", { name: /Editar|Excluir/ })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Fechar" }));
    expect(screen.queryByLabelText("Selecionar fotos")).not.toBeInTheDocument();
  });

  test("sem fotos: estado vazio", async () => {
    instalarApi(detalhe());
    renderizar("/inspecoes/4");
    expect(await screen.findByText("Nenhuma foto anexada.")).toBeInTheDocument();
  });
});
