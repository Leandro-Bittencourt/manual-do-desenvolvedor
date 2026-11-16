const LIMITE_EMPRESTIMOS = 3;
const PRAZO_DIAS = 14;
const VALOR_MULTA_DIA = 2.0;
const UM_DIA_MS = 24 * 60 * 60 * 1000;

export class ErroBiblioteca extends Error {}

/** ISBN-13: 13 dígitos com dígito verificador válido. */
export function validarIsbn(isbn) {
  const digitos = [...isbn].filter((c) => c >= "0" && c <= "9").map(Number);
  if (digitos.length !== 13) {
    return false;
  }
  const soma = digitos.slice(0, 12).reduce((total, d, i) => total + (i % 2 === 0 ? d : d * 3), 0);
  return (10 - (soma % 10)) % 10 === digitos[12];
}

export function validarEmail(email) {
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email);
}

/** Quantidade de dias de atraso em relação ao prazo de devolução. */
export function diasDeAtraso(dataEmprestimo, dataDevolucao) {
  const dias = Math.round((dataDevolucao - dataEmprestimo) / UM_DIA_MS) - PRAZO_DIAS;
  return Math.max(dias, 0);
}

/** Multa de R$ 2,00 por dia de atraso. */
export function calcularMulta(dias) {
  return dias * VALOR_MULTA_DIA;
}

export class ServicoBiblioteca {
  constructor(armazenamento) {
    this.armazenamento = armazenamento;
  }

  // @traces RF-01
  cadastrarLivro(isbn, titulo, autor) {
    if (!validarIsbn(isbn)) {
      throw new ErroBiblioteca("ISBN inválido");
    }
    if (this.armazenamento.buscarLivro(isbn)) {
      throw new ErroBiblioteca("ISBN já cadastrado");
    }
    const livro = { isbn, titulo, autor, disponivel: true };
    this.armazenamento.salvarLivro(livro);
    return livro;
  }

  /** Cadastra o leitor após validar o e-mail. */
  cadastrarLeitor(nome, email) {
    if (!validarEmail(email)) {
      throw new ErroBiblioteca("E-mail inválido");
    }
    const leitor = { email, nome };
    this.armazenamento.salvarLeitor(leitor);
    return leitor;
  }

  // @traces RF-03
  emprestar(isbn, emailLeitor, hoje) {
    const livro = this.armazenamento.buscarLivro(isbn);
    if (!livro || !livro.disponivel) {
      throw new ErroBiblioteca("Livro indisponível");
    }
    if (this.armazenamento.emprestimosAtivos(emailLeitor).length >= LIMITE_EMPRESTIMOS) {
      throw new ErroBiblioteca("Limite de empréstimos atingido");
    }
    livro.disponivel = false;
    const emprestimo = { isbn, emailLeitor, dataEmprestimo: hoje.getTime(), dataDevolucao: null };
    this.armazenamento.salvarLivro(livro);
    this.armazenamento.salvarEmprestimo(emprestimo);
    return emprestimo;
  }

  /** Registra a devolução do livro e devolve o valor da multa. */
  devolver(isbn, hoje) {
    const emprestimo = this.armazenamento.emprestimoAberto(isbn);
    if (!emprestimo) {
      throw new ErroBiblioteca("Empréstimo não encontrado");
    }
    emprestimo.dataDevolucao = hoje.getTime();
    const livro = this.armazenamento.buscarLivro(isbn);
    livro.disponivel = true;
    this.armazenamento.salvarEmprestimo(emprestimo);
    this.armazenamento.salvarLivro(livro);
    return calcularMulta(diasDeAtraso(emprestimo.dataEmprestimo, emprestimo.dataDevolucao));
  }

  /** Busca livros pelo título ou pelo autor, sem diferenciar maiúsculas. */
  buscarLivros(termo) {
    const procurado = termo.toLowerCase();
    return this.armazenamento
      .listarLivros()
      .filter((l) => l.titulo.toLowerCase().includes(procurado) || l.autor.toLowerCase().includes(procurado));
  }
}
