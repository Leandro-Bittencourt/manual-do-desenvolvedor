"""Leitura de código JavaScript com tree-sitter.

* funções (``function f``, ``const f = () => ...``), classes e métodos;
* testes em arquivos ``*.test.js`` / ``*.spec.js``: chamadas ``test("nome", ...)``
  e ``it("nome", ...)``, com o prefixo de ``describe("grupo", ...)``;
* chamadas: ``objeto.metodo(...)`` e ``new Classe(...)``;
* seletores de interface citados no código (``"#form-livro"``,
  ``getElementById("titulo")``), usados para ligar testes e scripts ao HTML;
* importações ES (``import { f } from "./m.js"``) e CommonJS (``require``).
"""

from __future__ import annotations

import posixpath
import re
from functools import lru_cache
from pathlib import Path, PurePosixPath

import tree_sitter_javascript
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
from .modelos import TIPO_CLASSE, TIPO_FUNCAO, TIPO_METODO, TIPO_TESTE, Artefato, Chamada

FUNCOES_DE_TESTE = {"test", "it"}
FUNCOES_DE_GRUPO = {"describe", "suite", "context"}
TIPOS_FUNCAO_ANONIMA = {"arrow_function", "function_expression", "function"}
RE_SELETOR_ID = re.compile(r"#([A-Za-z][\w-]*)")
FUNCOES_DE_ID = {"getElementById"}


@lru_cache(maxsize=1)
def _parser() -> Parser:
    return Parser(Language(tree_sitter_javascript.language()))


def _texto(no: Node | None) -> str:
    return no.text.decode("utf-8", errors="replace") if no is not None else ""


def _percorrer(no: Node):
    pilha = [no]
    while pilha:
        atual = pilha.pop()
        yield atual
        pilha.extend(reversed(atual.children))


def _string(no: Node | None) -> str | None:
    if no is None or no.type not in {"string", "template_string"}:
        return None
    return _texto(no)[1:-1]


def _nome_pontuado(no: Node | None) -> str | None:
    if no is None:
        return None
    if no.type in {"identifier", "this", "super", "property_identifier"}:
        return _texto(no)
    if no.type == "member_expression":
        base = _nome_pontuado(no.child_by_field_name("object"))
        propriedade = _texto(no.child_by_field_name("property"))
        return f"{base}.{propriedade}" if base else f"?.{propriedade}"
    if no.type == "call_expression":
        base = _nome_pontuado(no.child_by_field_name("function"))
        return f"{base}()" if base else None
    if no.type in {"await_expression", "parenthesized_expression"} and no.named_children:
        return _nome_pontuado(no.named_children[0])
    return None


def _chamadas(no: Node) -> list[Chamada]:
    chamadas = []
    for filho in _percorrer(no):
        linha = filho.start_point[0] + 1
        if filho.type == "call_expression":
            alvo = _nome_pontuado(filho.child_by_field_name("function"))
            if alvo:
                chamadas.append(Chamada(alvo, linha))
                if alvo.rsplit(".", 1)[-1] in FUNCOES_DE_ID:
                    argumentos = filho.child_by_field_name("arguments")
                    primeiro = argumentos.named_children[0] if argumentos and argumentos.named_children else None
                    valor = _string(primeiro)
                    if valor:
                        chamadas.append(Chamada(f"#{valor}", linha))
        elif filho.type == "new_expression":
            alvo = _nome_pontuado(filho.child_by_field_name("constructor"))
            if alvo:
                chamadas.append(Chamada(alvo, linha))
        elif filho.type in {"string", "template_string"}:
            for seletor in RE_SELETOR_ID.findall(_texto(filho)):
                chamadas.append(Chamada(f"#{seletor}", linha))
    return chamadas


def _termos(no: Node) -> list[str]:
    tipos = {"identifier", "property_identifier", "shorthand_property_identifier"}
    return [_texto(f) for f in _percorrer(no) if f.type in tipos]


def _resolver_modulo(origem: str, relativo: str) -> str:
    """``../src/emprestimos.js`` importado de ``test/x.test.js`` -> ``src.emprestimos``."""
    if not origem.startswith("."):
        return origem  # pacote externo (ex.: "mongodb", "node:test")
    pasta = posixpath.dirname(relativo)
    caminho = posixpath.normpath(posixpath.join(pasta, origem))
    for extensao in (".js", ".mjs", ".cjs", ".jsx"):
        if caminho.endswith(extensao):
            caminho = caminho[: -len(extensao)]
    if caminho.endswith("/index"):
        caminho = caminho[: -len("/index")]
    return ".".join(p for p in PurePosixPath(caminho).parts if p not in {".", ""})


def _importacoes(raiz: Node, relativo: str) -> dict[str, str]:
    mapa: dict[str, str] = {}
    for no in _percorrer(raiz):
        if no.type == "import_statement":
            origem = _string(no.child_by_field_name("source"))
            if origem is None:
                continue
            modulo = _resolver_modulo(origem, relativo)
            for filho in _percorrer(no):
                if filho.type == "import_specifier":
                    nome = _texto(filho.child_by_field_name("name"))
                    apelido = _texto(filho.child_by_field_name("alias")) or nome
                    mapa[apelido] = f"{modulo}.{nome}"
                elif filho.type == "namespace_import":
                    identificadores = [c for c in filho.named_children if c.type == "identifier"]
                    if identificadores:
                        mapa[_texto(identificadores[0])] = modulo
                elif filho.type == "import_clause":
                    for c in filho.named_children:
                        if c.type == "identifier":  # importação padrão
                            mapa[_texto(c)] = modulo
        elif no.type == "variable_declarator":
            valor = no.child_by_field_name("value")
            if valor is None or valor.type != "call_expression":
                continue
            if _texto(valor.child_by_field_name("function")) != "require":
                continue
            argumentos = valor.child_by_field_name("arguments")
            origem = _string(argumentos.named_children[0]) if argumentos and argumentos.named_children else None
            if origem is None:
                continue
            modulo = _resolver_modulo(origem, relativo)
            nome = no.child_by_field_name("name")
            if nome is not None and nome.type == "identifier":
                mapa[_texto(nome)] = modulo
            elif nome is not None and nome.type == "object_pattern":
                for c in nome.named_children:
                    if c.type == "shorthand_property_identifier_pattern":
                        mapa[_texto(c)] = f"{modulo}.{_texto(c)}"
                    elif c.type == "pair_pattern":
                        chave = _texto(c.child_by_field_name("key"))
                        mapa[_texto(c.child_by_field_name("value"))] = f"{modulo}.{chave}"
    return mapa


def analisar_javascript(raiz: Path, relativo: str) -> tuple[list[Artefato], str | None]:
    fonte = (Path(raiz) / relativo).read_bytes()
    arvore = _parser().parse(fonte)
    linhas = fonte.decode("utf-8", errors="replace").splitlines()
    eh_teste = eh_arquivo_de_teste(relativo)
    modulo = modulo_de(relativo)
    importacoes = _importacoes(arvore.root_node, relativo)
    artefatos: list[Artefato] = []

    def criar(no: Node, corpo: Node, nome: str, qualificado: str, tipo: str) -> None:
        inicio, fim = no.start_point[0] + 1, no.end_point[0] + 1
        chave = chave_teste(relativo, qualificado) if tipo == TIPO_TESTE else chave_codigo(relativo, qualificado)
        artefatos.append(
            Artefato(
                chave=chave, tipo=tipo, identificador=qualificado, nome=nome, arquivo=relativo,
                linha_inicio=inicio, linha_fim=fim, hash=hash_trecho(linhas, inicio, fim), modulo=modulo,
                chamadas=_chamadas(corpo) if tipo != TIPO_CLASSE else [], termos=_termos(corpo),
                importacoes=importacoes,
            )
        )

    def visitar_producao(no: Node) -> None:
        if no.type == "export_statement":
            for filho in no.named_children:
                visitar_producao(filho)
        elif no.type in {"function_declaration", "generator_function_declaration"}:
            nome = _texto(no.child_by_field_name("name"))
            criar(no, no, nome, nome, TIPO_FUNCAO)
        elif no.type in {"lexical_declaration", "variable_declaration"}:
            for declarador in no.named_children:
                valor = declarador.child_by_field_name("value") if declarador.type == "variable_declarator" else None
                nome_no = declarador.child_by_field_name("name") if declarador.type == "variable_declarator" else None
                if valor is not None and valor.type in TIPOS_FUNCAO_ANONIMA and nome_no is not None:
                    nome = _texto(nome_no)
                    criar(no, valor, nome, nome, TIPO_FUNCAO)
        elif no.type == "class_declaration":
            classe = _texto(no.child_by_field_name("name"))
            criar(no, no, classe, classe, TIPO_CLASSE)
            corpo = no.child_by_field_name("body")
            for membro in corpo.named_children if corpo is not None else []:
                if membro.type == "method_definition":
                    nome = _texto(membro.child_by_field_name("name"))
                    if nome != "constructor":
                        criar(membro, membro, nome, f"{classe}.{nome}", TIPO_METODO)

    def visitar_teste(no: Node, grupos: list[str]) -> None:
        if no.type == "call_expression":
            funcao = _nome_pontuado(no.child_by_field_name("function")) or ""
            base = funcao.split(".")[0]
            argumentos = no.child_by_field_name("arguments")
            filhos = argumentos.named_children if argumentos is not None else []
            titulo = _string(filhos[0]) if filhos else None
            callback = next((f for f in filhos[1:] if f.type in TIPOS_FUNCAO_ANONIMA), None)
            if titulo is not None and callback is not None:
                if base in FUNCOES_DE_TESTE:
                    criar(no, callback, titulo, " > ".join([*grupos, titulo]), TIPO_TESTE)
                    return
                if base in FUNCOES_DE_GRUPO:
                    visitar_teste(callback, [*grupos, titulo])
                    return
        for filho in no.named_children:
            visitar_teste(filho, grupos)

    if eh_teste:
        visitar_teste(arvore.root_node, [])
    else:
        for filho in arvore.root_node.named_children:
            visitar_producao(filho)

    comentarios = [
        (n.start_point[0] + 1, n.end_point[0] + 1, limpar_comentario(_texto(n)))
        for n in _percorrer(arvore.root_node)
        if n.type == "comment"
    ]
    atribuir_comentarios(artefatos, [c for c in comentarios if c[2]], linhas)

    aviso = None
    if arvore.root_node.has_error:
        aviso = f"{relativo}: há trechos com erro de sintaxe; a análise deste arquivo pode estar incompleta."
    return artefatos, aviso
