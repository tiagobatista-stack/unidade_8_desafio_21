import { expect, test, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

const raiz = path.resolve(__dirname, "..", "..");
const telas = path.join(raiz, "docs", "evidencias", "telas");
const imgs = path.join(__dirname, "..", ".tmp", "imagens");
const venv = path.join(raiz, "backend", ".venv");
const python = existsSync(path.join(venv, "Scripts", "python.exe")) ? path.join(venv, "Scripts", "python.exe") : path.join(venv, "bin", "python");
const API = "http://127.0.0.1:8100/api/v1";

const SCRIPT_IMAGENS = `
import sys
from PIL import Image, ImageDraw
d = sys.argv[1]
for nome, cor, fmt in (("ficticia1.jpg", (60, 120, 90), "JPEG"), ("ficticia2.png", (70, 100, 160), "PNG")):
    img = Image.new("RGB", (800, 600), cor)
    ImageDraw.Draw(img).text((60, 280), "FOTO FICTICIA - " + nome, fill=(255, 255, 255))
    img.save(d + "/" + nome, format=fmt)
open(d + "/texto.jpg", "w").write("isto nao e uma imagem")
`;

let n = 0;
async function tela(page: Page, nome: string) {
  n += 1;
  await page.screenshot({ path: path.join(telas, `${String(n).padStart(2, "0")}-${nome}.png`), fullPage: true });
}
const indicador = (page: Page, id: string) => page.getByTestId(`indicador-${id}`);
const irPara = (page: Page, nome: string) => page.getByRole("navigation", { name: "Principal" }).getByRole("link", { name: nome, exact: true }).click();

test.describe.serial("Fluxo completo do MVP", () => {
  test.beforeAll(() => {
    mkdirSync(telas, { recursive: true });
    mkdirSync(imgs, { recursive: true });
    execFileSync(python, ["-I", "-c", SCRIPT_IMAGENS, imgs]);
  });

  test("painel vazio e carga de exemplos (5/2/3)", async ({ page }) => {
    await page.goto("/");
    await expect(indicador(page, "inspecoes")).toContainText("0");
    await tela(page, "painel-vazio");
    await page.getByRole("button", { name: "Carregar exemplos" }).click();
    await tela(page, "confirmar-carga-exemplos");
    await page.getByRole("button", { name: "Confirmar" }).click();
    await expect(indicador(page, "inspecoes")).toContainText("5");
    await expect(indicador(page, "pendencias")).toContainText("2");
    await expect(indicador(page, "finalizadas")).toContainText("3");
    await expect(page.getByRole("status")).toContainText("9 fotos fictícias");
    await tela(page, "painel-com-exemplos-5-2-3");
  });

  test("lista, filtros e pendências", async ({ page }) => {
    await page.goto("/");
    await irPara(page, "Inspeções");
    await expect(page.getByRole("row")).toHaveCount(6); // cabeçalho + 5
    await tela(page, "lista-inspecoes");
    await page.getByLabel("Filtrar por status").selectOption("FINALIZADA");
    await expect(page.getByRole("row")).toHaveCount(4);
    await page.getByLabel("Filtrar por status").selectOption("");
    await page.getByLabel("Data inicial").fill("2026-10-13");
    await page.getByLabel("Data final").fill("2026-10-20");
    await expect(page.getByRole("row")).toHaveCount(4); // INS-002, 003, 004 (período inclusivo)
    await tela(page, "lista-filtro-periodo");
    await irPara(page, "Painel");
    await page.getByRole("link", { name: "Ver pendências" }).click();
    await expect(page.getByRole("row")).toHaveCount(3);
    await expect(page.getByRole("link", { name: "INS-004", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "INS-005", exact: true })).toBeVisible();
    await tela(page, "lista-pendencias");
  });

  test("contadores do painel listam cada categoria", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("indicador-pendencias").click();
    await expect(page.getByTestId("filtro-ativo")).toContainText("Pendências");
    await expect(page.getByRole("row")).toHaveCount(3); // INS-004 e INS-005
    await tela(page, "painel-clique-pendencias");
    await irPara(page, "Painel");
    await page.getByTestId("indicador-finalizadas").click();
    await expect(page.getByRole("row")).toHaveCount(4); // INS-001..003
    await expect(page.getByRole("link", { name: "INS-001", exact: true })).toBeVisible();
    await tela(page, "painel-clique-finalizadas");
    await irPara(page, "Painel");
    await page.getByTestId("indicador-inspecoes").click();
    await expect(page.getByRole("row")).toHaveCount(6); // todas, exceto canceladas (hoje nenhuma)
    await expect(page.getByTestId("filtro-ativo")).toContainText("5 inspeção(ões)");
    await tela(page, "painel-clique-inspecoes");
  });

  test("editar inspeção, número do processo e busca", async ({ page }) => {
    await page.goto("/inspecoes");
    await expect(page.getByRole("link", { name: "Editar INS-001" })).toHaveCount(0); // finalizada: sem botão
    await expect(page.getByRole("cell", { name: "SEMA-PRO-2026/10005" })).toBeVisible();
    await page.getByRole("link", { name: "Editar INS-005" }).click();
    await expect(page.getByRole("heading", { name: "Editar INS-005" })).toBeVisible();
    await expect(page.getByLabel("Data de agendamento")).toBeEnabled(); // Aberta: agendamento editável
    await expect(page.getByLabel("Data de realização")).toHaveCount(0); // bloqueada nesse status
    await page.getByLabel("Número do processo").fill("");
    await page.getByRole("button", { name: "Salvar alterações" }).click();
    await expect(page.getByRole("alert")).toContainText("Campo obrigatório");
    await tela(page, "editar-aberta-erro-processo-obrigatorio");
    await page.getByLabel("Número do processo").fill("SEMA-PRO-2026/20005");
    await page.getByLabel("Objetivo").fill("Vistoria reagendada pelo processo 20005");
    await page.getByRole("button", { name: "Salvar alterações" }).click();
    await expect(page.getByRole("heading", { name: "INS-005" })).toBeVisible();
    await expect(page.getByTestId("numero-processo")).toHaveText("SEMA-PRO-2026/20005");
    await expect(page.getByText("Vistoria reagendada pelo processo 20005")).toBeVisible();
    await tela(page, "detalhe-apos-editar");
    // Em andamento: agendamento e local viram texto; processo continua editável
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "Editar INS-004" }).click();
    await expect(page.getByLabel("Data de realização")).toBeEnabled();
    await expect(page.getByLabel("Data de agendamento")).toHaveCount(0);
    await expect(page.getByTestId("leitura-data_agendamento")).toHaveText("20/10/2026");
    await tela(page, "editar-em-andamento-campos-bloqueados");
    // finalizada: a rota existe mas nada é editável
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-001", exact: true }).click();
    await expect(page.getByRole("link", { name: "Editar inspeção" })).toHaveCount(0);
    // busca por número do processo
    await page.goto("/inspecoes");
    await page.getByLabel("Buscar por número do processo").fill("20005");
    await expect(page.getByRole("row")).toHaveCount(2);
    await expect(page.getByRole("link", { name: "INS-005", exact: true })).toBeVisible();
    await tela(page, "lista-busca-por-processo");
    await page.getByLabel("Buscar por número do processo").fill("sema-pro-2026/1000");
    await expect(page.getByRole("row")).toHaveCount(5); // 001..004 (005 mudou para 20005)
  });

  test("Locais: cadastrar e editar com CAR e proprietários e ver o empreendimento na inspeção", async ({ page }) => {
    await page.goto("/");
    await irPara(page, "Locais");
    await expect(page.getByRole("row")).toHaveCount(5); // cabeçalho + 4 locais de exemplo
    await expect(page.getByRole("cell", { name: "(65) 90000-0001" }).first()).toBeVisible();
    await tela(page, "locais-lista");
    await page.getByRole("link", { name: "Novo local" }).click();
    await page.getByLabel("Nome do local").fill("Fazenda E2E Fictícia");
    await page.getByLabel("Município do local").fill("Cidade E2E Fictícia");
    await page.getByLabel("Tipo do local").fill("Propriedade rural");
    await page.getByLabel("Latitude do local").fill("-12,5");
    await page.getByLabel("Longitude do local").fill("-55,5");
    await page.getByLabel("Número do CAR").fill("mt-5107925-00000000000000000000000000009999");
    await page.getByRole("button", { name: "+ Adicionar proprietário" }).click();
    await page.getByLabel("Nome do proprietário 1").fill("Dono E2E Fictício");
    await page.getByLabel("Telefone do proprietário 1").fill("65900000009");
    await page.getByLabel("Nome do local").click(); // sai do campo: o telefone é formatado
    await expect(page.getByLabel("Telefone do proprietário 1")).toHaveValue("(65) 90000-0009");
    await tela(page, "local-novo-com-car-e-proprietario");
    await page.getByRole("button", { name: "Cadastrar local" }).click();
    const linha = page.getByRole("row").filter({ hasText: "Fazenda E2E Fictícia" });
    await expect(linha).toContainText("MT-5107925-00000000000000000000000000009999"); // guardado em maiúsculas
    await expect(linha).toContainText("Dono E2E Fictício — (65) 90000-0009");
    // editar: telefone inválido é recusado pela API, depois corrigido; segundo proprietário
    await page.getByRole("link", { name: "Editar Fazenda E2E Fictícia" }).click();
    await page.getByRole("button", { name: "+ Adicionar proprietário" }).click();
    await page.getByLabel("Nome do proprietário 2").fill("Dona E2E Fictícia");
    await page.getByLabel("Telefone do proprietário 2").fill("123");
    await page.getByRole("button", { name: "Salvar alterações" }).click();
    await expect(page.getByRole("alert")).toContainText("proprietarios.1.telefone");
    await tela(page, "local-telefone-invalido-recusado");
    await page.getByLabel("Telefone do proprietário 2").fill("6533334444");
    await page.getByRole("button", { name: "Salvar alterações" }).click();
    await expect(page.getByRole("row").filter({ hasText: "Fazenda E2E Fictícia" })).toContainText("Dona E2E Fictícia — (65) 3333-4444");
    await tela(page, "locais-lista-apos-editar");
    // o novo local aparece no detalhe da inspeção (Em aberto: dados atuais do Local)
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "Editar INS-005" }).click();
    await page.getByLabel("Local").selectOption({ label: "Fazenda E2E Fictícia — Cidade E2E Fictícia" });
    await page.getByRole("button", { name: "Salvar alterações" }).click();
    const cartao = page.getByTestId("empreendimento");
    await expect(cartao).toContainText("Fazenda E2E Fictícia — Cidade E2E Fictícia");
    await expect(page.getByTestId("numero-car")).toHaveText("MT-5107925-00000000000000000000000000009999");
    await expect(page.getByTestId("proprietarios")).toContainText("Dono E2E Fictício — (65) 90000-0009");
    await tela(page, "detalhe-empreendimento-car-e-proprietarios");
  });

  test("nova inspeção e cancelamento com motivo", async ({ page }) => {
    await page.goto("/inspecoes/nova");
    await page.getByRole("button", { name: "Cadastrar inspeção" }).click();
    await expect(page.getByText("Selecione um local.")).toBeVisible();
    await expect(page.getByText("Informe o número do processo.")).toBeVisible();
    await tela(page, "nova-inspecao-campos-obrigatorios");
    // novo local: coordenada fora de MT é recusada, corrigida e o local já vem selecionado
    await page.getByRole("button", { name: "+ Novo local" }).click();
    await page.getByLabel("Nome do local").fill("Frigorífico Boa Terra (fictício)");
    await page.getByLabel("Município do local").fill("Sinop");
    await page.getByLabel("Tipo do local").fill("Indústria alimentícia");
    await page.getByLabel("Latitude do local").fill("-25");
    await page.getByLabel("Longitude do local").fill("-55,5");
    await page.getByRole("button", { name: "Salvar local" }).click();
    await expect(page.getByRole("dialog").getByRole("alert")).toContainText("Coordenada fora de Mato Grosso");
    await tela(page, "novo-local-coordenada-fora-de-mt");
    await page.getByLabel("Latitude do local").fill("-11,85");
    await page.getByRole("button", { name: "Salvar local" }).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page.getByLabel("Local")).toHaveValue(/\d+/);
    await expect(page.getByLabel("Local").locator("option:checked")).toHaveText("Frigorífico Boa Terra (fictício) — Sinop");
    await expect(page.getByLabel("Latitude")).toHaveValue("-11.85");
    await page.getByLabel("Número do processo").fill("SEMA-PRO-2026/12345");
    await page.getByLabel("Data de agendamento").fill("2026-10-30");
    await page.getByLabel("Objetivo").fill("Verificação de rotina do posto (exemplo fictício)");
    await tela(page, "nova-inspecao-preenchida");
    await page.getByRole("button", { name: "Cadastrar inspeção" }).click();
    await expect(page.getByRole("heading", { name: "INS-006" })).toBeVisible();
    await expect(page.getByTestId(/^item-/)).toHaveCount(6);
    await expect(page.getByTestId("numero-processo")).toHaveText("SEMA-PRO-2026/12345");
    await expect(page.getByTestId("aviso-agendamento-futuro")).toContainText("Vistoria agendada para 30/10/2026");
    await expect(page.getByRole("button", { name: "Fechar inspeção" })).toBeDisabled();
    await expect(page.getByText("Frigorífico Boa Terra (fictício) — Sinop")).toBeVisible();
    await tela(page, "detalhe-inspecao-aberta");
    await page.getByRole("button", { name: "Cancelar inspeção" }).click();
    await page.getByLabel("Motivo do cancelamento").fill("Responsável indisponível na data");
    await tela(page, "modal-cancelar");
    await page.getByRole("button", { name: "Confirmar cancelamento" }).click();
    await expect(page.getByText("Somente leitura", { exact: true })).toBeVisible();
    await expect(page.getByText("Responsável indisponível na data")).toBeVisible();
    await tela(page, "detalhe-inspecao-cancelada");
    await irPara(page, "Painel");
    await expect(indicador(page, "inspecoes")).toContainText("5"); // cancelada não conta
    await expect(indicador(page, "pendencias")).toContainText("2");
  });

  test("INS-005: agendamento futuro mostra o aviso antes de qualquer tentativa e bloqueia a situação (P1)", async ({ page }) => {
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-005", exact: true }).click();
    const aviso = page.getByTestId("aviso-agendamento-futuro");
    await expect(aviso).toContainText("Vistoria agendada para 28/10/2026");
    await expect(aviso.getByRole("link", { name: "Editar inspeção" })).toBeVisible();
    await expect(page.getByLabel(/^Situação de Licença/)).toBeDisabled(); // sem precisar tentar
    await expect(page.getByTestId("aviso-inicio")).toContainText("quando você registrar a situação do primeiro item");
    await expect(page.getByRole("button", { name: "Fechar inspeção" })).toBeDisabled();
    await expect(page.getByTestId("motivo-fechar")).toContainText("A inspeção ainda não foi iniciada");
    await tela(page, "aviso-agendamento-futuro-e-fechar-desabilitado");
    await aviso.getByRole("link", { name: "Editar inspeção" }).click();
    await expect(page.getByRole("heading", { name: "Editar INS-005" })).toBeVisible();
  });

  test("INS-004: fechamento bloqueado destaca os itens pendentes", async ({ page }) => {
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-004", exact: true }).click();
    await expect(page.getByRole("heading", { name: "INS-004" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Fotos da vistoria \(2\)/ })).toBeVisible();
    await tela(page, "detalhe-em-andamento-com-fotos");
    await page.getByRole("button", { name: "Fechar inspeção" }).click();
    await expect(page.getByRole("dialog")).toContainText("Fotos anexadas: 2");
    await tela(page, "modal-fechar");
    await page.getByRole("button", { name: "Confirmar fechamento" }).click();
    await expect(page.locator(".item-destacado")).toHaveCount(3);
    await expect(page.getByRole("alert").first()).toContainText("Há itens pendentes");
    await tela(page, "fechamento-bloqueado-itens-destacados");
  });

  test("INS-004: fotos com anotação obrigatória, falha parcial e visualizador", async ({ page }) => {
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-004", exact: true }).click();
    await page.getByLabel("Selecionar fotos").setInputFiles([
      path.join(imgs, "ficticia1.jpg"), path.join(imgs, "ficticia2.png"), path.join(imgs, "texto.jpg"),
    ]);
    await expect(page.getByTestId("foto-pendente")).toHaveCount(3);
    await expect(page.getByRole("button", { name: "Enviar" })).toBeDisabled(); // CA69
    await tela(page, "fotos-pendentes-enviar-desabilitado");
    await page.getByLabel("Anotação de ficticia1.jpg").fill("Vista geral do trecho sul, com vegetação ciliar preservada.");
    await page.getByLabel("Legenda de ficticia1.jpg").fill("Trecho sul");
    await page.getByLabel("Anotação de ficticia2.png").fill("Marco de divisa <b>sem</b> sinais de invasão.");
    await page.getByLabel("Anotação de texto.jpg").fill("Esta anotação precisa sobreviver à falha.");
    await expect(page.getByRole("button", { name: "Enviar" })).toBeEnabled();
    await page.getByRole("button", { name: "Enviar" }).click();
    await expect(page.getByTestId("foto-pendente")).toHaveCount(1); // CA70
    await expect(page.getByLabel("Anotação de texto.jpg")).toHaveValue("Esta anotação precisa sobreviver à falha.");
    await expect(page.getByTestId("foto-pendente").getByRole("alert")).toContainText("JPEG, PNG ou WebP");
    await expect(page.getByTestId("foto-galeria")).toHaveCount(4);
    await tela(page, "falha-parcial-anotacao-preservada");
    await page.getByRole("button", { name: "Descartar" }).click();
    await page.getByRole("button", { name: "Abrir foto 4" }).click();
    const dialogo = page.getByRole("dialog");
    await expect(dialogo).toContainText("Marco de divisa <b>sem</b> sinais de invasão."); // texto literal
    await expect(dialogo.locator("b")).toHaveCount(0);
    await expect(dialogo.getByRole("img")).toHaveJSProperty("complete", true);
    await tela(page, "visualizador-foto-anotacao-literal");
    await dialogo.getByRole("button", { name: "Fechar" }).click();
    await page.reload(); // persistência: nada se perde ao recarregar
    await expect(page.getByTestId("foto-galeria")).toHaveCount(4);
    await tela(page, "galeria-apos-recarregar");
  });

  test("INS-004: responder itens, observações da vistoria e fechar (1 pendência, 4 finalizadas)", async ({ page }) => {
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-004", exact: true }).click();
    for (const nome of [/^Situação de Sinalização/, /^Situação de Registro/, /^Situação de Destinação/]) {
      const select = page.getByLabel(nome);
      await select.selectOption("CONFORME");
      await expect(select).toHaveValue("CONFORME");
    }
    await page.getByRole("textbox", { name: "Observações da vistoria" }).fill("Trecho sul percorrido.\nSem pendências visíveis.");
    await expect(page.getByTestId("contador-obs")).toContainText("/2000");
    await page.getByRole("button", { name: "Salvar observações" }).click();
    await expect(page.getByRole("button", { name: "Salvar observações" })).toBeDisabled();
    await tela(page, "checklist-respondido-e-observacoes");
    await page.getByRole("button", { name: "Fechar inspeção" }).click();
    await page.getByRole("button", { name: "Confirmar fechamento" }).click();
    await expect(page.getByText("Somente leitura", { exact: true })).toBeVisible();
    await expect(page.locator("dt", { hasText: /^Resultado$/ }).locator("..")).toContainText("Aprovada");
    await expect(page.getByRole("button", { name: "Fechar inspeção" })).toHaveCount(0);
    await expect(page.getByTestId("concluido-em")).toHaveText(/^Checklist concluído em \d{2}\/\d{2}\/\d{4} \d{2}:\d{2}$/);
    await tela(page, "inspecao-finalizada-somente-leitura");
    await irPara(page, "Painel");
    await expect(indicador(page, "inspecoes")).toContainText("5");
    await expect(indicador(page, "pendencias")).toContainText("1");
    await expect(indicador(page, "finalizadas")).toContainText("4");
    await tela(page, "painel-apos-fechar-5-1-4");
  });

  test("cópia no fechamento: editar o Local depois não muda a inspeção finalizada", async ({ page }) => {
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-004", exact: true }).click();
    const emp = page.getByTestId("empreendimento");
    await expect(page.getByTestId("origem-empreendimento")).toContainText("Cópia dos dados registrada no fechamento");
    await expect(emp).toContainText("Reserva Mata Ciliar Beta — Campo Verde do Sul");
    await expect(page.getByTestId("proprietarios")).toContainText("Proprietário Fictício Quatro");
    // troca tipo e proprietário no cadastro do Local
    await irPara(page, "Locais");
    await page.getByRole("link", { name: "Editar Reserva Mata Ciliar Beta" }).click();
    await page.getByLabel("Tipo do local").fill("Tipo alterado depois (E2E)");
    await page.getByLabel("Nome do proprietário 1").fill("Dono Novo Fictício");
    await page.getByRole("button", { name: "Salvar alterações" }).click();
    await expect(page.getByRole("row").filter({ hasText: "Reserva Mata Ciliar Beta" })).toContainText("Dono Novo Fictício");
    // a finalizada continua com os dados do fechamento
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-004", exact: true }).click();
    await expect(page.getByTestId("proprietarios")).toContainText("Proprietário Fictício Quatro");
    await expect(page.getByTestId("proprietarios")).not.toContainText("Dono Novo Fictício");
    await expect(page.getByTestId("empreendimento")).toContainText("Área de preservação");
    await expect(page.getByTestId("empreendimento")).not.toContainText("Tipo alterado depois");
    await tela(page, "copia-no-fechamento-local-editado-depois");
  });

  test("relatório: INS-004 finalizada (com fotos) numerada e imprimível; prévia da INS-005", async ({ page }) => {
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-004", exact: true }).click();
    await expect(page.getByTestId("numero-relatorio")).toHaveText("nº 0004/2026"); // as 3 do exemplo são 0001..0003
    await page.getByRole("link", { name: "Gerar relatório" }).click();
    await expect(page.getByTestId("titulo-relatorio")).toHaveText("Relatório de Vistoria nº 0004/2026");
    await expect(page.getByRole("heading", { level: 2 })).toHaveText([
      "1. Identificação", "2. Empreendimento", "3. Objetivo e observações", "4. Checklist", "5. Registro fotográfico", "6. Conclusão",
    ]);
    await expect(page.getByTestId("foto-relatorio")).toHaveCount(4);
    await expect(page.getByRole("button", { name: "Imprimir / Salvar PDF" })).toBeEnabled(); // imagens já carregadas
    const larguras = await page.locator("figure img").evaluateAll((imgs) => imgs.map((i) => (i as HTMLImageElement).naturalWidth));
    expect(larguras.every((w) => w > 0)).toBe(true);
    // o relatório usa a cópia do fechamento (o Local foi editado depois, no passo anterior)
    await expect(page.getByTestId("rel-proprietarios")).toContainText("Proprietário Fictício Quatro");
    await expect(page.getByTestId("rel-proprietarios")).not.toContainText("Dono Novo Fictício");
    await expect(page.getByTestId("rel-car")).toContainText("MT-5107925-00000000000000000000000000000004");
    await expect(page.getByTestId("conclusao-resultado")).toContainText("Aprovada");
    await expect(page.getByTestId("conclusao-regra")).toContainText("Nenhum item não conforme");
    await expect(page.getByTestId("rodape-relatorio")).toContainText("Relatório nº 0004/2026 · INS-004 · Sistema fictício/simulado");
    await tela(page, "relatorio-finalizado-INS-004");
    // modo de impressão: sem menu nem botões
    await page.emulateMedia({ media: "print" });
    await expect(page.locator(".topo")).toBeHidden();
    await expect(page.getByRole("button", { name: "Imprimir / Salvar PDF" })).toBeHidden();
    await tela(page, "relatorio-finalizado-modo-impressao");
    const pdf = path.join(raiz, "docs", "evidencias", "relatorio-INS-004.pdf");
    await page.pdf({ path: pdf, format: "A4", preferCSSPageSize: true, printBackground: true });
    const paginas = (readFileSync(pdf).toString("latin1").match(/\/Type\s*\/Page(?!s)/g) ?? []).length;
    expect(paginas).toBeGreaterThanOrEqual(4); // dados + checklist, duas páginas de fotos (pares) e conclusão
    await page.emulateMedia({ media: "screen" });
    // prévia: inspeção aberta, sem número e com a marca
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-005", exact: true }).click();
    await expect(page.getByTestId("numero-relatorio")).toHaveCount(0);
    await page.getByRole("link", { name: "Gerar relatório" }).click();
    await expect(page.getByTestId("marca-dagua")).toHaveText("PRÉVIA, NÃO FINALIZADO");
    await expect(page.getByTestId("titulo-relatorio")).toHaveText("Relatório de Vistoria (sem número)");
    await expect(page.getByTestId("rel-numero")).toHaveText("— (prévia)");
    await tela(page, "relatorio-previa-nao-finalizado");
    await page.emulateMedia({ media: "print" });
    await page.pdf({ path: path.join(raiz, "docs", "evidencias", "relatorio-previa-INS-005.pdf"), format: "A4", preferCSSPageSize: true, printBackground: true });
    await page.emulateMedia({ media: "screen" });
  });

  test("INS-003 reprovada em somente leitura e layout estreito", async ({ page }) => {
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-003", exact: true }).click();
    await expect(page.locator("dt", { hasText: /^Resultado$/ }).locator("..")).toContainText("Reprovada");
    await expect(page.getByLabel("Selecionar fotos")).toHaveCount(0);
    await page.setViewportSize({ width: 390, height: 844 });
    await tela(page, "detalhe-reprovada-celular");
  });

  test("exportação CSV e verificação de fotos pela API", async ({ page, request }) => {
    await page.goto("/");
    const [download] = await Promise.all([page.waitForEvent("download"), page.getByRole("link", { name: "Exportar CSV" }).click()]);
    expect(download.suggestedFilename()).toBe("inspecoes.csv");
    const csv = await request.get(`${API}/exportacao/inspecoes.csv`);
    const texto = (await csv.text()).replace(/^\uFEFF/, "");
    const linhas = texto.trim().split("\r\n");
    expect(linhas[0]).toBe("codigo;numero_processo;local;latitude;longitude;data_agendamento;data_realizacao;status;resultado;observacoes_vistoria;qtd_fotos");
    expect(linhas.some((l) => l.startsWith("INS-006;") && l.includes(";CANCELADA;"))).toBe(true);
    expect(linhas.find((l) => l.startsWith("INS-004;SEMA-PRO-2026/10004;"))).toMatch(/;FINALIZADA;APROVADA;"?Trecho sul percorrido\.[\s\S]*;4$/);
    writeFileSync(path.join(raiz, "docs", "evidencias", "exportacao-e2e.csv"), texto, "utf-8");
    // CSV dos itens do checklist: arquivo separado, uma linha por item
    const [downloadItens] = await Promise.all([page.waitForEvent("download"), page.getByRole("link", { name: "Exportar itens (CSV)" }).click()]);
    expect(downloadItens.suggestedFilename()).toBe("itens-checklist.csv");
    const csvItens = (await (await request.get(`${API}/exportacao/itens.csv`)).text()).replace(/^\uFEFF/, "");
    const itens = csvItens.trim().split("\r\n");
    expect(itens[0]).toBe("codigo_inspecao;numero_processo;local;status_inspecao;resultado_inspecao;item_numero;item_descricao;critico;situacao;observacao;origem;qtd_fotos");
    expect(itens.length - 1).toBe(6 * 6); // INS-001..INS-006 (a cancelada também), 6 itens do modelo cada
    expect(itens.find((l) => l.startsWith("INS-003;") && l.includes(";6;Destinação de efluentes regular;")))
      .toMatch(/;REPROVADA;6;Destinação de efluentes regular;sim;NAO_CONFORME;Caixa separadora com sinais de transbordamento[^;]*;MODELO;2$/);
    expect(itens.some((l) => l.startsWith("INS-006;") && l.includes(";CANCELADA;"))).toBe(true);
    writeFileSync(path.join(raiz, "docs", "evidencias", "itens-checklist-e2e.csv"), csvItens, "utf-8");
    const verif = await (await request.get(`${API}/utilitarios/verificar-fotos`)).json();
    expect(verif.total_inconsistencias).toBe(0);
  });
});
