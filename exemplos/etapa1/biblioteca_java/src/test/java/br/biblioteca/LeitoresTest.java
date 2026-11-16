package br.biblioteca;

import br.biblioteca.modelo.Leitor;
import br.biblioteca.servico.ErroBiblioteca;
import br.biblioteca.servico.ServicoBiblioteca;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class LeitoresTest {
    @Test
    void cadastraLeitor() {
        ServicoBiblioteca servico = new ServicoBiblioteca(new RepositorioMemoria());
        Leitor leitor = servico.cadastrarLeitor("Ana", "ana@exemplo.com");
        assertEquals("Ana", leitor.nome());
    }

    @Test
    void rf02RejeitaEmailInvalido() {
        ServicoBiblioteca servico = new ServicoBiblioteca(new RepositorioMemoria());
        assertThrows(ErroBiblioteca.class, () -> servico.cadastrarLeitor("Ana", "email-invalido"));
    }
}
