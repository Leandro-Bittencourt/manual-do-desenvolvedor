"""Persistência em PostgreSQL (modelo relacional)."""

import psycopg

from .modelos import Emprestimo, Leitor, Livro


class RepositorioPostgres:
    """Grava livros, leitores e empréstimos nas tabelas do banco de dados PostgreSQL."""

    def __init__(self, url_conexao: str):
        self.conexao = psycopg.connect(url_conexao)

    def salvar_livro(self, livro: Livro) -> None:
        with self.conexao.cursor() as cursor:
            cursor.execute(
                "INSERT INTO livros (isbn, titulo, autor, disponivel) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (isbn) DO UPDATE SET disponivel = EXCLUDED.disponivel",
                (livro.isbn, livro.titulo, livro.autor, livro.disponivel),
            )
        self.conexao.commit()

    def buscar_livro(self, isbn: str) -> Livro | None:
        with self.conexao.cursor() as cursor:
            cursor.execute("SELECT isbn, titulo, autor, disponivel FROM livros WHERE isbn = %s", (isbn,))
            linha = cursor.fetchone()
        return Livro(*linha) if linha else None

    def listar_livros(self) -> list[Livro]:
        with self.conexao.cursor() as cursor:
            cursor.execute("SELECT isbn, titulo, autor, disponivel FROM livros ORDER BY titulo")
            return [Livro(*linha) for linha in cursor.fetchall()]

    def salvar_leitor(self, leitor: Leitor) -> None:
        with self.conexao.cursor() as cursor:
            cursor.execute("INSERT INTO leitores (email, nome) VALUES (%s, %s)", (leitor.email, leitor.nome))
        self.conexao.commit()

    def buscar_leitor(self, email: str) -> Leitor | None:
        with self.conexao.cursor() as cursor:
            cursor.execute("SELECT email, nome FROM leitores WHERE email = %s", (email,))
            linha = cursor.fetchone()
        return Leitor(*linha) if linha else None

    def salvar_emprestimo(self, emprestimo: Emprestimo) -> None:
        with self.conexao.cursor() as cursor:
            cursor.execute(
                "INSERT INTO emprestimos (isbn, email_leitor, data_emprestimo, data_devolucao) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT (isbn, data_emprestimo) "
                "DO UPDATE SET data_devolucao = EXCLUDED.data_devolucao",
                (emprestimo.isbn, emprestimo.email_leitor, emprestimo.data_emprestimo, emprestimo.data_devolucao),
            )
        self.conexao.commit()

    def emprestimos_ativos(self, email_leitor: str) -> list[Emprestimo]:
        with self.conexao.cursor() as cursor:
            cursor.execute(
                "SELECT isbn, email_leitor, data_emprestimo, data_devolucao FROM emprestimos "
                "WHERE email_leitor = %s AND data_devolucao IS NULL",
                (email_leitor,),
            )
            return [Emprestimo(*linha) for linha in cursor.fetchall()]

    def emprestimo_aberto(self, isbn: str) -> Emprestimo | None:
        with self.conexao.cursor() as cursor:
            cursor.execute(
                "SELECT isbn, email_leitor, data_emprestimo, data_devolucao FROM emprestimos "
                "WHERE isbn = %s AND data_devolucao IS NULL",
                (isbn,),
            )
            linha = cursor.fetchone()
        return Emprestimo(*linha) if linha else None
