"""Etapa 3 — Estratégias de vinculação entre artefatos (Quadro 4 do TCC).

* E1 – Marcação explícita: identificadores de requisitos em comentários,
  *docstrings* e nomes de testes (ex.: ``# @traces RF-01``, ``test_rf01_login``).
* E2 – Análise de chamadas: funções chamadas por cada teste, obtidas pela
  árvore sintática.
* E3 – Inferência transitiva: se o requisito liga-se ao teste e o teste chama
  a função, o requisito liga-se à função.
* E4 – Similaridade textual: TF-IDF e similaridade do cosseno entre o texto
  do requisito e o texto do código (identificadores, docstrings, comentários).

Cada estratégia devolve um dicionário ``(origem, destino) -> [Evidencia]``.
"""

from __future__ import annotations

import re
from collections import defaultdict

import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import texto
from .modelos import TIPO_CLASSE, TIPO_INTERFACE, Artefato, Evidencia
from .requisitos import chave_requisito, encontrar_ids
from .resolvedor import Resolvedor

Vinculos = dict[tuple[str, str], list[Evidencia]]


def _adicionar(vinculos: Vinculos, origem: str, destino: str, evidencia: Evidencia) -> None:
    vinculos.setdefault((origem, destino), []).append(evidencia)


# --------------------------------------------------------------------------
# E1 — Marcação explícita
# --------------------------------------------------------------------------
def estrategia_e1(requisitos: dict[str, Artefato], alvos: list[Artefato],
                  padrao: re.Pattern) -> tuple[Vinculos, list[str]]:
    vinculos: Vinculos = {}
    avisos: list[str] = []
    for alvo in alvos:
        fontes = [("no nome", alvo.nome, alvo.linha_inicio)]
        if alvo.docstring:
            onde = "no atributo data-requisito" if alvo.tipo == TIPO_INTERFACE else "na docstring"
            fontes.append((onde, alvo.docstring, alvo.linha_inicio))
        fontes.extend(("em comentário", texto_c, linha) for linha, texto_c in alvo.comentarios)

        ja_vinculados: set[str] = set()
        for onde, conteudo, linha in fontes:
            for encontrado in encontrar_ids(conteudo, padrao):
                chave = chave_requisito(encontrado.canonico)
                if chave not in requisitos:
                    avisos.append(
                        f"{alvo.arquivo}:{linha} cita {encontrado.exibicao}, que não está no arquivo de requisitos."
                    )
                    continue
                if chave in ja_vinculados:
                    continue
                ja_vinculados.add(chave)
                _adicionar(
                    vinculos, chave, alvo.chave,
                    Evidencia("E1", 1.0, f"Marcação {encontrado.exibicao} {onde} ({alvo.arquivo}, linha {linha})"),
                )
    return vinculos, avisos


# --------------------------------------------------------------------------
# E2 — Análise de chamadas
# --------------------------------------------------------------------------
def estrategia_e2(testes: list[Artefato], resolvedor: Resolvedor) -> Vinculos:
    vinculos: Vinculos = {}
    for teste in testes:
        melhores: dict[str, tuple[float, str]] = {}
        for chamada in teste.chamadas:
            for destino, pontuacao, como in resolvedor.resolver(chamada, teste.importacoes):
                atual = melhores.get(destino.chave)
                if atual is None or pontuacao > atual[0]:
                    melhores[destino.chave] = (
                        pontuacao,
                        f"{teste.nome} chama {destino.identificador} na linha {chamada.linha} ({como})",
                    )
        for destino_chave, (pontuacao, detalhe) in melhores.items():
            _adicionar(vinculos, teste.chave, destino_chave, Evidencia("E2", pontuacao, detalhe))
    return vinculos


def dependencias_de_codigo(codigo: list[Artefato], resolvedor: Resolvedor) -> list[tuple[str, str]]:
    """Grafo de chamadas entre elementos de produção (usado na análise de impacto)."""
    arestas = set()
    for origem in codigo:
        for chamada in origem.chamadas:
            for destino, pontuacao, _ in resolvedor.resolver(chamada, origem.importacoes):
                if pontuacao == 1.0 and destino.chave != origem.chave:
                    arestas.add((origem.chave, destino.chave))
    return sorted(arestas)


# --------------------------------------------------------------------------
# E3 — Inferência transitiva (sobre o grafo de vínculos)
# --------------------------------------------------------------------------
def estrategia_e3(confianca_req_teste: dict[tuple[str, str], float],
                  pontuacao_teste_codigo: dict[tuple[str, str], float],
                  artefatos: dict[str, Artefato], limiar: float = 0.10) -> Vinculos:
    grafo = nx.DiGraph()
    for (requisito, teste), peso in confianca_req_teste.items():
        grafo.add_edge(requisito, teste, peso=peso)
    for (teste, codigo), peso in pontuacao_teste_codigo.items():
        grafo.add_edge(teste, codigo, peso=peso)

    vinculos: Vinculos = {}
    for requisito in [n for n in grafo.nodes if n.startswith("REQ:")]:
        melhores: dict[str, tuple[float, str]] = {}
        for teste in grafo.successors(requisito):
            conf_rt = grafo[requisito][teste]["peso"]
            for codigo in grafo.successors(teste):
                # Instanciar uma classe não significa implementá-la: a inferência
                # transitiva considera apenas funções e métodos.
                if artefatos[codigo].tipo == TIPO_CLASSE:
                    continue
                pontuacao = round(conf_rt * grafo[teste][codigo]["peso"], 4)
                if pontuacao < limiar:
                    continue
                if codigo not in melhores or pontuacao > melhores[codigo][0]:
                    melhores[codigo] = (
                        pontuacao,
                        f"Via teste {artefatos[teste].identificador} (confiança {conf_rt:.2f}), "
                        f"que chama {artefatos[codigo].identificador}",
                    )
        for codigo, (pontuacao, detalhe) in melhores.items():
            _adicionar(vinculos, requisito, codigo, Evidencia("E3", pontuacao, detalhe))
    return vinculos


# --------------------------------------------------------------------------
# E4 — Similaridade textual (TF-IDF + cosseno)
# --------------------------------------------------------------------------
def texto_do_artefato(artefato: Artefato) -> str:
    if artefato.eh_requisito:
        return f"{artefato.nome} {artefato.descricao}"
    partes = [
        artefato.identificador,
        artefato.modulo.rsplit(".", 1)[-1],
        artefato.docstring,
        artefato.descricao,  # texto visível dos elementos de interface (HTML)
        " ".join(t for _, t in artefato.comentarios),
        " ".join(t.lstrip("#") for t in artefato.termos),
    ]
    return " ".join(p for p in partes if p)


def _identidade(termos):
    return termos


def estrategia_e4(requisitos: list[Artefato], alvos: list[Artefato], limiar: float = 0.30,
                  top_k: int = 5, glossario: dict[str, list[str]] | None = None) -> Vinculos:
    # Métodos especiais (__init__, __str__...) não implementam requisitos por si só.
    alvos = [a for a in alvos if not (a.nome.startswith("__") and a.nome.endswith("__"))]
    if not requisitos or not alvos:
        return {}

    exemplos: dict[str, str] = {}
    docs_req = [texto.preparar(texto_do_artefato(r), glossario, exemplos) for r in requisitos]
    docs_alvo = [texto.preparar(texto_do_artefato(a), glossario) for a in alvos]

    vetorizador = TfidfVectorizer(analyzer=_identidade, sublinear_tf=True)
    try:
        matriz = vetorizador.fit_transform(docs_req + docs_alvo)
    except ValueError:  # vocabulário vazio
        return {}

    n = len(requisitos)
    similaridades = cosine_similarity(matriz[:n], matriz[n:])

    vinculos: Vinculos = {}
    for i, requisito in enumerate(requisitos):
        ordem = similaridades[i].argsort()[::-1]
        escolhidos = [j for j in ordem[:top_k] if similaridades[i, j] >= limiar]
        termos_req = set(docs_req[i])
        for j in escolhidos:
            alvo = alvos[j]
            comuns = termos_req & set(docs_alvo[j])
            pesos = {t: matriz[i, vetorizador.vocabulary_[t]] for t in comuns if t in vetorizador.vocabulary_}
            principais = sorted(pesos, key=pesos.get, reverse=True)[:4]
            legiveis = ", ".join(exemplos.get(t, t) for t in principais) or "—"
            sim = float(similaridades[i, j])
            _adicionar(
                vinculos, requisito.chave, alvo.chave,
                Evidencia("E4", round(sim, 4), f"Similaridade textual de {sim:.2f} (termos em comum: {legiveis})"),
            )
    return vinculos


def mesclar(*conjuntos: Vinculos) -> Vinculos:
    resultado: Vinculos = defaultdict(list)
    for conjunto in conjuntos:
        for par, evidencias in conjunto.items():
            resultado[par].extend(evidencias)
    return dict(resultado)
