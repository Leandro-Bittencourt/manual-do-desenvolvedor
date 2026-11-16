import { test } from "node:test";
import assert from "node:assert/strict";
import { ServicoBiblioteca } from "../src/servicoBiblioteca.js";
import { RepositorioMemoria } from "./repositorioMemoria.js";

test("busca por título ou autor sem diferenciar maiúsculas", async () => {
  const servico = new ServicoBiblioteca(new RepositorioMemoria());
  await servico.cadastrarLivro("9780306406157", "Dom Casmurro", "Machado de Assis");
  await servico.cadastrarLivro("9781861972712", "Vidas Secas", "Graciliano Ramos");
  assert.deepEqual((await servico.buscarLivros("casmurro")).map((l) => l.titulo), ["Dom Casmurro"]);
  assert.deepEqual((await servico.buscarLivros("GRACILIANO")).map((l) => l.titulo), ["Vidas Secas"]);
});
