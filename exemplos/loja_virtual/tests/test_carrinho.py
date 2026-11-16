from loja.carrinho import Carrinho


def test_rf03_adiciona_produto():
    carrinho = Carrinho()
    carrinho.adicionar("caneta", 2.50, quantidade=4)
    assert carrinho.itens["caneta"]["quantidade"] == 4


def test_remove_produto_do_carrinho():
    carrinho = Carrinho()
    carrinho.adicionar("caneta", 2.50)
    carrinho.remover("caneta")
    assert "caneta" not in carrinho.itens


def test_total_com_cupom():
    # @traces RF-04
    carrinho = Carrinho()
    carrinho.adicionar("livro", 50.0, quantidade=2)
    assert carrinho.calcular_total("DESCONTO10") == 90.0
