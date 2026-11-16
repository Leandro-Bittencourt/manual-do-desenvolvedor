const UM_DIA_MS = 24 * 60 * 60 * 1000;

export class Livro {
  constructor(isbn, titulo, autor, disponivel = true) {
    this.isbn = isbn;
    this.titulo = titulo;
    this.autor = autor;
    this.disponivel = disponivel;
  }
}

export class Leitor {
  constructor(email, nome) {
    this.email = email;
    this.nome = nome;
  }
}

export class Emprestimo {
  constructor(isbn, emailLeitor, dataEmprestimo, dataDevolucao = null) {
    this.isbn = isbn;
    this.emailLeitor = emailLeitor;
    this.dataEmprestimo = dataEmprestimo;
    this.dataDevolucao = dataDevolucao;
  }

  /** Quantidade de dias de atraso em relação ao prazo de devolução. */
  diasDeAtraso(dataDevolucao, prazoDias = 14) {
    const dias = Math.round((dataDevolucao - this.dataEmprestimo) / UM_DIA_MS) - prazoDias;
    return Math.max(dias, 0);
  }
}
