import { ArmazenamentoLocal } from "./armazenamento.js";
import { ServicoBiblioteca } from "./biblioteca.js";

const servico = new ServicoBiblioteca(new ArmazenamentoLocal());

function mostrarMensagem(texto) {
  document.getElementById("mensagem").textContent = texto;
}

function valor(id) {
  return document.getElementById(id).value.trim();
}

function executar(evento, acao) {
  evento.preventDefault();
  try {
    mostrarMensagem(acao());
    evento.target.reset();
  } catch (erro) {
    mostrarMensagem(erro.message);
  }
}

export function aoCadastrarLivro(evento) {
  executar(evento, () => {
    const livro = servico.cadastrarLivro(valor("livro-isbn"), valor("livro-titulo"), valor("livro-autor"));
    return `Livro "${livro.titulo}" cadastrado.`;
  });
}

export function aoCadastrarLeitor(evento) {
  executar(evento, () => {
    const leitor = servico.cadastrarLeitor(valor("leitor-nome"), valor("leitor-email"));
    return `Leitor ${leitor.nome} cadastrado.`;
  });
}

export function aoEmprestar(evento) {
  executar(evento, () => {
    servico.emprestar(valor("emprestimo-isbn"), valor("emprestimo-email"), new Date());
    return "Empréstimo registrado.";
  });
}

export function aoDevolver(evento) {
  executar(evento, () => {
    const multa = servico.devolver(valor("devolucao-isbn"), new Date());
    return multa > 0 ? `Devolução registrada. Multa: R$ ${multa.toFixed(2)}` : "Devolução registrada sem multa.";
  });
}

export function aoBuscar(evento) {
  evento.preventDefault();
  const lista = document.getElementById("lista-resultados");
  lista.replaceChildren(
    ...servico.buscarLivros(valor("termo-busca")).map((livro) => {
      const item = document.createElement("li");
      item.textContent = `${livro.titulo} — ${livro.autor}`;
      return item;
    }),
  );
}

export function iniciar() {
  document.getElementById("form-livro").addEventListener("submit", aoCadastrarLivro);
  document.getElementById("form-leitor").addEventListener("submit", aoCadastrarLeitor);
  document.getElementById("form-emprestimo").addEventListener("submit", aoEmprestar);
  document.getElementById("form-devolucao").addEventListener("submit", aoDevolver);
  document.getElementById("form-busca").addEventListener("submit", aoBuscar);
}

if (typeof document !== "undefined") {
  iniciar();
}
