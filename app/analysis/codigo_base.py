"""Regras comuns à leitura de código em todas as linguagens suportadas.

Linguagens e ferramentas de leitura:

* Python      — módulos nativos ``ast`` e ``tokenize``;
* Java        — tree-sitter (gramática ``tree-sitter-java``);
* JavaScript  — tree-sitter (gramática ``tree-sitter-javascript``);
* HTML        — módulo nativo ``html.parser`` (camada de interface).
"""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath

from .modelos import Artefato

LINGUAGENS = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".html": "html",
    ".htm": "html",
}

ARQUIVOS_NAO_PRODUCAO = frozenset({"conftest.py", "setup.py"})
PASTAS_DE_TESTE = frozenset({"tests", "test", "testing", "__tests__", "e2e", "cypress", "spec"})
SUFIXOS_TESTE_JS = (".test.js", ".spec.js", ".test.mjs", ".spec.mjs", ".test.cjs", ".spec.cjs",
                    ".test.jsx", ".spec.jsx")


def linguagem_de(relativo: str) -> str | None:
    return LINGUAGENS.get(PurePosixPath(relativo).suffix.lower())


def eh_arquivo_de_teste(relativo: str) -> bool:
    caminho = PurePosixPath(relativo)
    nome = caminho.name
    linguagem = linguagem_de(relativo)
    if linguagem == "python":
        return nome.startswith("test_") or nome.endswith("_test.py")
    if linguagem == "java":
        partes = [p.lower() for p in caminho.parts]
        em_src_test = any(partes[i] == "src" and partes[i + 1] == "test" for i in range(len(partes) - 1))
        return em_src_test or nome.endswith(("Test.java", "Tests.java", "IT.java")) or (
            nome.startswith("Test") and nome.endswith(".java")
        )
    if linguagem == "javascript":
        return nome.lower().endswith(SUFIXOS_TESTE_JS) or "__tests__" in caminho.parts
    return False


def eh_arquivo_de_producao(relativo: str) -> bool:
    caminho = PurePosixPath(relativo)
    linguagem = linguagem_de(relativo)
    if linguagem is None or eh_arquivo_de_teste(relativo):
        return False
    if caminho.name in ARQUIVOS_NAO_PRODUCAO:
        return False
    nome = caminho.name.lower()
    if linguagem == "javascript" and (".config." in nome or nome.endswith(".min.js") or nome.startswith(".")):
        return False
    return not any(parte.lower() in PASTAS_DE_TESTE for parte in caminho.parts[:-1])


def modulo_de(relativo: str) -> str:
    """Nome do módulo usado para resolver importações.

    Python/JavaScript: ``src/loja/carrinho.py`` -> ``src.loja.carrinho``.
    Java: o pacote é a pasta do arquivo (``src/main/java/br/app/Livro.java`` -> ``src.main.java.br.app``).
    """
    caminho = PurePosixPath(relativo)
    if linguagem_de(relativo) == "java":
        return ".".join(caminho.parent.parts)
    partes = list(caminho.with_suffix("").parts)
    if partes and partes[-1] in {"__init__", "index"}:
        partes.pop()
    return ".".join(partes)


def chave_codigo(arquivo: str, qualificado: str) -> str:
    return f"CODE:{arquivo}::{qualificado}"


def chave_teste(arquivo: str, qualificado: str) -> str:
    return f"TEST:{arquivo}::{qualificado}"


def hash_trecho(linhas: list[str], inicio: int, fim: int) -> str:
    trecho = "\n".join(l.rstrip() for l in linhas[inicio - 1 : fim])
    return hashlib.sha256(trecho.encode("utf-8")).hexdigest()


def atribuir_comentarios(artefatos: list[Artefato], comentarios: list[tuple[int, int, str]],
                         linhas: list[str]) -> None:
    """Associa cada comentário ``(linha_inicial, linha_final, texto)`` a um elemento.

    1. comentário logo acima de uma definição pertence a ela;
    2. senão, ao elemento mais interno que contém o comentário.
    """
    linhas_comentario = {l for ini, fim, _ in comentarios for l in range(ini, fim + 1)}
    for inicio, fim, texto in comentarios:
        seguinte = fim + 1
        while seguinte <= len(linhas) and (seguinte in linhas_comentario or not linhas[seguinte - 1].strip()):
            seguinte += 1
        candidatos = [a for a in artefatos if a.linha_inicio == seguinte]
        if not candidatos:
            candidatos = [a for a in artefatos if a.linha_inicio <= inicio <= a.linha_fim]
        if not candidatos:
            continue
        alvo = min(candidatos, key=lambda a: a.linha_fim - a.linha_inicio)
        alvo.comentarios.append((inicio, texto))


def limpar_comentario(texto: str) -> str:
    """Remove marcadores de comentário (``//``, ``/* */``, ``*``, ``<!-- -->``)."""
    linhas = []
    for linha in texto.replace("<!--", "").replace("-->", "").splitlines():
        linha = linha.strip()
        for prefixo in ("/**", "/*", "*/", "//", "*"):
            if linha.startswith(prefixo):
                linha = linha[len(prefixo):].strip()
        if linha.endswith("*/"):
            linha = linha[:-2].strip()
        if linha:
            linhas.append(linha)
    return " ".join(linhas)
