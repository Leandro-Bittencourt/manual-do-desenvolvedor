import { MongoClient } from "mongodb";
import { Emprestimo, Livro } from "./modelos.js";

/**
 * Grava livros, leitores e empréstimos no banco de dados de documentos MongoDB,
 * nas coleções "livros", "leitores" e "emprestimos".
 */
export class RepositorioMongo {
  constructor(url, nomeBanco = "biblioteca") {
    this.cliente = new MongoClient(url);
    this.banco = this.cliente.db(nomeBanco);
  }

  async salvarLivro(livro) {
    await this.banco.collection("livros").updateOne({ isbn: livro.isbn }, { $set: { ...livro } }, { upsert: true });
  }

  async buscarLivro(isbn) {
    const doc = await this.banco.collection("livros").findOne({ isbn });
    return doc ? new Livro(doc.isbn, doc.titulo, doc.autor, doc.disponivel) : null;
  }

  async listarLivros() {
    const docs = await this.banco.collection("livros").find().sort({ titulo: 1 }).toArray();
    return docs.map((d) => new Livro(d.isbn, d.titulo, d.autor, d.disponivel));
  }

  async salvarLeitor(leitor) {
    await this.banco.collection("leitores").insertOne({ ...leitor });
  }

  async salvarEmprestimo(emprestimo) {
    await this.banco.collection("emprestimos").updateOne(
      { isbn: emprestimo.isbn, dataEmprestimo: emprestimo.dataEmprestimo },
      { $set: { ...emprestimo } },
      { upsert: true },
    );
  }

  async emprestimosAtivos(emailLeitor) {
    const docs = await this.banco.collection("emprestimos").find({ emailLeitor, dataDevolucao: null }).toArray();
    return docs.map((d) => new Emprestimo(d.isbn, d.emailLeitor, d.dataEmprestimo));
  }

  async emprestimoAberto(isbn) {
    const d = await this.banco.collection("emprestimos").findOne({ isbn, dataDevolucao: null });
    return d ? new Emprestimo(d.isbn, d.emailLeitor, d.dataEmprestimo) : null;
  }
}
