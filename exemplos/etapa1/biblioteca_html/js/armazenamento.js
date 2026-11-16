/**
 * Grava livros, leitores e empréstimos no armazenamento chave-valor do navegador
 * (localStorage). Cada registro é guardado como JSON em uma chave com prefixo:
 * "livro:<isbn>", "leitor:<email>" e "emprestimo:<isbn>:<data>".
 */
export class ArmazenamentoLocal {
  constructor(armazenamento = globalThis.localStorage) {
    this.armazenamento = armazenamento;
  }

  salvarLivro(livro) {
    this.armazenamento.setItem(`livro:${livro.isbn}`, JSON.stringify(livro));
  }

  buscarLivro(isbn) {
    const valor = this.armazenamento.getItem(`livro:${isbn}`);
    return valor ? JSON.parse(valor) : null;
  }

  listarLivros() {
    return this.valoresComPrefixo("livro:").sort((a, b) => a.titulo.localeCompare(b.titulo));
  }

  salvarLeitor(leitor) {
    this.armazenamento.setItem(`leitor:${leitor.email}`, JSON.stringify(leitor));
  }

  salvarEmprestimo(emprestimo) {
    this.armazenamento.setItem(`emprestimo:${emprestimo.isbn}:${emprestimo.dataEmprestimo}`, JSON.stringify(emprestimo));
  }

  emprestimosAtivos(emailLeitor) {
    return this.valoresComPrefixo("emprestimo:").filter((e) => e.emailLeitor === emailLeitor && !e.dataDevolucao);
  }

  emprestimoAberto(isbn) {
    return this.valoresComPrefixo(`emprestimo:${isbn}:`).find((e) => !e.dataDevolucao) ?? null;
  }

  valoresComPrefixo(prefixo) {
    const valores = [];
    for (let i = 0; i < this.armazenamento.length; i++) {
      const chave = this.armazenamento.key(i);
      if (chave.startsWith(prefixo)) {
        valores.push(JSON.parse(this.armazenamento.getItem(chave)));
      }
    }
    return valores;
  }
}
