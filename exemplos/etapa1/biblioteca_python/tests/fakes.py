"""Repositório em memória usado nos testes (substitui o PostgreSQL)."""


class RepositorioMemoria:
    def __init__(self):
        self.livros, self.leitores, self.emprestimos = {}, {}, []

    def salvar_livro(self, livro):
        self.livros[livro.isbn] = livro

    def buscar_livro(self, isbn):
        return self.livros.get(isbn)

    def listar_livros(self):
        return sorted(self.livros.values(), key=lambda l: l.titulo)

    def salvar_leitor(self, leitor):
        self.leitores[leitor.email] = leitor

    def buscar_leitor(self, email):
        return self.leitores.get(email)

    def salvar_emprestimo(self, emprestimo):
        if emprestimo not in self.emprestimos:
            self.emprestimos.append(emprestimo)

    def emprestimos_ativos(self, email_leitor):
        return [e for e in self.emprestimos if e.email_leitor == email_leitor and e.data_devolucao is None]

    def emprestimo_aberto(self, isbn):
        return next((e for e in self.emprestimos if e.isbn == isbn and e.data_devolucao is None), None)
