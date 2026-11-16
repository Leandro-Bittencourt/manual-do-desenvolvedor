"""Estruturas de dados usadas durante a análise (em memória).

Seguem o metamodelo de rastreabilidade (Figura 2 do TCC): cada requisito,
caso de teste ou elemento de código é um *artefato* (elemento rastreável),
e cada relação entre dois artefatos é sustentada por uma ou mais
*evidências*, produzidas pelas regras de rastreabilidade (estratégias).
"""

from __future__ import annotations

from dataclasses import dataclass, field

TIPO_REQUISITO = "requisito"
TIPO_TESTE = "teste"
TIPO_FUNCAO = "funcao"
TIPO_CLASSE = "classe"
TIPO_METODO = "metodo"
TIPO_INTERFACE = "interface"  # elemento de interface HTML (formulário, seção, botão...)

TIPOS_CODIGO = frozenset({TIPO_FUNCAO, TIPO_CLASSE, TIPO_METODO, TIPO_INTERFACE})


@dataclass
class Chamada:
    """Uma chamada encontrada no corpo de uma função (ex.: ``carrinho.adicionar``)."""

    alvo: str
    linha: int

    @property
    def nome(self) -> str:
        return self.alvo.rsplit(".", 1)[-1]


@dataclass
class Artefato:
    """Elemento rastreável: requisito, caso de teste ou elemento de código."""

    chave: str
    tipo: str
    identificador: str
    nome: str
    arquivo: str = ""
    linha_inicio: int | None = None
    linha_fim: int | None = None
    descricao: str = ""
    hash: str = ""
    # Dados auxiliares, usados apenas durante a análise (não são persistidos).
    modulo: str = ""
    docstring: str = ""
    comentarios: list[tuple[int, str]] = field(default_factory=list)
    chamadas: list[Chamada] = field(default_factory=list)
    termos: list[str] = field(default_factory=list)
    importacoes: dict[str, str] = field(default_factory=dict)

    @property
    def eh_requisito(self) -> bool:
        return self.tipo == TIPO_REQUISITO

    @property
    def eh_teste(self) -> bool:
        return self.tipo == TIPO_TESTE

    @property
    def eh_codigo(self) -> bool:
        return self.tipo in TIPOS_CODIGO


@dataclass
class Evidencia:
    """Justificativa de um vínculo, produzida por uma estratégia."""

    estrategia: str
    pontuacao: float
    detalhe: str


@dataclass
class ResultadoAnalise:
    artefatos: list[Artefato]
    dependencias: list[tuple[str, str]]
    vinculos: dict[tuple[str, str], list[Evidencia]]
    confiancas: dict[tuple[str, str], float]
    metricas: dict
    avisos: list[str]

    def artefato(self, chave: str) -> Artefato | None:
        for artefato in self.artefatos:
            if artefato.chave == chave:
                return artefato
        return None
