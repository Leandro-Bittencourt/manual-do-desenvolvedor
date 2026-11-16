import pytest

from loja.usuarios import CadastroUsuarios, gerar_hash_senha


def test_rf01_cadastra_usuario():
    cadastro = CadastroUsuarios()
    usuario = cadastro.cadastrar("Ana", "ana@exemplo.com", "segredo123")
    assert usuario["nome"] == "Ana"


def test_cadastro_rejeita_email_invalido():
    """O cadastro não aceita e-mail com formato inválido."""
    cadastro = CadastroUsuarios()
    with pytest.raises(ValueError):
        cadastro.cadastrar("Ana", "email-invalido", "segredo123")


def test_autentica_usuario():
    # @traces RF-02
    cadastro = CadastroUsuarios()
    cadastro.cadastrar("Ana", "ana@exemplo.com", "segredo123")
    assert cadastro.autenticar("ana@exemplo.com", "segredo123")
    assert not cadastro.autenticar("ana@exemplo.com", "errada")


def test_senha_guardada_como_hash():
    # RNF-01: a senha não pode ficar em texto puro
    cadastro = CadastroUsuarios()
    usuario = cadastro.cadastrar("Ana", "ana@exemplo.com", "segredo123")
    assert usuario["senha_hash"] == gerar_hash_senha("segredo123")
    assert usuario["senha_hash"] != "segredo123"
