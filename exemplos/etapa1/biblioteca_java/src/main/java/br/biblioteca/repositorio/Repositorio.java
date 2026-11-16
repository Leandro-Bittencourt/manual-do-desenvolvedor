package br.biblioteca.repositorio;

import br.biblioteca.modelo.Emprestimo;
import br.biblioteca.modelo.Leitor;
import br.biblioteca.modelo.Livro;

import java.util.List;
import java.util.Optional;

public interface Repositorio {
    void salvarLivro(Livro livro);
    Optional<Livro> buscarLivro(String isbn);
    List<Livro> listarLivros();
    void salvarLeitor(Leitor leitor);
    void salvarEmprestimo(Emprestimo emprestimo);
    List<Emprestimo> emprestimosAtivos(String emailLeitor);
    Optional<Emprestimo> emprestimoAberto(String isbn);
}
