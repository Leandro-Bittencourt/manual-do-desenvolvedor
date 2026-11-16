package br.biblioteca;

import br.biblioteca.modelo.Livro;
import br.biblioteca.servico.ServicoBiblioteca;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class BuscaTest {
    @Test
    void buscaPorTituloOuAutorSemDiferenciarMaiusculas() {
        ServicoBiblioteca servico = new ServicoBiblioteca(new RepositorioMemoria());
        servico.cadastrarLivro("9780306406157", "Dom Casmurro", "Machado de Assis");
        servico.cadastrarLivro("9781861972712", "Vidas Secas", "Graciliano Ramos");
        assertEquals(List.of("Dom Casmurro"), servico.buscarLivros("casmurro").stream().map(Livro::getTitulo).toList());
        assertEquals(List.of("Vidas Secas"), servico.buscarLivros("GRACILIANO").stream().map(Livro::getTitulo).toList());
    }
}
