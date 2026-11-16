package br.biblioteca;

import br.biblioteca.modelo.Emprestimo;
import br.biblioteca.modelo.Leitor;
import br.biblioteca.modelo.Livro;
import br.biblioteca.repositorio.Repositorio;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Repositório em memória usado nos testes (substitui o Neo4j). */
public class RepositorioMemoria implements Repositorio {
    private final Map<String, Livro> livros = new LinkedHashMap<>();
    private final Map<String, Leitor> leitores = new LinkedHashMap<>();
    private final List<Emprestimo> emprestimos = new ArrayList<>();

    @Override public void salvarLivro(Livro livro) { livros.put(livro.getIsbn(), livro); }
    @Override public Optional<Livro> buscarLivro(String isbn) { return Optional.ofNullable(livros.get(isbn)); }
    @Override public List<Livro> listarLivros() {
        return livros.values().stream().sorted(Comparator.comparing(Livro::getTitulo)).toList();
    }
    @Override public void salvarLeitor(Leitor leitor) { leitores.put(leitor.email(), leitor); }
    @Override public void salvarEmprestimo(Emprestimo e) { if (!emprestimos.contains(e)) emprestimos.add(e); }
    @Override public List<Emprestimo> emprestimosAtivos(String email) {
        return emprestimos.stream().filter(e -> e.getEmailLeitor().equals(email) && e.isAtivo()).toList();
    }
    @Override public Optional<Emprestimo> emprestimoAberto(String isbn) {
        return emprestimos.stream().filter(e -> e.getIsbn().equals(isbn) && e.isAtivo()).findFirst();
    }
}
