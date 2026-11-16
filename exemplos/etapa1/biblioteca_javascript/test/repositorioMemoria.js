/** Repositório em memória usado nos testes (substitui o MongoDB). */
export class RepositorioMemoria {
  constructor() {
    this.livros = new Map();
    this.leitores = new Map();
    this.emprestimos = [];
  }

  async salvarLivro(livro) { this.livros.set(livro.isbn, livro); }
  async buscarLivro(isbn) { return this.livros.get(isbn) ?? null; }
  async listarLivros() { return [...this.livros.values()].sort((a, b) => a.titulo.localeCompare(b.titulo)); }
  async salvarLeitor(leitor) { this.leitores.set(leitor.email, leitor); }
  async salvarEmprestimo(e) { if (!this.emprestimos.includes(e)) this.emprestimos.push(e); }
  async emprestimosAtivos(email) { return this.emprestimos.filter((e) => e.emailLeitor === email && !e.dataDevolucao); }
  async emprestimoAberto(isbn) { return this.emprestimos.find((e) => e.isbn === isbn && !e.dataDevolucao) ?? null; }
}
