"""Leitura de HTML (camada de interface) com o módulo nativo ``html.parser``.

HTML é uma linguagem de marcação: não tem funções nem testes próprios.
Por isso, seus elementos rastreáveis são os **elementos de interface com
``id``** (formulários, seções, botões, tabelas...). Para cada um são
registrados:

* o texto visível e os rótulos (``placeholder``, ``aria-label``, ``title``...),
  usados pela similaridade textual (E4);
* marcações explícitas em comentários (``<!-- @traces RF-01 -->``) ou no
  atributo ``data-requisito="RF-01"`` (E1);
* os ``id`` dos campos internos, para que testes de interface que usam
  seletores (``#titulo``) sejam ligados ao elemento (E2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

from .codigo_base import atribuir_comentarios, chave_codigo, hash_trecho, limpar_comentario, modulo_de
from .modelos import TIPO_INTERFACE, Artefato

ELEMENTOS_RASTREAVEIS = frozenset(
    {"form", "section", "article", "main", "nav", "aside", "header", "footer", "dialog",
     "table", "ul", "ol", "div", "button", "a", "fieldset", "details"}
)
ELEMENTOS_VAZIOS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
)
ATRIBUTOS_DE_TEXTO = ("placeholder", "aria-label", "title", "alt", "value", "label")
ATRIBUTOS_DE_REQUISITO = ("data-requisito", "data-requisitos", "data-req", "data-requirement")
CONTEUDO_IGNORADO = frozenset({"script", "style"})


@dataclass
class _Aberto:
    tag: str
    linha: int
    artefato: Artefato | None = None
    textos: list[str] = field(default_factory=list)


class _Leitor(HTMLParser):
    def __init__(self, relativo: str):
        super().__init__(convert_charrefs=True)
        self.relativo = relativo
        self.modulo = modulo_de(relativo)
        self.pilha: list[_Aberto] = []
        self.artefatos: list[Artefato] = []
        self.comentarios: list[tuple[int, int, str]] = []
        self._ignorar = 0

    def _rastreado_mais_interno(self) -> Artefato | None:
        for aberto in reversed(self.pilha):
            if aberto.artefato is not None:
                return aberto.artefato
        return None

    def handle_starttag(self, tag, attrs):
        linha = self.getpos()[0]
        atributos = {k: (v or "") for k, v in attrs}
        if tag in CONTEUDO_IGNORADO:
            self._ignorar += 1
        artefato = None
        ident = atributos.get("id", "").strip()
        if ident and tag in ELEMENTOS_RASTREAVEIS:
            qualificado = f"{tag}#{ident}"
            artefato = Artefato(
                chave=chave_codigo(self.relativo, qualificado), tipo=TIPO_INTERFACE, identificador=qualificado,
                nome=ident, arquivo=self.relativo, linha_inicio=linha, linha_fim=linha, modulo=self.modulo,
            )
            requisitos = [atributos[a] for a in ATRIBUTOS_DE_REQUISITO if atributos.get(a)]
            if requisitos:
                artefato.docstring = " ".join(requisitos)
            self.artefatos.append(artefato)

        aberto = _Aberto(tag, linha, artefato)
        textos = [atributos[a] for a in ATRIBUTOS_DE_TEXTO if atributos.get(a)]
        alvo = artefato or self._rastreado_mais_interno()
        if alvo is not None:
            alvo.descricao = " ".join(p for p in [alvo.descricao, *textos] if p)
            if ident:
                alvo.termos.append(f"#{ident}")
            for nome in ("name", "for"):
                if atributos.get(nome):
                    alvo.termos.append(atributos[nome])

        if tag in ELEMENTOS_VAZIOS:
            return
        self.pilha.append(aberto)

    def handle_endtag(self, tag):
        if tag in CONTEUDO_IGNORADO and self._ignorar:
            self._ignorar -= 1
        linha = self.getpos()[0]
        for i in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[i].tag == tag:
                for fechado in self.pilha[i:]:
                    if fechado.artefato is not None:
                        fechado.artefato.linha_fim = linha
                del self.pilha[i:]
                return

    def handle_data(self, data):
        if self._ignorar or not data.strip():
            return
        alvo = self._rastreado_mais_interno()
        if alvo is not None:
            alvo.descricao = f"{alvo.descricao} {data.strip()}".strip()

    def handle_comment(self, data):
        inicio = self.getpos()[0]
        texto = limpar_comentario(data)
        if texto:
            self.comentarios.append((inicio, inicio + data.count("\n"), texto))


def analisar_html(raiz: Path, relativo: str) -> tuple[list[Artefato], str | None]:
    texto = (Path(raiz) / relativo).read_text(encoding="utf-8-sig", errors="replace")
    linhas = texto.splitlines()
    leitor = _Leitor(relativo)
    leitor.feed(texto)
    leitor.close()
    for artefato in leitor.artefatos:
        if artefato.linha_fim < artefato.linha_inicio:
            artefato.linha_fim = artefato.linha_inicio
        artefato.hash = hash_trecho(linhas, artefato.linha_inicio, artefato.linha_fim)
    atribuir_comentarios(leitor.artefatos, leitor.comentarios, linhas)
    return leitor.artefatos, None
