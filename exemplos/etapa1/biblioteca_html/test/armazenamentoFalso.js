/** Substituto do localStorage para executar os testes fora do navegador. */
export class ArmazenamentoEmMemoria {
  constructor() {
    this.dados = new Map();
  }

  get length() { return this.dados.size; }
  key(i) { return [...this.dados.keys()][i] ?? null; }
  getItem(chave) { return this.dados.has(chave) ? this.dados.get(chave) : null; }
  setItem(chave, valor) { this.dados.set(chave, String(valor)); }
  removeItem(chave) { this.dados.delete(chave); }
}
