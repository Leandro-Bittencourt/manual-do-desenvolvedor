"""Leitura de código Java com tree-sitter.

* classes, interfaces, enums e records -> elementos do tipo ``classe``;
* métodos com corpo -> ``metodo`` (métodos abstratos e construtores são ignorados);
* em arquivos de teste, métodos anotados com ``@Test`` (JUnit) -> ``teste``;
* chamadas: ``objeto.metodo(...)`` e ``new Classe(...)``;
* importações: ``import br.app.Livro;`` -> ``Livro`` = ``br.app.Livro``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import tree_sitter_java
from tree_sitter import Language, Node, Parser

from .codigo_base import (
    atribuir_comentarios,
    chave_codigo,
    chave_teste,
    eh_arquivo_de_teste,
    hash_trecho,
    limpar_comentario,
    modulo_de,
)
from .modelos import TIPO_CLASSE, TIPO_METODO, TIPO_TESTE, Artefato, Chamada

DECLARACOES_DE_TIPO = {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration"}
ANOTACOES_DE_TESTE = {"Test", "ParameterizedTest", "RepeatedTest", "TestFactory"}


@lru_cache(maxsize=1)
def _parser() -> Parser:
    return Parser(Language(tree_sitter_java.language()))


def _texto(no: Node | None) -> str:
    return no.text.decode("utf-8", errors="replace") if no is not None else ""


def _percorrer(no: Node):
    pilha = [no]
    while pilha:
        atual = pilha.pop()
        yield atual
        pilha.extend(reversed(atual.children))


def _nome_pontuado(no: Node | None) -> str | None:
    if no is None:
        return None
    if no.type in {"identifier", "type_identifier", "this", "super"}:
        return _texto(no)
    if no.type == "field_access":
        base = _nome_pontuado(no.child_by_field_name("object"))
        campo = _texto(no.child_by_field_name("field"))
        return f"{base}.{campo}" if base else f"?.{campo}"
    if no.type == "method_invocation":
        base = _nome_chamada(no)
        return f"{base}()" if base else None
    return None


def _nome_chamada(no: Node) -> str | None:
    nome = _texto(no.child_by_field_name("name"))
    objeto = no.child_by_field_name("object")
    if objeto is None:
        return nome
    base = _nome_pontuado(objeto)
    return f"{base}.{nome}" if base else f"?.{nome}"


def _chamadas(no: Node) -> list[Chamada]:
    chamadas = []
    for filho in _percorrer(no):
        if filho.type == "method_invocation":
            alvo = _nome_chamada(filho)
            if alvo:
                chamadas.append(Chamada(alvo, filho.start_point[0] + 1))
        elif filho.type == "object_creation_expression":
            tipo = _texto(filho.child_by_field_name("type")).split("<")[0].strip()
            if tipo:
                chamadas.append(Chamada(tipo, filho.start_point[0] + 1))
    return chamadas


def _termos(no: Node) -> list[str]:
    return [_texto(f) for f in _percorrer(no) if f.type in {"identifier", "type_identifier"}]


def _anotacoes(no: Node) -> set[str]:
    nomes = set()
    for filho in no.children:
        if filho.type == "modifiers":
            for anotacao in filho.named_children:
                if anotacao.type in {"marker_annotation", "annotation"}:
                    nomes.add(_texto(anotacao.child_by_field_name("name")).split(".")[-1])
    return nomes


def _importacoes(raiz: Node) -> dict[str, str]:
    mapa = {}
    for filho in raiz.named_children:
        if filho.type != "import_declaration":
            continue
        caminho = "".join(_texto(c) for c in filho.named_children if c.type in {"scoped_identifier", "identifier"})
        if caminho and not caminho.endswith("*"):
            mapa[caminho.rsplit(".", 1)[-1]] = caminho
    return mapa


def analisar_java(raiz: Path, relativo: str) -> tuple[list[Artefato], str | None]:
    fonte = (Path(raiz) / relativo).read_bytes()
    arvore = _parser().parse(fonte)
    linhas = fonte.decode("utf-8", errors="replace").splitlines()
    eh_teste = eh_arquivo_de_teste(relativo)
    modulo = modulo_de(relativo)
    importacoes = _importacoes(arvore.root_node)
    artefatos: list[Artefato] = []

    def criar(no: Node, nome: str, qualificado: str, tipo: str) -> None:
        inicio, fim = no.start_point[0] + 1, no.end_point[0] + 1
        chave = chave_teste(relativo, qualificado) if tipo == TIPO_TESTE else chave_codigo(relativo, qualificado)
        artefatos.append(
            Artefato(
                chave=chave, tipo=tipo, identificador=qualificado, nome=nome, arquivo=relativo,
                linha_inicio=inicio, linha_fim=fim, hash=hash_trecho(linhas, inicio, fim), modulo=modulo,
                chamadas=_chamadas(no) if tipo != TIPO_CLASSE else [], termos=_termos(no),
                importacoes=importacoes,
            )
        )

    def visitar(no: Node, escopo: list[str]) -> None:
        if no.type in DECLARACOES_DE_TIPO:
            nome = _texto(no.child_by_field_name("name"))
            if not eh_teste:
                criar(no, nome, ".".join([*escopo, nome]), TIPO_CLASSE)
            corpo = no.child_by_field_name("body")
            if corpo is not None:
                for filho in corpo.named_children:
                    visitar(filho, [*escopo, nome])
        elif no.type == "method_declaration":
            if no.child_by_field_name("body") is None:
                return  # método abstrato ou de interface
            nome = _texto(no.child_by_field_name("name"))
            qualificado = ".".join([*escopo, nome])
            if eh_teste:
                if _anotacoes(no) & ANOTACOES_DE_TESTE:
                    criar(no, nome, qualificado, TIPO_TESTE)
            else:
                criar(no, nome, qualificado, TIPO_METODO)

    for filho in arvore.root_node.named_children:
        visitar(filho, [])

    comentarios = [
        (n.start_point[0] + 1, n.end_point[0] + 1, limpar_comentario(_texto(n)))
        for n in _percorrer(arvore.root_node)
        if n.type in {"line_comment", "block_comment"}
    ]
    atribuir_comentarios(artefatos, [c for c in comentarios if c[2]], linhas)

    aviso = None
    if arvore.root_node.has_error:
        aviso = f"{relativo}: há trechos com erro de sintaxe; a análise deste arquivo pode estar incompleta."
    return artefatos, aviso
