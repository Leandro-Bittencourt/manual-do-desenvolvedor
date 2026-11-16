import { Emprestimo, Leitor, Livro } from "./modelos.js";
import { calcularMulta, validarEmail, validarIsbn } from "./validacoes.js";

const LIMITE_EMPRESTIMOS = 3;

export class ErroBiblioteca extends Error {}

export class ServicoBiblioteca {
  constructor(repositorio) {
    this.repositorio = repositorio;
  }

  // @traces RF-01
  async cadastrarLivro(isbn, titulo, autor) {
    if (!validarIsbn(isbn)) {
      throw new ErroBiblioteca("ISBN inválido");
    }
    if (await this.repositorio.buscarLivro(isbn)) {
      throw new ErroBiblioteca("ISBN já cadastrado");
    }
    const livro = new Livro(isbn, titulo, autor);
    await this.repositorio.salvarLivro(livro);
    return livro;
  }

  /** Cadastra o leitor após validar o e-mail. */
  async cadastrarLeitor(nome, email) {
    if (!validarEmail(email)) {
      throw new ErroBiblioteca("E-mail inválido");
    }
    const leitor = new Leitor(email, nome);
    await this.repositorio.salvarLeitor(leitor);
    return leitor;
  }

  // @traces RF-03
  async emprestar(isbn, emailLeitor, hoje) {
    const livro = await this.repositorio.buscarLivro(isbn);
    if (!livro || !livro.disponivel) {
      throw new ErroBiblioteca("Livro indisponível");
    }
    const ativos = await this.repositorio.emprestimosAtivos(emailLeitor);
    if (ativos.length >= LIMITE_EMPRESTIMOS) {
      throw new ErroBiblioteca("Limite de empréstimos atingido");
    }
    livro.disponivel = false;
    const emprestimo = new Emprestimo(isbn, emailLeitor, hoje);
    await this.repositorio.salvarLivro(livro);
    await this.repositorio.salvarEmprestimo(emprestimo);
    return emprestimo;
  }

  /** Registra a devolução do livro e devolve o valor da multa. */
  async devolver(isbn, hoje) {
    const emprestimo = await this.repositorio.emprestimoAberto(isbn);
    if (!emprestimo) {
      throw new ErroBiblioteca("Empréstimo não encontrado");
    }
    emprestimo.dataDevolucao = hoje;
    const livro = await this.repositorio.buscarLivro(isbn);
    livro.disponivel = true;
    await this.repositorio.salvarEmprestimo(emprestimo);
    await this.repositorio.salvarLivro(livro);
    return calcularMulta(emprestimo.diasDeAtraso(hoje));
  }

  /** Busca livros pelo título ou pelo autor, sem diferenciar maiúsculas. */
  async buscarLivros(termo) {
    const procurado = termo.toLowerCase();
    const livros = await this.repositorio.listarLivros();
    return livros.filter(
      (l) => l.titulo.toLowerCase().includes(procurado) || l.autor.toLowerCase().includes(procurado),
    );
  }
}
