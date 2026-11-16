from app.analysis.codigo import analisar_codigo, eh_arquivo_de_producao, eh_arquivo_de_teste, modulo_de

PRODUCAO = '''import re
from .util import formatar


class Pedido:
    """Representa um pedido."""

    # @traces RF-02
    def fechar(self):
        # calcula o total do pedido
        return formatar(self.total())

    def total(self):
        return 10


def auxiliar():
    def interna():
        return 1
    return interna()
'''

TESTE = '''import unittest
from loja.pedido import Pedido


def helper():
    return Pedido()


def test_rf02_fecha_pedido():
    assert helper().fechar()


class TestPedido(unittest.TestCase):
    def setUp(self):
        self.p = Pedido()

    def test_total(self):
        self.assertEqual(self.p.total(), 10)
'''


def _analisar(tmp_path):
    (tmp_path / "loja").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "loja" / "pedido.py").write_text(PRODUCAO, encoding="utf-8")
    (tmp_path / "tests" / "test_pedido.py").write_text(TESTE, encoding="utf-8")
    (tmp_path / "tests" / "conftest.py").write_text("import pytest\n", encoding="utf-8")
    (tmp_path / "quebrado.py").write_text("def x(:\n", encoding="utf-8")
    arquivos = ["loja/pedido.py", "tests/test_pedido.py", "tests/conftest.py", "quebrado.py"]
    artefatos, avisos, por_linguagem = analisar_codigo(tmp_path, arquivos)
    assert por_linguagem == {"python": 3}  # conftest.py não é produção nem teste
    return {a.identificador: a for a in artefatos}, avisos


def test_classificacao_de_arquivos():
    assert eh_arquivo_de_teste("tests/test_app.py") and eh_arquivo_de_teste("app_test.py")
    assert eh_arquivo_de_producao("src/app.py")
    assert not eh_arquivo_de_producao("tests/helpers.py")
    assert not eh_arquivo_de_producao("conftest.py")
    assert modulo_de("src/loja/__init__.py") == "src.loja"


def test_extrai_classes_metodos_funcoes_e_testes(tmp_path):
    artefatos, _ = _analisar(tmp_path)
    tipos = {nome: a.tipo for nome, a in artefatos.items()}
    assert tipos == {
        "Pedido": "classe",
        "Pedido.fechar": "metodo",
        "Pedido.total": "metodo",
        "auxiliar": "funcao",
        "test_rf02_fecha_pedido": "teste",
        "TestPedido.test_total": "teste",
    }  # helper(), setUp() e funções internas não entram


def test_intervalo_de_linhas_e_docstring(tmp_path):
    artefatos, _ = _analisar(tmp_path)
    fechar = artefatos["Pedido.fechar"]
    assert (fechar.linha_inicio, fechar.linha_fim) == (9, 11)
    assert artefatos["Pedido"].docstring == "Representa um pedido."
    assert len(fechar.hash) == 64


def test_comentarios_vao_para_a_definicao_certa(tmp_path):
    artefatos, _ = _analisar(tmp_path)
    textos = [t for _, t in artefatos["Pedido.fechar"].comentarios]
    assert textos == ["@traces RF-02", "calcula o total do pedido"]
    assert artefatos["Pedido"].comentarios == []


def test_chamadas_e_importacoes(tmp_path):
    artefatos, _ = _analisar(tmp_path)
    fechar = artefatos["Pedido.fechar"]
    assert {c.alvo for c in fechar.chamadas} == {"formatar", "self.total"}
    assert fechar.importacoes["formatar"] == "loja.util.formatar"
    teste = artefatos["TestPedido.test_total"]
    assert "self.p.total" in {c.alvo for c in teste.chamadas}
    assert teste.importacoes["Pedido"] == "loja.pedido.Pedido"


def test_erro_de_sintaxe_gera_aviso_sem_interromper(tmp_path):
    artefatos, avisos = _analisar(tmp_path)
    assert artefatos  # os demais arquivos foram analisados
    assert any("quebrado.py" in a and "sintaxe" in a for a in avisos)
