"""Etapa 6 — Leitura de mensagens de erro para localizar a origem da falha.

Aceita:

* *traceback* do Python: ``File "/caminho/app.py", line 42, in funcao``;
* pilha do Java: ``at br.app.Servico.devolver(Servico.java:42)``;
* pilha do JavaScript: ``at devolver (file:///C:/app/src/emprestimos.js:42:11)``;
* saída resumida do pytest: ``src/app.py:42: AssertionError``;
* identificador de teste do pytest: ``tests/test_app.py::test_login``;
* apenas o nome de um teste ou função: ``test_login``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

RE_TRACEBACK = re.compile(r'File "(?P<arquivo>[^"]+)", line (?P<linha>\d+)(?:, in (?P<funcao>[^\s]+))?')
RE_PYTEST = re.compile(r"(?P<arquivo>[\w.\\/:-]+\.py):(?P<linha>\d+)")
# Java: "at br.app.Servico.devolver(Servico.java:42)"
RE_JAVA = re.compile(r"at\s+(?P<funcao>[\w$.<>]+)\((?P<arquivo>[\w$-]+\.java):(?P<linha>\d+)\)")
# JavaScript (Node.js/navegador): "at devolver (file:///C:/app/src/emprestimos.js:42:11)"
RE_JS = re.compile(
    r"at\s+(?:async\s+)?(?:(?P<funcao>[^\s(]+)\s+\()?(?:file:/{2,3})?"
    r"(?P<arquivo>[^\s()]+?\.(?:m?js|cjs|jsx|html?)):(?P<linha>\d+):\d+\)?"
)
# Cabeçalho do relatório do "node --test" ("test at test/x.test.js:36:3"): não é um quadro da pilha.
RE_CABECALHO_NODE = re.compile(r"^\s*test at \S+$", re.MULTILINE)
RE_NODEID = re.compile(r"(?P<arquivo>[\w.\\/-]+\.py)::(?P<nome>[\w.:\[\]-]+)")
RE_NOME = re.compile(r"^[A-Za-z_][\w.]*$")


@dataclass
class Quadro:
    arquivo: str
    linha: int
    funcao: str | None = None


def _normalizar(caminho: str) -> list[str]:
    return [p for p in caminho.replace("\\", "/").split("/") if p and p != "."]


def extrair_quadros(texto: str) -> list[Quadro]:
    """Quadros da pilha, sempre do mais externo ao mais interno.

    O traceback do Python já vem nessa ordem; as pilhas de Java e de
    JavaScript vêm ao contrário (a chamada mais interna primeiro).
    """
    texto = RE_CABECALHO_NODE.sub("", texto or "")
    quadros = [Quadro(m.group("arquivo"), int(m.group("linha")), m.group("funcao")) for m in RE_TRACEBACK.finditer(texto)]
    if quadros:
        return quadros
    for padrao in (RE_JAVA, RE_JS):
        quadros = [Quadro(m.group("arquivo"), int(m.group("linha")), m.group("funcao")) for m in padrao.finditer(texto)]
        if quadros:
            return list(reversed(quadros))
    return [Quadro(m.group("arquivo"), int(m.group("linha"))) for m in RE_PYTEST.finditer(texto)]


def extrair_teste(texto: str) -> tuple[str | None, str] | None:
    """Identificador de teste (``arquivo::nome``) ou apenas um nome."""
    m = RE_NODEID.search(texto or "")
    if m:
        nome = m.group("nome").split("[")[0].replace("::", ".")
        return m.group("arquivo"), nome
    candidato = (texto or "").strip()
    if RE_NOME.match(candidato):
        return None, candidato
    return None


def casar_arquivo(caminho_erro: str, arquivos_projeto: list[str]) -> str | None:
    """Encontra o arquivo do projeto que corresponde ao caminho do erro.

    O caminho do erro costuma ser absoluto (máquina do desenvolvedor), então
    escolhe-se o arquivo do projeto com o maior sufixo de pastas em comum.
    """
    partes_erro = [p.lower() for p in _normalizar(caminho_erro)]
    if not partes_erro:
        return None
    melhor, melhor_tamanho = None, 0
    for arquivo in arquivos_projeto:
        partes = [p.lower() for p in PurePosixPath(arquivo).parts]
        if partes[-1] != partes_erro[-1]:
            continue
        comum = 0
        for a, b in zip(reversed(partes), reversed(partes_erro)):
            if a != b:
                break
            comum += 1
        if comum > melhor_tamanho:
            melhor, melhor_tamanho = arquivo, comum
    return melhor
