package br.biblioteca.servico;

public class ErroBiblioteca extends RuntimeException {
    public ErroBiblioteca(String mensagem) {
        super(mensagem);
    }
}
