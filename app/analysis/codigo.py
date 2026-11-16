"""Etapa 2 — Leitura do código-fonte e dos casos de teste.

Este módulo escolhe o leitor de cada arquivo pela extensão e implementa o
leitor de Python:

* funções, classes, métodos, *docstrings*, chamadas e importações são
  extraídos com o módulo nativo ``ast`` (árvore sintática abstrata);
* comentários são obtidos com o módulo nativo ``tokenize``, pois a árvore
  sintática os descarta;
* casos de teste são reconhecidos pelas convenções do ``pytest`` e do
  ``unittest``: arquivos ``test_*.py`` ou ``*_test.py``, funções iniciadas
  por ``test`` e classes iniciadas por ``Test`` ou derivadas de ``TestCase``.

Java e JavaScript são lidos com tree-sitter (``codigo_java``, ``codigo_js``)
e HTML com ``html.parser`` (``codigo_html``). O código é apenas lido; nada é
executado.
"""

from __future__ import annotations

import ast
import io
import tokenize
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .codigo_base import (
    atribuir_comentarios,
    chave_codigo,
    chave_teste,
    eh_arquivo_de_producao,
    eh_arquivo_de_teste,
    hash_trecho,
    linguagem_de,
    modulo_de,
)
from .modelos import (
    TIPO_CLASSE,
    TIPO_FUNCAO,
    TIPO_METODO,
    TIPO_TESTE,
    Artefato,
    Chamada,
)


def nome_pontuado(no: ast.AST) -> str | None:
    """Converte o alvo de uma chamada em texto: ``a.b.c``, ``Classe`` etc."""
    if isinstance(no, ast.Name):
        return no.id
    if isinstance(no, ast.Attribute):
        base = nome_pontuado(no.value)
        return f"{base}.{no.attr}" if base else f"?.{no.attr}"
    if isinstance(no, ast.Call):
        base = nome_pontuado(no.func)
        return f"{base}()" if base else None
    return None


def _importacoes(arvore: ast.Module, modulo: str) -> dict[str, str]:
    """Mapeia nomes locais para o caminho importado (``Carrinho`` -> ``loja.carrinho.Carrinho``)."""
    pacote = modulo.rsplit(".", 1)[0] if "." in modulo else ""
    mapa: dict[str, str] = {}
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                if alias.asname:
                    mapa[alias.asname] = alias.name
                else:
                    raiz = alias.name.split(".")[0]
                    mapa[raiz] = raiz
        elif isinstance(no, ast.ImportFrom):
            base = no.module or ""
            if no.level:
                partes = pacote.split(".") if pacote else []
                partes = partes[: len(partes) - (no.level - 1)] if no.level > 1 else partes
                base = ".".join(p for p in [*partes, base] if p)
            for alias in no.names:
                if alias.name == "*":
                    continue
                mapa[alias.asname or alias.name] = f"{base}.{alias.name}" if base else alias.name
    return mapa


def _comentarios(fonte: str) -> list[tuple[int, str]]:
    comentarios = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(fonte).readline):
            if token.type == tokenize.COMMENT:
                texto = token.string.lstrip("#").strip()
                if texto:
                    comentarios.append((token.start[0], texto))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return comentarios


@dataclass
class _Escopo:
    tipo: str  # "classe" ou "funcao"
    nome: str
    eh_classe_de_teste: bool = False


class _Visitante(ast.NodeVisitor):
    def __init__(self, arquivo: str, linhas: list[str], eh_teste: bool, modulo: str, importacoes: dict[str, str]):
        self.arquivo = arquivo
        self.linhas = linhas
        self.eh_teste = eh_teste
        self.modulo = modulo
        self.importacoes = importacoes
        self.pilha: list[_Escopo] = []
        self.artefatos: list[Artefato] = []

    # -- utilidades -------------------------------------------------------
    def _qualificado(self, nome: str) -> str:
        return ".".join([*(e.nome for e in self.pilha), nome])

    def _intervalo(self, no) -> tuple[int, int]:
        inicio = min([no.lineno, *(d.lineno for d in getattr(no, "decorator_list", []))])
        fim = getattr(no, "end_lineno", None) or no.lineno
        return inicio, fim

    def _hash(self, inicio: int, fim: int) -> str:
        return hash_trecho(self.linhas, inicio, fim)

    @staticmethod
    def _chamadas(no) -> list[Chamada]:
        chamadas = []
        for filho in ast.walk(no):
            if isinstance(filho, ast.Call):
                alvo = nome_pontuado(filho.func)
                if alvo:
                    chamadas.append(Chamada(alvo=alvo, linha=filho.lineno))
        return chamadas

    @staticmethod
    def _termos(no) -> list[str]:
        termos = []
        for filho in ast.walk(no):
            if isinstance(filho, ast.Name):
                termos.append(filho.id)
            elif isinstance(filho, ast.Attribute):
                termos.append(filho.attr)
            elif isinstance(filho, ast.arg):
                termos.append(filho.arg)
        return termos

    def _criar(self, no, tipo: str) -> Artefato:
        qualificado = self._qualificado(no.name)
        inicio, fim = self._intervalo(no)
        chave = chave_teste(self.arquivo, qualificado) if tipo == TIPO_TESTE else chave_codigo(self.arquivo, qualificado)
        artefato = Artefato(
            chave=chave,
            tipo=tipo,
            identificador=qualificado,
            nome=no.name,
            arquivo=self.arquivo,
            linha_inicio=inicio,
            linha_fim=fim,
            hash=self._hash(inicio, fim),
            modulo=self.modulo,
            docstring=ast.get_docstring(no) or "",
            chamadas=self._chamadas(no) if tipo != TIPO_CLASSE else [],
            termos=self._termos(no),
            importacoes=self.importacoes,
        )
        self.artefatos.append(artefato)
        return artefato

    # -- visitantes -------------------------------------------------------
    def visit_ClassDef(self, no: ast.ClassDef) -> None:
        if any(e.tipo == "funcao" for e in self.pilha):
            return  # classes internas a funções não são analisadas
        if self.eh_teste:
            bases = [nome_pontuado(b) or "" for b in no.bases]
            eh_classe_de_teste = no.name.startswith("Test") or any(b.endswith("TestCase") for b in bases)
        else:
            eh_classe_de_teste = False
            self._criar(no, TIPO_CLASSE)
        self.pilha.append(_Escopo("classe", no.name, eh_classe_de_teste))
        self.generic_visit(no)
        self.pilha.pop()

    def _visitar_funcao(self, no) -> None:
        if any(e.tipo == "funcao" for e in self.pilha):
            return  # funções internas pertencem à função externa
        dentro_de_classe = bool(self.pilha) and self.pilha[-1].tipo == "classe"
        if self.eh_teste:
            classe_ok = not dentro_de_classe or self.pilha[-1].eh_classe_de_teste
            if no.name.startswith("test") and classe_ok:
                self._criar(no, TIPO_TESTE)
        else:
            self._criar(no, TIPO_METODO if dentro_de_classe else TIPO_FUNCAO)
        self.pilha.append(_Escopo("funcao", no.name))
        self.generic_visit(no)
        self.pilha.pop()

    visit_FunctionDef = _visitar_funcao
    visit_AsyncFunctionDef = _visitar_funcao


def analisar_python(raiz: Path, relativo: str) -> tuple[list[Artefato], str | None]:
    """Analisa um arquivo Python. Devolve os artefatos e, se houver, um aviso."""
    fonte = (Path(raiz) / relativo).read_text(encoding="utf-8-sig", errors="replace")
    try:
        arvore = ast.parse(fonte, filename=relativo)
    except SyntaxError as erro:
        return [], f"{relativo}: erro de sintaxe na linha {erro.lineno}; o arquivo foi ignorado."

    modulo = modulo_de(relativo)
    linhas = fonte.splitlines()
    visitante = _Visitante(relativo, linhas, eh_arquivo_de_teste(relativo), modulo, _importacoes(arvore, modulo))
    visitante.visit(arvore)
    comentarios = [(linha, linha, texto) for linha, texto in _comentarios(fonte)]
    atribuir_comentarios(visitante.artefatos, comentarios, linhas)
    return visitante.artefatos, None


def _leitores():
    # importação tardia: o tree-sitter só é carregado quando necessário
    from .codigo_html import analisar_html
    from .codigo_java import analisar_java
    from .codigo_js import analisar_javascript

    return {"python": analisar_python, "java": analisar_java, "javascript": analisar_javascript, "html": analisar_html}


def analisar_arquivo(raiz: Path, relativo: str) -> tuple[list[Artefato], str | None]:
    leitor = _leitores().get(linguagem_de(relativo))
    if leitor is None:
        return [], None
    try:
        return leitor(raiz, relativo)
    except (UnicodeError, ValueError, RecursionError) as erro:
        return [], f"{relativo}: não foi possível analisar o arquivo ({erro}); ele foi ignorado."


def analisar_codigo(raiz: Path, arquivos: list[str]) -> tuple[list[Artefato], list[str], dict[str, int]]:
    """Analisa os arquivos de produção e de teste de todas as linguagens suportadas.

    Devolve os artefatos, os avisos e a quantidade de arquivos lidos por linguagem.
    """
    artefatos: list[Artefato] = []
    avisos: list[str] = []
    por_linguagem: Counter[str] = Counter()
    for relativo in sorted(arquivos):
        if not (eh_arquivo_de_teste(relativo) or eh_arquivo_de_producao(relativo)):
            continue
        encontrados, aviso = analisar_arquivo(raiz, relativo)
        por_linguagem[linguagem_de(relativo)] += 1
        artefatos.extend(encontrados)
        if aviso:
            avisos.append(aviso)
    return artefatos, avisos, dict(por_linguagem)


__all__ = [
    "TIPO_FUNCAO",
    "analisar_arquivo",
    "analisar_codigo",
    "analisar_python",
    "chave_codigo",
    "chave_teste",
    "eh_arquivo_de_producao",
    "eh_arquivo_de_teste",
    "hash_trecho",
    "modulo_de",
]
