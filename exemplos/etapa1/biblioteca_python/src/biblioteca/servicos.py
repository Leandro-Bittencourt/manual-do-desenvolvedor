import re
from datetime import date

from .modelos import Emprestimo, Leitor, Livro

LIMITE_EMPRESTIMOS = 3
VALOR_MULTA_DIA = 2.0


class ErroBiblioteca(Exception):
    pass


class ServicoBiblioteca:
    def __init__(self, repositorio):
        self.repositorio = repositorio

    # @traces RF-01
    def cadastrar_livro(self, isbn: str, titulo: str, autor: str) -> Livro:
        if not validar_isbn(isbn):
            raise ErroBiblioteca("ISBN inválido")
        if self.repositorio.buscar_livro(isbn):
            raise ErroBiblioteca("ISBN já cadastrado")
        livro = Livro(isbn, titulo, autor)
        self.repositorio.salvar_livro(livro)
        return livro

    def cadastrar_leitor(self, nome: str, email: str) -> Leitor:
        """Cadastra o leitor após validar o e-mail."""
        if not validar_email(email):
            raise ErroBiblioteca("E-mail inválido")
        leitor = Leitor(email, nome)
        self.repositorio.salvar_leitor(leitor)
        return leitor

    # @traces RF-03
    def emprestar(self, isbn: str, email_leitor: str, hoje: date) -> Emprestimo:
        livro = self.repositorio.buscar_livro(isbn)
        if livro is None or not livro.disponivel:
            raise ErroBiblioteca("Livro indisponível")
        if len(self.repositorio.emprestimos_ativos(email_leitor)) >= LIMITE_EMPRESTIMOS:
            raise ErroBiblioteca("Limite de empréstimos atingido")
        livro.disponivel = False
        emprestimo = Emprestimo(isbn, email_leitor, hoje)
        self.repositorio.salvar_livro(livro)
        self.repositorio.salvar_emprestimo(emprestimo)
        return emprestimo

    def devolver(self, isbn: str, hoje: date) -> float:
        """Registra a devolução do livro e devolve o valor da multa."""
        emprestimo = self.repositorio.emprestimo_aberto(isbn)
        if emprestimo is None:
            raise ErroBiblioteca("Empréstimo não encontrado")
        emprestimo.data_devolucao = hoje
        livro = self.repositorio.buscar_livro(isbn)
        livro.disponivel = True
        self.repositorio.salvar_emprestimo(emprestimo)
        self.repositorio.salvar_livro(livro)
        return calcular_multa(emprestimo.dias_de_atraso(hoje))

    def buscar_livros(self, termo: str) -> list[Livro]:
        """Busca livros pelo título ou pelo autor, sem diferenciar maiúsculas."""
        termo = termo.lower()
        return [
            livro for livro in self.repositorio.listar_livros()
            if termo in livro.titulo.lower() or termo in livro.autor.lower()
        ]


def validar_isbn(isbn: str) -> bool:
    """ISBN-13: 13 dígitos com dígito verificador válido."""
    digitos = [int(c) for c in isbn if c.isdigit()]
    if len(digitos) != 13:
        return False
    soma = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digitos[:12]))
    return (10 - soma % 10) % 10 == digitos[12]


def validar_email(email: str) -> bool:
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


def calcular_multa(dias_de_atraso: int) -> float:
    """Multa de R$ 2,00 por dia de atraso."""
    return dias_de_atraso * VALOR_MULTA_DIA
