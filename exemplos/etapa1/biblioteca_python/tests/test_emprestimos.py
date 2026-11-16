from datetime import date, timedelta

import pytest

from biblioteca.servicos import ErroBiblioteca, ServicoBiblioteca
from fakes import RepositorioMemoria

ISBNS = ["9780306406157", "9781861972712", "9780131103627", "9780201633610"]
HOJE = date(2026, 11, 1)


def _servico_com_livros():
    repositorio = RepositorioMemoria()
    servico = ServicoBiblioteca(repositorio)
    for i, isbn in enumerate(ISBNS):
        servico.cadastrar_livro(isbn, f"Livro {i}", f"Autor {i}")
    servico.cadastrar_leitor("Ana", "ana@exemplo.com")
    return servico, repositorio


def test_empresta_livro_disponivel():
    # @traces RF-03
    servico, repositorio = _servico_com_livros()
    servico.emprestar(ISBNS[0], "ana@exemplo.com", HOJE)
    assert repositorio.buscar_livro(ISBNS[0]).disponivel is False


def test_limite_de_tres_emprestimos_ativos():
    servico, _ = _servico_com_livros()
    for isbn in ISBNS[:3]:
        servico.emprestar(isbn, "ana@exemplo.com", HOJE)
    with pytest.raises(ErroBiblioteca):
        servico.emprestar(ISBNS[3], "ana@exemplo.com", HOJE)


def test_devolucao_no_prazo_nao_gera_multa():
    # @traces RF-04
    servico, _ = _servico_com_livros()
    servico.emprestar(ISBNS[0], "ana@exemplo.com", HOJE)
    assert servico.devolver(ISBNS[0], HOJE + timedelta(days=14)) == 0


def test_multa_por_dias_de_atraso():
    servico, _ = _servico_com_livros()
    servico.emprestar(ISBNS[0], "ana@exemplo.com", HOJE)
    assert servico.devolver(ISBNS[0], HOJE + timedelta(days=17)) == 6.0
