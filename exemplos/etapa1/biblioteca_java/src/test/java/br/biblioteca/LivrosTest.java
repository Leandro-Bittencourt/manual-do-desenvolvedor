package br.biblioteca;

import br.biblioteca.modelo.Livro;
import br.biblioteca.servico.ErroBiblioteca;
import br.biblioteca.servico.ServicoBiblioteca;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class LivrosTest {
    private static final String ISBN_VALIDO = "9780306406157";

    @Test
    void rf01CadastraLivroComIsbnValido() {
        ServicoBiblioteca servico = new ServicoBiblioteca(new RepositorioMemoria());
        Livro livro = servico.cadastrarLivro(ISBN_VALIDO, "Dom Casmurro", "Machado de Assis");
        assertTrue(livro.isDisponivel());
    }

    @Test
    void rejeitaIsbnInvalido() {
        ServicoBiblioteca servico = new ServicoBiblioteca(new RepositorioMemoria());
        assertThrows(ErroBiblioteca.class, () -> servico.cadastrarLivro("123", "Livro", "Autor"));
    }

    @Test
    void rejeitaIsbnRepetido() {
        // RF-01: não pode haver dois livros com o mesmo ISBN
        ServicoBiblioteca servico = new ServicoBiblioteca(new RepositorioMemoria());
        servico.cadastrarLivro(ISBN_VALIDO, "Dom Casmurro", "Machado de Assis");
        assertThrows(ErroBiblioteca.class, () -> servico.cadastrarLivro(ISBN_VALIDO, "Outro", "Outro autor"));
    }
}
