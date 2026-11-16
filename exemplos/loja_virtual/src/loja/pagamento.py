from .carrinho import Carrinho


def processar_pagamento(carrinho: Carrinho, numero_cartao: str, cupom=None):
    """Processa o pagamento do pedido e devolve o comprovante."""
    if not validar_cartao(numero_cartao):
        return {"aprovado": False, "motivo": "Cartão inválido"}
    total = carrinho.calcular_total(cupom)
    return {"aprovado": True, "valor": total}


def validar_cartao(numero_cartao: str) -> bool:
    """Verifica o número do cartão pelo algoritmo de Luhn."""
    digitos = [int(d) for d in numero_cartao if d.isdigit()]
    if len(digitos) < 13:
        return False
    soma = 0
    for posicao, digito in enumerate(reversed(digitos)):
        if posicao % 2 == 1:
            digito *= 2
            if digito > 9:
                digito -= 9
        soma += digito
    return soma % 10 == 0
