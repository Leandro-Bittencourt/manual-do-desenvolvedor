import { describe, test } from "node:test";
import assert from "node:assert/strict";
import { ErroBiblioteca, ServicoBiblioteca } from "../src/servicoBiblioteca.js";
import { RepositorioMemoria } from "./repositorioMemoria.js";

const ISBN_VALIDO = "9780306406157";

describe("Cadastro de livros", () => {
  test("RF-01 cadastra livro com ISBN válido", async () => {
    const servico = new ServicoBiblioteca(new RepositorioMemoria());
    const livro = await servico.cadastrarLivro(ISBN_VALIDO, "Dom Casmurro", "Machado de Assis");
    assert.equal(livro.disponivel, true);
  });

  test("rejeita ISBN inválido", async () => {
    const servico = new ServicoBiblioteca(new RepositorioMemoria());
    await assert.rejects(servico.cadastrarLivro("123", "Livro", "Autor"), ErroBiblioteca);
  });

  test("rejeita ISBN repetido", async () => {
    // RF-01: não pode haver dois livros com o mesmo ISBN
    const servico = new ServicoBiblioteca(new RepositorioMemoria());
    await servico.cadastrarLivro(ISBN_VALIDO, "Dom Casmurro", "Machado de Assis");
    await assert.rejects(servico.cadastrarLivro(ISBN_VALIDO, "Outro", "Outro autor"), ErroBiblioteca);
  });
});
