import pytest

from biblioteca.servicos import ErroBiblioteca, ServicoBiblioteca
from fakes import RepositorioMemoria


def test_cadastra_leitor():
    servico = ServicoBiblioteca(RepositorioMemoria())
    leitor = servico.cadastrar_leitor("Ana", "ana@exemplo.com")
    assert leitor.nome == "Ana"


def test_rf02_rejeita_email_invalido():
    servico = ServicoBiblioteca(RepositorioMemoria())
    with pytest.raises(ErroBiblioteca):
        servico.cadastrar_leitor("Ana", "email-invalido")
