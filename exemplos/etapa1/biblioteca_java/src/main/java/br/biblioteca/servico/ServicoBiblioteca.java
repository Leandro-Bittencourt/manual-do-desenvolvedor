package br.biblioteca.servico;

import br.biblioteca.modelo.Emprestimo;
import br.biblioteca.modelo.Leitor;
import br.biblioteca.modelo.Livro;
import br.biblioteca.repositorio.Repositorio;

import java.time.LocalDate;
import java.util.List;

import static br.biblioteca.servico.Validacoes.calcularMulta;
import static br.biblioteca.servico.Validacoes.validarEmail;
import static br.biblioteca.servico.Validacoes.validarIsbn;

public class ServicoBiblioteca {
    private static final int LIMITE_EMPRESTIMOS = 3;
    private static final int PRAZO_DIAS = 14;
    private final Repositorio repositorio;

    public ServicoBiblioteca(Repositorio repositorio) {
        this.repositorio = repositorio;
    }

    // @traces RF-01
    public Livro cadastrarLivro(String isbn, String titulo, String autor) {
        if (!validarIsbn(isbn)) {
            throw new ErroBiblioteca("ISBN inválido");
        }
        if (repositorio.buscarLivro(isbn).isPresent()) {
            throw new ErroBiblioteca("ISBN já cadastrado");
        }
        Livro livro = new Livro(isbn, titulo, autor);
        repositorio.salvarLivro(livro);
        return livro;
    }

    /** Cadastra o leitor após validar o e-mail. */
    public Leitor cadastrarLeitor(String nome, String email) {
        if (!validarEmail(email)) {
            throw new ErroBiblioteca("E-mail inválido");
        }
        Leitor leitor = new Leitor(email, nome);
        repositorio.salvarLeitor(leitor);
        return leitor;
    }

    // @traces RF-03
    public Emprestimo emprestar(String isbn, String emailLeitor, LocalDate hoje) {
        Livro livro = repositorio.buscarLivro(isbn)
                .filter(Livro::isDisponivel)
                .orElseThrow(() -> new ErroBiblioteca("Livro indisponível"));
        if (repositorio.emprestimosAtivos(emailLeitor).size() >= LIMITE_EMPRESTIMOS) {
            throw new ErroBiblioteca("Limite de empréstimos atingido");
        }
        livro.setDisponivel(false);
        Emprestimo emprestimo = new Emprestimo(isbn, emailLeitor, hoje);
        repositorio.salvarLivro(livro);
        repositorio.salvarEmprestimo(emprestimo);
        return emprestimo;
    }

    /** Registra a devolução do livro e devolve o valor da multa. */
    public double devolver(String isbn, LocalDate hoje) {
        Emprestimo emprestimo = repositorio.emprestimoAberto(isbn)
                .orElseThrow(() -> new ErroBiblioteca("Empréstimo não encontrado"));
        emprestimo.setDataDevolucao(hoje);
        Livro livro = repositorio.buscarLivro(isbn).orElseThrow();
        livro.setDisponivel(true);
        repositorio.salvarEmprestimo(emprestimo);
        repositorio.salvarLivro(livro);
        return calcularMulta(emprestimo.diasDeAtraso(hoje, PRAZO_DIAS));
    }

    /** Busca livros pelo título ou pelo autor, sem diferenciar maiúsculas. */
    public List<Livro> buscarLivros(String termo) {
        String procurado = termo.toLowerCase();
        return repositorio.listarLivros().stream()
                .filter(l -> l.getTitulo().toLowerCase().contains(procurado)
                        || l.getAutor().toLowerCase().contains(procurado))
                .toList();
    }
}
