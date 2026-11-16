package br.biblioteca.repositorio;

import br.biblioteca.modelo.Emprestimo;
import br.biblioteca.modelo.Leitor;
import br.biblioteca.modelo.Livro;
import org.neo4j.driver.Driver;
import org.neo4j.driver.Record;
import org.neo4j.driver.Session;
import org.neo4j.driver.Values;

import java.util.List;
import java.util.Optional;

/**
 * Grava livros, leitores e empréstimos no banco de dados de grafo Neo4j.
 * Livros e leitores são nós; o empréstimo é a relação (:Leitor)-[:EMPRESTOU]->(:Livro).
 */
public class RepositorioNeo4j implements Repositorio {
    private final Driver driver;

    public RepositorioNeo4j(Driver driver) {
        this.driver = driver;
    }

    @Override
    public void salvarLivro(Livro livro) {
        try (Session sessao = driver.session()) {
            sessao.run("MERGE (l:Livro {isbn: $isbn}) SET l.titulo = $titulo, l.autor = $autor, l.disponivel = $disponivel",
                    Values.parameters("isbn", livro.getIsbn(), "titulo", livro.getTitulo(),
                            "autor", livro.getAutor(), "disponivel", livro.isDisponivel()));
        }
    }

    @Override
    public Optional<Livro> buscarLivro(String isbn) {
        try (Session sessao = driver.session()) {
            var resultado = sessao.run("MATCH (l:Livro {isbn: $isbn}) RETURN l", Values.parameters("isbn", isbn));
            return resultado.hasNext() ? Optional.of(paraLivro(resultado.next())) : Optional.empty();
        }
    }

    @Override
    public List<Livro> listarLivros() {
        try (Session sessao = driver.session()) {
            return sessao.run("MATCH (l:Livro) RETURN l ORDER BY l.titulo").list(this::paraLivro);
        }
    }

    @Override
    public void salvarLeitor(Leitor leitor) {
        try (Session sessao = driver.session()) {
            sessao.run("MERGE (p:Leitor {email: $email}) SET p.nome = $nome",
                    Values.parameters("email", leitor.email(), "nome", leitor.nome()));
        }
    }

    @Override
    public void salvarEmprestimo(Emprestimo emprestimo) {
        try (Session sessao = driver.session()) {
            sessao.run("MATCH (p:Leitor {email: $email}), (l:Livro {isbn: $isbn}) "
                            + "MERGE (p)-[e:EMPRESTOU {data: $data}]->(l) SET e.devolucao = $devolucao",
                    Values.parameters("email", emprestimo.getEmailLeitor(), "isbn", emprestimo.getIsbn(),
                            "data", emprestimo.getDataEmprestimo(), "devolucao", emprestimo.getDataDevolucao()));
        }
    }

    @Override
    public List<Emprestimo> emprestimosAtivos(String emailLeitor) {
        try (Session sessao = driver.session()) {
            return sessao.run("MATCH (p:Leitor {email: $email})-[e:EMPRESTOU]->(l:Livro) WHERE e.devolucao IS NULL "
                            + "RETURN l.isbn AS isbn, e.data AS data", Values.parameters("email", emailLeitor))
                    .list(r -> new Emprestimo(r.get("isbn").asString(), emailLeitor, r.get("data").asLocalDate()));
        }
    }

    @Override
    public Optional<Emprestimo> emprestimoAberto(String isbn) {
        try (Session sessao = driver.session()) {
            var resultado = sessao.run("MATCH (p:Leitor)-[e:EMPRESTOU]->(l:Livro {isbn: $isbn}) WHERE e.devolucao IS NULL "
                    + "RETURN p.email AS email, e.data AS data", Values.parameters("isbn", isbn));
            if (!resultado.hasNext()) {
                return Optional.empty();
            }
            Record r = resultado.next();
            return Optional.of(new Emprestimo(isbn, r.get("email").asString(), r.get("data").asLocalDate()));
        }
    }

    private Livro paraLivro(Record registro) {
        var no = registro.get("l");
        Livro livro = new Livro(no.get("isbn").asString(), no.get("titulo").asString(), no.get("autor").asString());
        livro.setDisponivel(no.get("disponivel").asBoolean());
        return livro;
    }
}
