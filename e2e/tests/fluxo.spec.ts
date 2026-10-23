import { expect, test, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
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
    await expect(page.getByRole("link", { name: "INS-004" })).toBeVisible();
    await expect(page.getByRole("link", { name: "INS-005" })).toBeVisible();
    await tela(page, "lista-pendencias");
  });

  test("nova inspeção e cancelamento com motivo", async ({ page }) => {
    await page.goto("/inspecoes/nova");
    await page.getByRole("button", { name: "Cadastrar inspeção" }).click();
    await expect(page.getByText("Selecione um local.")).toBeVisible();
    await tela(page, "nova-inspecao-campos-obrigatorios");
    await page.getByLabel("Local").selectOption({ label: "Posto Rio Claro — São Tomé do Norte" });
    await expect(page.getByLabel("Latitude")).toHaveValue("-9.71234");
    await page.getByLabel("Data de agendamento").fill("2026-10-30");
    await page.getByLabel("Objetivo").fill("Verificação de rotina do posto (exemplo fictício)");
    await tela(page, "nova-inspecao-preenchida");
    await page.getByRole("button", { name: "Cadastrar inspeção" }).click();
    await expect(page.getByRole("heading", { name: "INS-006" })).toBeVisible();
    await expect(page.getByTestId(/^item-/)).toHaveCount(6);
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

  test("INS-005: registrar item em vistoria agendada para o futuro é bloqueado (P1)", async ({ page }) => {
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-005" }).click();
    await page.getByLabel(/^Situação de Licença/).selectOption("CONFORME");
    await expect(page.getByRole("alert")).toContainText("Vistoria agendada para 28/10/2026");
    await expect(page.getByText("Aberta").first()).toBeVisible();
    await tela(page, "bloqueio-vistoria-agendada-p1");
  });

  test("INS-004: fechamento bloqueado destaca os itens pendentes", async ({ page }) => {
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-004" }).click();
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
    await page.getByRole("link", { name: "INS-004" }).click();
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
    await page.getByRole("link", { name: "INS-004" }).click();
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
    await tela(page, "inspecao-finalizada-somente-leitura");
    await irPara(page, "Painel");
    await expect(indicador(page, "inspecoes")).toContainText("5");
    await expect(indicador(page, "pendencias")).toContainText("1");
    await expect(indicador(page, "finalizadas")).toContainText("4");
    await tela(page, "painel-apos-fechar-5-1-4");
  });

  test("INS-003 reprovada em somente leitura e layout estreito", async ({ page }) => {
    await page.goto("/inspecoes");
    await page.getByRole("link", { name: "INS-003" }).click();
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
    const texto = (await csv.text()).replace(/^﻿/, "");
    const linhas = texto.trim().split("\r\n");
    expect(linhas[0]).toBe("codigo;local;latitude;longitude;data_agendamento;data_realizacao;status;resultado;observacoes_vistoria;qtd_fotos");
    expect(linhas.some((l) => l.startsWith("INS-006;") && l.includes(";CANCELADA;"))).toBe(true);
    expect(linhas.find((l) => l.startsWith("INS-004;"))).toMatch(/;FINALIZADA;APROVADA;"?Trecho sul percorrido\.[\s\S]*;4$/);
    writeFileSync(path.join(raiz, "docs", "evidencias", "exportacao-e2e.csv"), texto, "utf-8");
    const verif = await (await request.get(`${API}/utilitarios/verificar-fotos`)).json();
    expect(verif.total_inconsistencias).toBe(0);
  });
});
