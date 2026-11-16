package br.biblioteca.modelo;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

public class Emprestimo {
    private final String isbn;
    private final String emailLeitor;
    private final LocalDate dataEmprestimo;
    private LocalDate dataDevolucao;

    public Emprestimo(String isbn, String emailLeitor, LocalDate dataEmprestimo) {
        this.isbn = isbn;
        this.emailLeitor = emailLeitor;
        this.dataEmprestimo = dataEmprestimo;
    }

    /** Quantidade de dias de atraso em relação ao prazo de devolução. */
    public long diasDeAtraso(LocalDate dataDevolucao, int prazoDias) {
        long dias = ChronoUnit.DAYS.between(dataEmprestimo, dataDevolucao) - prazoDias;
        return Math.max(dias, 0);
    }

    public String getIsbn() { return isbn; }
    public String getEmailLeitor() { return emailLeitor; }
    public LocalDate getDataEmprestimo() { return dataEmprestimo; }
    public LocalDate getDataDevolucao() { return dataDevolucao; }
    public void setDataDevolucao(LocalDate dataDevolucao) { this.dataDevolucao = dataDevolucao; }
    public boolean isAtivo() { return dataDevolucao == null; }
}
