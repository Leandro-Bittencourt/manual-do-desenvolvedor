"""Regras da aplicação: salva o resultado da análise, aplica as decisões do
desenvolvedor, calcula a cobertura e localiza a origem de erros."""

from __future__ import annotations

import json
import os
import tempfile
from collections import defaultdict
from pathlib import PurePosixPath

import networkx as nx
from flask import current_app

from .analysis import localizador
from .analysis.extrator import ErroExtracao  # noqa: F401  (reexportado para as views)
from .analysis.modelos import ResultadoAnalise
from .analysis.pipeline import Configuracao, analisar_zip
from .extensions import db
from .models import Decisao, Dependencia, Elemento, Evidencia, Projeto, Versao, Vinculo


# --------------------------------------------------------------------------
# Análise e persistência
# --------------------------------------------------------------------------
def configuracao_da_app() -> Configuracao:
    c = current_app.config
    return Configuracao(
        padrao_ids=c.get("ANALISE_PADRAO_IDS"),
        pesos=dict(c["ANALISE_PESOS"]),
        faixas=dict(c["ANALISE_FAIXAS"]),
        limiar_e4=c["ANALISE_LIMIAR_E4"],
        top_k_e4=c["ANALISE_TOP_K_E4"],
        limiar_e3=c["ANALISE_LIMIAR_E3"],
    )


def nome_seguro(nome: str | None) -> str:
    base = PurePosixPath((nome or "projeto.zip").replace("\\", "/")).name
    return base[:200] or "projeto.zip"


def analisar_arquivo_enviado(arquivo) -> ResultadoAnalise:
    """Salva o upload em um arquivo temporário, analisa e apaga o arquivo."""
    descritor, caminho = tempfile.mkstemp(suffix=".zip", prefix="manual-upload-")
    os.close(descritor)
    try:
        arquivo.save(caminho)
        return analisar_zip(caminho, configuracao_da_app())
    finally:
        try:
            os.remove(caminho)
        except OSError:
            pass


def _status_por_decisao(decisao: Decisao | None, origem: Elemento, destino: Elemento) -> str:
    if decisao is None:
        return "sugerido"
    if decisao.hash_origem == origem.hash and decisao.hash_destino == destino.hash:
        return decisao.decisao
    return "a_revisar"  # algum dos elementos mudou desde a decisão


def salvar_versao(projeto: Projeto, resultado: ResultadoAnalise, nome_arquivo: str) -> Versao:
    numero = (projeto.versao_atual.numero + 1) if projeto.versao_atual else 1
    versao = Versao(
        projeto=projeto,
        numero=numero,
        nome_arquivo=nome_arquivo,
        metricas_json=json.dumps(resultado.metricas, ensure_ascii=False),
        avisos_json=json.dumps(resultado.avisos, ensure_ascii=False),
    )
    db.session.add(versao)

    elementos: dict[str, Elemento] = {}
    for a in resultado.artefatos:
        elemento = Elemento(
            versao=versao, tipo=a.tipo, chave=a.chave, identificador=a.identificador, nome=a.nome,
            descricao=a.descricao if a.eh_requisito else "", arquivo=a.arquivo,
            linha_inicio=a.linha_inicio, linha_fim=a.linha_fim, hash=a.hash,
        )
        db.session.add(elemento)
        elementos[a.chave] = elemento
    db.session.flush()

    for origem, destino in resultado.dependencias:
        db.session.add(Dependencia(versao=versao, origem=elementos[origem], destino=elementos[destino]))

    decisoes = {(d.origem_chave, d.destino_chave): d for d in projeto.decisoes}
    gerados = set()
    for (origem, destino), evidencias in resultado.vinculos.items():
        vinculo = Vinculo(
            versao=versao, origem=elementos[origem], destino=elementos[destino],
            confianca=resultado.confiancas[(origem, destino)],
            status=_status_por_decisao(decisoes.get((origem, destino)), elementos[origem], elementos[destino]),
        )
        for e in evidencias:
            vinculo.evidencias.append(Evidencia(estrategia=e.estrategia, pontuacao=e.pontuacao, detalhe=e.detalhe))
        db.session.add(vinculo)
        gerados.add((origem, destino))

    # Vínculos confirmados antes, que as estratégias não sugeriram desta vez.
    for (origem, destino), decisao in decisoes.items():
        if decisao.decisao != "confirmado" or (origem, destino) in gerados:
            continue
        if origem not in elementos or destino not in elementos:
            continue
        vinculo = Vinculo(
            versao=versao, origem=elementos[origem], destino=elementos[destino], confianca=1.0,
            status=_status_por_decisao(decisao, elementos[origem], elementos[destino]),
        )
        vinculo.evidencias.append(
            Evidencia(estrategia="REV", pontuacao=1.0, detalhe="Confirmado pelo desenvolvedor em versão anterior")
        )
        db.session.add(vinculo)

    return versao


def criar_projeto(usuario, nome: str, resultado: ResultadoAnalise, nome_arquivo: str) -> Projeto:
    projeto = Projeto(usuario=usuario, nome=nome)
    db.session.add(projeto)
    salvar_versao(projeto, resultado, nome_arquivo)
    db.session.commit()
    return projeto


def registrar_decisao(vinculo: Vinculo, decisao: str) -> None:
    if decisao not in {"confirmado", "rejeitado"}:
        raise ValueError("Decisão inválida")
    vinculo.status = decisao
    projeto = vinculo.versao.projeto
    registro = Decisao.query.filter_by(
        projeto_id=projeto.id, origem_chave=vinculo.origem.chave, destino_chave=vinculo.destino.chave
    ).first()
    if registro is None:
        registro = Decisao(projeto=projeto, origem_chave=vinculo.origem.chave, destino_chave=vinculo.destino.chave)
        db.session.add(registro)
    registro.decisao = decisao
    registro.hash_origem = vinculo.origem.hash
    registro.hash_destino = vinculo.destino.hash
    db.session.commit()


# --------------------------------------------------------------------------
# Consultas
# --------------------------------------------------------------------------
def vinculos_ativos(versao: Versao) -> list[Vinculo]:
    return [v for v in versao.vinculos if v.ativo]


def mapa_de_vinculos(versao: Versao) -> tuple[dict[int, list[Vinculo]], dict[int, list[Vinculo]]]:
    """Vínculos ativos indexados pela origem e pelo destino."""
    por_origem, por_destino = defaultdict(list), defaultdict(list)
    for v in vinculos_ativos(versao):
        por_origem[v.origem_id].append(v)
        por_destino[v.destino_id].append(v)
    for lista in [*por_origem.values(), *por_destino.values()]:
        lista.sort(key=lambda v: v.confianca, reverse=True)
    return por_origem, por_destino


def elementos_por_tipo(versao: Versao, *tipos: str) -> list[Elemento]:
    return (
        Elemento.query.filter(Elemento.versao_id == versao.id, Elemento.tipo.in_(tipos))
        .order_by(Elemento.arquivo, Elemento.linha_inicio, Elemento.identificador)
        .all()
    )


def cobertura(versao: Versao) -> list[dict]:
    por_origem, _ = mapa_de_vinculos(versao)
    linhas = []
    for requisito in elementos_por_tipo(versao, "requisito"):
        vinculos = por_origem.get(requisito.id, [])
        linhas.append(
            {
                "requisito": requisito,
                "codigo": [v for v in vinculos if v.destino.eh_codigo],
                "testes": [v for v in vinculos if v.destino.eh_teste],
            }
        )
    return linhas


def resumo(versao: Versao | None) -> dict:
    if versao is None:
        return {}
    linhas = cobertura(versao)
    total = len(linhas)
    com_codigo = sum(1 for l in linhas if l["codigo"])
    com_teste = sum(1 for l in linhas if l["testes"])
    status = defaultdict(int)
    for v in versao.vinculos:
        status[v.status] += 1
    contagem = defaultdict(int)
    for e in versao.elementos:
        contagem["codigo" if e.eh_codigo else e.tipo] += 1
    return {
        "requisitos": contagem["requisito"],
        "testes": contagem["teste"],
        "codigo": contagem["codigo"],
        "vinculos": sum(status.values()) - status["rejeitado"],
        "pendentes": status["sugerido"] + status["a_revisar"],
        "a_revisar": status["a_revisar"],
        "confirmados": status["confirmado"],
        "rejeitados": status["rejeitado"],
        "cobertura_codigo": (com_codigo / total) if total else 0.0,
        "cobertura_testes": (com_teste / total) if total else 0.0,
        "sem_codigo": [l["requisito"] for l in linhas if not l["codigo"]],
        "sem_teste": [l["requisito"] for l in linhas if not l["testes"]],
    }


# --------------------------------------------------------------------------
# Localização de erros (Etapa 6)
# --------------------------------------------------------------------------
def _elemento_na_linha(versao: Versao, arquivo: str, linha: int) -> Elemento | None:
    candidatos = (
        Elemento.query.filter(
            Elemento.versao_id == versao.id,
            Elemento.arquivo == arquivo,
            Elemento.tipo != "requisito",
            Elemento.linha_inicio <= linha,
            Elemento.linha_fim >= linha,
        ).all()
    )
    if not candidatos:
        return None
    return min(candidatos, key=lambda e: (e.linha_fim - e.linha_inicio))


def _grafo_de_chamadas(versao: Versao) -> nx.DiGraph:
    grafo = nx.DiGraph()
    for d in versao.dependencias:
        grafo.add_edge(d.origem_id, d.destino_id)
    return grafo


def _alcancaveis(grafo: nx.DiGraph, inicio: list[int], niveis: int, reverso: bool) -> list[Elemento]:
    base = grafo.reverse(copy=False) if reverso else grafo
    ids: set[int] = set()
    for no in inicio:
        if no in base:
            distancias = nx.single_source_shortest_path_length(base, no, cutoff=niveis)
            ids.update(i for i, dist in distancias.items() if dist > 0)
    ids -= set(inicio)
    if not ids:
        return []
    return Elemento.query.filter(Elemento.id.in_(ids)).order_by(Elemento.arquivo, Elemento.linha_inicio).all()


def _impacto(versao: Versao, origem: Elemento, niveis: int = 2) -> list[Elemento]:
    """Funções que chamam a origem (direta ou indiretamente), até ``niveis`` níveis."""
    return _alcancaveis(_grafo_de_chamadas(versao), [origem.id], niveis, reverso=True)


def localizar_erro(versao: Versao, texto: str) -> dict:
    arquivos = sorted({e.arquivo for e in versao.elementos if e.arquivo and not e.eh_requisito})
    pilha: list[dict] = []
    origem: Elemento | None = None

    for quadro in localizador.extrair_quadros(texto):
        arquivo = localizador.casar_arquivo(quadro.arquivo, arquivos)
        elemento = _elemento_na_linha(versao, arquivo, quadro.linha) if arquivo else None
        pilha.append({"quadro": quadro, "arquivo": arquivo, "elemento": elemento})
    for item in reversed(pilha):  # o quadro mais interno do projeto é a origem
        if item["elemento"] is not None:
            origem = item["elemento"]
            break

    if origem is None and not pilha:
        teste = localizador.extrair_teste(texto)
        if teste:
            arquivo, nome = teste
            consulta = Elemento.query.filter(Elemento.versao_id == versao.id, Elemento.tipo != "requisito")
            candidatos = [
                e for e in consulta.all()
                if (e.identificador == nome or e.nome == nome)
                and (arquivo is None or e.arquivo.endswith(arquivo.replace("\\", "/")))
            ]
            origem = candidatos[0] if candidatos else None

    if origem is None:
        return {"pilha": pilha, "origem": None}

    por_origem, por_destino = mapa_de_vinculos(versao)
    requisitos: dict[int, Vinculo] = {}
    testes: dict[int, Vinculo] = {}
    codigo: list[Vinculo] = []
    codigo_indireto: list[Elemento] = []

    if origem.eh_teste:
        for v in por_destino.get(origem.id, []):
            if v.origem.eh_requisito:
                requisitos[v.origem_id] = v
        codigo = [v for v in por_origem.get(origem.id, []) if v.destino.eh_codigo]
        # funções chamadas pelo código que o teste exercita (o defeito pode estar nelas)
        codigo_indireto = _alcancaveis(_grafo_de_chamadas(versao), [v.destino_id for v in codigo], 2, reverso=False)
    else:
        for v in por_destino.get(origem.id, []):
            if v.origem.eh_requisito:
                requisitos[v.origem_id] = v
            elif v.origem.eh_teste:
                testes[v.origem_id] = v
        for v_req in list(requisitos.values()):
            for v in por_origem.get(v_req.origem_id, []):
                if v.destino.eh_teste and v.destino_id not in testes:
                    testes[v.destino_id] = v

    # Sem vínculo direto, os requisitos são herdados pelo grafo de chamadas: de quem chama a
    # origem (quando ela é código) ou do código exercitado (quando ela é um teste).
    requisitos_indiretos: list[dict] = []
    if not requisitos:
        if origem.eh_teste:
            base = [v.destino for v in codigo] + codigo_indireto
        else:
            base = _impacto(versao, origem)
        pontuacao: dict[int, dict] = {}
        for elemento in base:
            for v in por_destino.get(elemento.id, []):
                if v.origem.eh_requisito:
                    item = pontuacao.setdefault(v.origem_id, {"requisito": v.origem, "pontos": 0.0, "via": []})
                    item["pontos"] += v.confianca
                    item["via"].append(elemento)
        requisitos_indiretos = sorted(pontuacao.values(), key=lambda i: i["pontos"], reverse=True)

    return {
        "pilha": pilha,
        "origem": origem,
        "requisitos": sorted(requisitos.values(), key=lambda v: v.confianca, reverse=True),
        "requisitos_indiretos": requisitos_indiretos,
        "testes": sorted(testes.values(), key=lambda v: v.confianca, reverse=True),
        "codigo": codigo,
        "codigo_indireto": codigo_indireto,
        "impacto": _impacto(versao, origem) if origem.eh_codigo else [],
    }


# --------------------------------------------------------------------------
# Exportação
# --------------------------------------------------------------------------
def exportar(versao: Versao) -> dict:
    def elemento(e: Elemento) -> dict:
        return {
            "tipo": e.tipo, "identificador": e.identificador, "nome": e.nome,
            "arquivo": e.arquivo, "linha_inicio": e.linha_inicio, "linha_fim": e.linha_fim,
        }

    return {
        "projeto": versao.projeto.nome,
        "versao": versao.numero,
        "arquivo": versao.nome_arquivo,
        "enviado_em": versao.enviado_em.isoformat() if versao.enviado_em else None,
        "metricas": versao.metricas,
        "avisos": versao.avisos,
        "elementos": [elemento(e) for e in versao.elementos],
        "vinculos": [
            {
                "origem": elemento(v.origem),
                "destino": elemento(v.destino),
                "confianca": v.confianca,
                "status": v.status,
                "evidencias": [
                    {"estrategia": ev.estrategia, "pontuacao": ev.pontuacao, "detalhe": ev.detalhe}
                    for ev in v.evidencias
                ],
            }
            for v in versao.vinculos
        ],
    }
