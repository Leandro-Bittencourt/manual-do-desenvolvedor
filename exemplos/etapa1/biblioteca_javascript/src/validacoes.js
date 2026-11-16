const VALOR_MULTA_DIA = 2.0;

/** ISBN-13: 13 dígitos com dígito verificador válido. */
export function validarIsbn(isbn) {
  const digitos = [...isbn].filter((c) => c >= "0" && c <= "9").map(Number);
  if (digitos.length !== 13) {
    return false;
  }
  const soma = digitos.slice(0, 12).reduce((total, d, i) => total + (i % 2 === 0 ? d : d * 3), 0);
  return (10 - (soma % 10)) % 10 === digitos[12];
}

export function validarEmail(email) {
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email);
}

/** Multa de R$ 2,00 por dia de atraso. */
export function calcularMulta(diasDeAtraso) {
  return diasDeAtraso * VALOR_MULTA_DIA;
}
