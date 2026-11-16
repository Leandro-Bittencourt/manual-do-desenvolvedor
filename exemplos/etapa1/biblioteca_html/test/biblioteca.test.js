import { beforeEach, describe, test } from "node:test";
import assert from "node:assert/strict";
import { ArmazenamentoLocal } from "../js/armazenamento.js";
import { ErroBiblioteca, ServicoBiblioteca } from "../js/biblioteca.js";
import { ArmazenamentoEmMemoria } from "./armazenamentoFalso.js";

const ISBNS = ["9780306406157", "9781861972712", "9780131103627", "9780201633610"];
const HOJE = new Date(2026, 10, 1);
const diasDepois = (dias) => new Date(HOJE.getTime() + dias * 24 * 60 * 60 * 1000);

let armazenamento;
let servico;

beforeEach(() => {
  armazenamento = new ArmazenamentoLocal(new ArmazenamentoEmMemoria());
  servico = new ServicoBiblioteca(armazenamento);
});

describe("Cadastro de livros", () => {
  test("RF-01 cadastra livro com ISBN válido", () => {
    assert.equal(servico.cadastrarLivro(ISBNS[0], "Dom Casmurro", "Machado de Assis").disponivel, true);
  });

  test("rejeita ISBN inválido", () => {
    assert.throws(() => servico.cadastrarLivro("123", "Livro", "Autor"), ErroBiblioteca);
  });

  test("rejeita ISBN repetido", () => {
    // RF-01: não pode haver dois livros com o mesmo ISBN
    servico.cadastrarLivro(ISBNS[0], "Dom Casmurro", "Machado de Assis");
    assert.throws(() => servico.cadastrarLivro(ISBNS[0], "Outro", "Outro autor"), ErroBiblioteca);
  });
});

describe("Cadastro de leitores", () => {
  test("cadastra leitor", () => {
    assert.equal(servico.cadastrarLeitor("Ana", "ana@exemplo.com").nome, "Ana");
  });

  test("RF-02 rejeita e-mail inválido", () => {
    assert.throws(() => servico.cadastrarLeitor("Ana", "email-invalido"), ErroBiblioteca);
  });
});

describe("Empréstimos e devoluções", () => {
  beforeEach(() => {
    ISBNS.forEach((isbn, i) => servico.cadastrarLivro(isbn, `Livro ${i}`, `Autor ${i}`));
    servico.cadastrarLeitor("Ana", "ana@exemplo.com");
  });

  test("empresta livro disponível", () => {
    // @traces RF-03
    servico.emprestar(ISBNS[0], "ana@exemplo.com", HOJE);
    assert.equal(armazenamento.buscarLivro(ISBNS[0]).disponivel, false);
  });

  test("limite de três empréstimos ativos", () => {
    ISBNS.slice(0, 3).forEach((isbn) => servico.emprestar(isbn, "ana@exemplo.com", HOJE));
    assert.throws(() => servico.emprestar(ISBNS[3], "ana@exemplo.com", HOJE), ErroBiblioteca);
  });

  test("devolução no prazo não gera multa", () => {
    // @traces RF-04
    servico.emprestar(ISBNS[0], "ana@exemplo.com", HOJE);
    assert.equal(servico.devolver(ISBNS[0], diasDepois(14)), 0);
  });

  test("multa por dias de atraso", () => {
    servico.emprestar(ISBNS[0], "ana@exemplo.com", HOJE);
    assert.equal(servico.devolver(ISBNS[0], diasDepois(17)), 6);
  });
});

test("busca por título ou autor sem diferenciar maiúsculas", () => {
  servico.cadastrarLivro(ISBNS[0], "Dom Casmurro", "Machado de Assis");
  servico.cadastrarLivro(ISBNS[1], "Vidas Secas", "Graciliano Ramos");
  assert.deepEqual(servico.buscarLivros("casmurro").map((l) => l.titulo), ["Dom Casmurro"]);
  assert.deepEqual(servico.buscarLivros("GRACILIANO").map((l) => l.titulo), ["Vidas Secas"]);
});
