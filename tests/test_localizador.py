from app.analysis.localizador import casar_arquivo, extrair_quadros, extrair_teste

TRACEBACK = '''Traceback (most recent call last):
  File "C:\\Users\\dev\\loja\\tests\\test_carrinho.py", line 20, in test_total_com_cupom
    assert carrinho.calcular_total("XYZ") == 90.0
  File "C:\\Users\\dev\\loja\\src\\loja\\carrinho.py", line 23, in calcular_total
    return aplicar_desconto(subtotal, cupom)
  File "/usr/lib/python3.12/site-packages/x.py", line 5, in y
KeyError: 'XYZ'
'''


def test_extrai_quadros_do_traceback_na_ordem():
    quadros = extrair_quadros(TRACEBACK)
    assert [(q.linha, q.funcao) for q in quadros] == [(20, "test_total_com_cupom"), (23, "calcular_total"), (5, "y")]


def test_extrai_quadros_da_saida_resumida_do_pytest():
    quadros = extrair_quadros("src/loja/carrinho.py:30: KeyError")
    assert [(q.arquivo, q.linha) for q in quadros] == [("src/loja/carrinho.py", 30)]


def test_casa_caminho_absoluto_com_arquivo_do_projeto():
    arquivos = ["src/loja/carrinho.py", "tests/test_carrinho.py", "outro/carrinho.py"]
    assert casar_arquivo("C:\\Users\\dev\\loja\\src\\loja\\carrinho.py", arquivos) == "src/loja/carrinho.py"
    assert casar_arquivo("/home/dev/projeto/tests/test_carrinho.py", arquivos) == "tests/test_carrinho.py"
    assert casar_arquivo("/usr/lib/python3.12/site-packages/x.py", arquivos) is None


def test_extrai_identificador_ou_nome_de_teste():
    assert extrair_teste("FAILED tests/test_carrinho.py::test_total_com_cupom - KeyError") == (
        "tests/test_carrinho.py", "test_total_com_cupom")
    assert extrair_teste("tests/test_x.py::TestPedido::test_total[caso1]") == ("tests/test_x.py", "TestPedido.test_total")
    assert extrair_teste("test_total_com_cupom") == (None, "test_total_com_cupom")
    assert extrair_teste("isso não é um nome") is None
