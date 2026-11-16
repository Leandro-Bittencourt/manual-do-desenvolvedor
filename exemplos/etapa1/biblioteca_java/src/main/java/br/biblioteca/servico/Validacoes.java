package br.biblioteca.servico;

import java.util.regex.Pattern;

public final class Validacoes {
    private static final Pattern EMAIL = Pattern.compile("[^@\\s]+@[^@\\s]+\\.[^@\\s]+");
    private static final double VALOR_MULTA_DIA = 2.0;

    private Validacoes() {
    }

    /** ISBN-13: 13 dígitos com dígito verificador válido. */
    public static boolean validarIsbn(String isbn) {
        String digitos = isbn.replaceAll("\\D", "");
        if (digitos.length() != 13) {
            return false;
        }
        int soma = 0;
        for (int i = 0; i < 12; i++) {
            int d = digitos.charAt(i) - '0';
            soma += (i % 2 == 0) ? d : d * 3;
        }
        return (10 - soma % 10) % 10 == digitos.charAt(12) - '0';
    }

    public static boolean validarEmail(String email) {
        return EMAIL.matcher(email).matches();
    }

    /** Multa de R$ 2,00 por dia de atraso. */
    public static double calcularMulta(long diasDeAtraso) {
        return diasDeAtraso * VALOR_MULTA_DIA;
    }
}
