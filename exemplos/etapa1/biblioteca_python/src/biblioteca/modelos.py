from dataclasses import dataclass
from datetime import date


@dataclass
class Livro:
    isbn: str
    titulo: str
    autor: str
    disponivel: bool = True


@dataclass
class Leitor:
    email: str
    nome: str


@dataclass
class Emprestimo:
    isbn: str
    email_leitor: str
    data_emprestimo: date
    data_devolucao: date | None = None

    def dias_de_atraso(self, data_devolucao: date, prazo_dias: int = 14) -> int:
        """Quantidade de dias de atraso em relação ao prazo de devolução."""
        dias = (data_devolucao - self.data_emprestimo).days - prazo_dias
        return max(dias, 0)
