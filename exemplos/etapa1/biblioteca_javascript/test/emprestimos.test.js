import { beforeEach, describe, test } from "node:test";
import assert from "node:assert/strict";
import { ErroBiblioteca, ServicoBiblioteca } from "../src/servicoBiblioteca.js";
import { RepositorioMemoria } from "./repositorioMemoria.js";

const ISBNS = ["9780306406157", "9781861972712", "9780131103627", "9780201633610"];
const HOJE = new Date(2026, 10, 1);
const diasDepois = (dias) => new Date(HOJE.getTime() + dias * 24 * 60 * 60 * 1000);

describe("Empréstimos e devoluções", () => {
  let repositorio;
  let servico;

  beforeEach(async () => {
    repositorio = new RepositorioMemoria();
    servico = new ServicoBiblioteca(repositorio);
    for (const [i, isbn] of ISBNS.entries()) {
      await servico.cadastrarLivro(isbn, `Livro ${i}`, `Autor ${i}`);
    }
    await servico.cadastrarLeitor("Ana", "ana@exemplo.com");
  });

  test("empresta livro disponível", async () => {
    // @traces RF-03
    await servico.emprestar(ISBNS[0], "ana@exemplo.com", HOJE);
    assert.equal((await repositorio.buscarLivro(ISBNS[0])).disponivel, false);
  });

  test("limite de três empréstimos ativos", async () => {
    for (const isbn of ISBNS.slice(0, 3)) {
      await servico.emprestar(isbn, "ana@exemplo.com", HOJE);
    }
    await assert.rejects(servico.emprestar(ISBNS[3], "ana@exemplo.com", HOJE), ErroBiblioteca);
  });

  test("devolução no prazo não gera multa", async () => {
    // @traces RF-04
    await servico.emprestar(ISBNS[0], "ana@exemplo.com", HOJE);
    assert.equal(await servico.devolver(ISBNS[0], diasDepois(14)), 0);
  });

  test("multa por dias de atraso", async () => {
    await servico.emprestar(ISBNS[0], "ana@exemplo.com", HOJE);
    assert.equal(await servico.devolver(ISBNS[0], diasDepois(17)), 6);
  });
});
