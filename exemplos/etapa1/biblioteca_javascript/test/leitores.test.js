import { describe, test } from "node:test";
import assert from "node:assert/strict";
import { ErroBiblioteca, ServicoBiblioteca } from "../src/servicoBiblioteca.js";
import { RepositorioMemoria } from "./repositorioMemoria.js";

describe("Cadastro de leitores", () => {
  test("cadastra leitor", async () => {
    const servico = new ServicoBiblioteca(new RepositorioMemoria());
    const leitor = await servico.cadastrarLeitor("Ana", "ana@exemplo.com");
    assert.equal(leitor.nome, "Ana");
  });

  test("RF-02 rejeita e-mail inválido", async () => {
    const servico = new ServicoBiblioteca(new RepositorioMemoria());
    await assert.rejects(servico.cadastrarLeitor("Ana", "email-invalido"), ErroBiblioteca);
  });
});
