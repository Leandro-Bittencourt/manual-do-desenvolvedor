from loja.carrinho import Carrinho
from loja.pagamento import processar_pagamento


def test_pagamento_aprovado_com_cartao_valido():
    carrinho = Carrinho()
    carrinho.adicionar("livro", 40.0)
    comprovante = processar_pagamento(carrinho, "4539 1488 0343 6467")
    assert comprovante["aprovado"]


def test_cartao_invalido_recusado():
    carrinho = Carrinho()
    carrinho.adicionar("livro", 40.0)
    comprovante = processar_pagamento(carrinho, "1234")
    assert not comprovante["aprovado"]
