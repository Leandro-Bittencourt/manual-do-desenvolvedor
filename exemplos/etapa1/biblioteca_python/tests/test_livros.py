import pytest

from biblioteca.servicos import ErroBiblioteca, ServicoBiblioteca
from fakes import RepositorioMemoria

ISBN_VALIDO = "9780306406157"


def test_rf01_cadastra_livro_com_isbn_valido():
    servico = ServicoBiblioteca(RepositorioMemoria())
    livro = servico.cadastrar_livro(ISBN_VALIDO, "Dom Casmurro", "Machado de Assis")
    assert livro.disponivel


def test_rejeita_isbn_invalido():
    servico = ServicoBiblioteca(RepositorioMemoria())
    with pytest.raises(ErroBiblioteca):
        servico.cadastrar_livro("123", "Livro", "Autor")


def test_rejeita_isbn_repetido():
    # RF-01: não pode haver dois livros com o mesmo ISBN
    servico = ServicoBiblioteca(RepositorioMemoria())
    servico.cadastrar_livro(ISBN_VALIDO, "Dom Casmurro", "Machado de Assis")
    with pytest.raises(ErroBiblioteca):
        servico.cadastrar_livro(ISBN_VALIDO, "Outro", "Outro autor")
