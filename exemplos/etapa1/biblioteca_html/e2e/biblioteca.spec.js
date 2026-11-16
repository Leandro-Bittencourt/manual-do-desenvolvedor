// Testes de interface com Playwright (executar com: npx playwright test).
// Eles abrem index.html no navegador e interagem com os formulários pelos seletores.
import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/index.html");
});

test("RF-01 cadastra livro pela interface", async ({ page }) => {
  await page.fill("#livro-titulo", "Dom Casmurro");
  await page.fill("#livro-autor", "Machado de Assis");
  await page.fill("#livro-isbn", "9780306406157");
  await page.click("#form-livro button");
  await expect(page.locator("#mensagem")).toHaveText('Livro "Dom Casmurro" cadastrado.');
});

test("empresta e devolve livro pela interface", async ({ page }) => {
  // @traces RF-03 RF-04
  await page.fill("#livro-titulo", "Vidas Secas");
  await page.fill("#livro-autor", "Graciliano Ramos");
  await page.fill("#livro-isbn", "9781861972712");
  await page.click("#form-livro button");
  await page.fill("#leitor-nome", "Ana");
  await page.fill("#leitor-email", "ana@exemplo.com");
  await page.click("#form-leitor button");
  await page.fill("#emprestimo-isbn", "9781861972712");
  await page.fill("#emprestimo-email", "ana@exemplo.com");
  await page.click("#form-emprestimo button");
  await page.fill("#devolucao-isbn", "9781861972712");
  await page.click("#form-devolucao button");
  await expect(page.locator("#mensagem")).toHaveText("Devolução registrada sem multa.");
});

test("busca livros pela interface", async ({ page }) => {
  await page.fill("#livro-titulo", "Dom Casmurro");
  await page.fill("#livro-autor", "Machado de Assis");
  await page.fill("#livro-isbn", "9780306406157");
  await page.click("#form-livro button");
  await page.fill("#termo-busca", "machado");
  await page.click("#form-busca button");
  await expect(page.locator("#lista-resultados li")).toHaveText(["Dom Casmurro — Machado de Assis"]);
});
