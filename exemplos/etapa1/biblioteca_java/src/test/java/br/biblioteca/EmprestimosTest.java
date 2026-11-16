package br.biblioteca;

import br.biblioteca.servico.ErroBiblioteca;
import br.biblioteca.servico.ServicoBiblioteca;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;

class EmprestimosTest {
    private static final List<String> ISBNS = List.of("9780306406157", "9781861972712", "9780131103627", "9780201633610");
    private static final LocalDate HOJE = LocalDate.of(2026, 11, 1);
    private final RepositorioMemoria repositorio = new RepositorioMemoria();
    private final ServicoBiblioteca servico = new ServicoBiblioteca(repositorio);

    private void prepararAcervo() {
        for (int i = 0; i < ISBNS.size(); i++) {
            servico.cadastrarLivro(ISBNS.get(i), "Livro " + i, "Autor " + i);
        }
        servico.cadastrarLeitor("Ana", "ana@exemplo.com");
    }

    @Test
    void emprestaLivroDisponivel() {
        // @traces RF-03
        prepararAcervo();
        servico.emprestar(ISBNS.get(0), "ana@exemplo.com", HOJE);
        assertFalse(repositorio.buscarLivro(ISBNS.get(0)).orElseThrow().isDisponivel());
    }

    @Test
    void limiteDeTresEmprestimosAtivos() {
        prepararAcervo();
        for (int i = 0; i < 3; i++) {
            servico.emprestar(ISBNS.get(i), "ana@exemplo.com", HOJE);
        }
        assertThrows(ErroBiblioteca.class, () -> servico.emprestar(ISBNS.get(3), "ana@exemplo.com", HOJE));
    }

    @Test
    void devolucaoNoPrazoNaoGeraMulta() {
        // @traces RF-04
        prepararAcervo();
        servico.emprestar(ISBNS.get(0), "ana@exemplo.com", HOJE);
        assertEquals(0.0, servico.devolver(ISBNS.get(0), HOJE.plusDays(14)));
    }

    @Test
    void multaPorDiasDeAtraso() {
        prepararAcervo();
        servico.emprestar(ISBNS.get(0), "ana@exemplo.com", HOJE);
        assertEquals(6.0, servico.devolver(ISBNS.get(0), HOJE.plusDays(17)));
    }
}
