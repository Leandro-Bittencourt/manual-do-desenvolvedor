from biblioteca.servicos import ServicoBiblioteca
from fakes import RepositorioMemoria


def test_busca_por_titulo_ou_autor_sem_diferenciar_maiusculas():
    servico = ServicoBiblioteca(RepositorioMemoria())
    servico.cadastrar_livro("9780306406157", "Dom Casmurro", "Machado de Assis")
    servico.cadastrar_livro("9781861972712", "Vidas Secas", "Graciliano Ramos")
    assert [l.titulo for l in servico.buscar_livros("casmurro")] == ["Dom Casmurro"]
    assert [l.titulo for l in servico.buscar_livros("GRACILIANO")] == ["Vidas Secas"]
