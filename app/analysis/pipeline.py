"""Orquestra as Etapas 1 a 4 e devolve o resultado da análise.

    resultado = analisar_zip("projeto.zip")

O resultado contém os artefatos (requisitos, testes e código), o grafo de
dependências entre funções, os vínculos com suas evidências, o grau de
confiança de cada vínculo e as métricas da execução (Seção 3.4 do TCC).
"""

from __future__ import annotations

import os
import tempfile
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import estrategias
from .codigo import analisar_codigo
from .confianca import FAIXAS_PADRAO, PESOS_PADRAO, combinar, faixa
from .extrator import LimitesExtracao, extrair_zip
from .modelos import TIPO_REQUISITO, Artefato, ResultadoAnalise
from .requisitos import compilar_padrao, ler_requisitos
from .resolvedor import Resolvedor


@dataclass
class Configuracao:
    padrao_ids: str | None = None
    pesos: dict[str, float] = field(default_factory=lambda: dict(PESOS_PADRAO))
    faixas: dict[str, float] = field(default_factory=lambda: dict(FAIXAS_PADRAO))
    limiar_e4: float = 0.30
    top_k_e4: int = 5
    limiar_e3: float = 0.10
    glossario: dict[str, list[str]] | None = None
    limites: LimitesExtracao = field(default_factory=LimitesExtracao)


def _tipo_do_vinculo(origem: Artefato, destino: Artefato) -> str:
    if origem.eh_requisito and destino.eh_teste:
        return "requisito-teste"
    if origem.eh_requisito:
        return "requisito-codigo"
    return "teste-codigo"


def analisar_diretorio(raiz: str | os.PathLike, arquivos: list[str],
                       configuracao: Configuracao | None = None) -> ResultadoAnalise:
    cfg = configuracao or Configuracao()
    inicio = time.perf_counter()
    raiz = Path(raiz)
    padrao = compilar_padrao(cfg.padrao_ids)

    # Etapa 2 — identificação dos artefatos
    lidos, avisos = ler_requisitos(raiz, arquivos, padrao)
    requisitos = [
        Artefato(
            chave=r.chave, tipo=TIPO_REQUISITO, identificador=r.identificador, nome=r.titulo,
            descricao=r.descricao, arquivo=r.arquivo, linha_inicio=r.linha, linha_fim=r.linha, hash=r.hash,
        )
        for r in lidos
    ]
    elementos, avisos_codigo, por_linguagem = analisar_codigo(raiz, arquivos)
    avisos.extend(avisos_codigo)
    testes = [a for a in elementos if a.eh_teste]
    codigo = [a for a in elementos if a.eh_codigo]
    artefatos = {a.chave: a for a in [*requisitos, *testes, *codigo]}
    por_requisito = {r.chave: r for r in requisitos}

    resolvedor = Resolvedor(codigo)
    dependencias = estrategias.dependencias_de_codigo(codigo, resolvedor)

    # Etapa 3 — estratégias de vinculação
    e1, avisos_e1 = estrategias.estrategia_e1(por_requisito, [*testes, *codigo], padrao)
    avisos.extend(dict.fromkeys(avisos_e1))
    e2 = estrategias.estrategia_e2(testes, resolvedor)
    e4 = estrategias.estrategia_e4(requisitos, [*testes, *codigo], cfg.limiar_e4, cfg.top_k_e4, cfg.glossario)

    # E3 usa a confiança requisito–teste (E1 + E4) e as chamadas dos testes (E2)
    parcial = estrategias.mesclar(e1, e4)
    conf_req_teste = {
        par: combinar(evid, cfg.pesos)
        for par, evid in parcial.items()
        if artefatos[par[1]].eh_teste
    }
    pont_teste_codigo = {par: max(e.pontuacao for e in evid) for par, evid in e2.items()}
    e3 = estrategias.estrategia_e3(conf_req_teste, pont_teste_codigo, artefatos, cfg.limiar_e3)

    vinculos = estrategias.mesclar(e1, e2, e3, e4)

    # Etapa 4 — combinação das evidências
    confiancas = {par: combinar(evid, cfg.pesos) for par, evid in vinculos.items()}

    por_estrategia = Counter()
    for evidencias in vinculos.values():
        for nome in {e.estrategia for e in evidencias}:
            por_estrategia[nome] += 1
    por_faixa = Counter(faixa(c, cfg.faixas) for c in confiancas.values())
    por_tipo = Counter(_tipo_do_vinculo(artefatos[o], artefatos[d]) for o, d in vinculos)

    metricas = {
        "tempo_ms": round((time.perf_counter() - inicio) * 1000, 1),
        "arquivos_analisados": len(arquivos),
        "arquivos_por_linguagem": por_linguagem,
        "requisitos": len(requisitos),
        "testes": len(testes),
        "elementos_codigo": len(codigo),
        "dependencias": len(dependencias),
        "vinculos": len(vinculos),
        "vinculos_por_estrategia": {k: por_estrategia.get(k, 0) for k in ("E1", "E2", "E3", "E4")},
        "vinculos_por_faixa": {k: por_faixa.get(k, 0) for k in ("alta", "media", "baixa")},
        "vinculos_por_tipo": dict(por_tipo),
        "avisos": len(avisos),
    }

    return ResultadoAnalise(
        artefatos=list(artefatos.values()),
        dependencias=dependencias,
        vinculos=vinculos,
        confiancas=confiancas,
        metricas=metricas,
        avisos=avisos,
    )


def analisar_zip(caminho_zip: str | os.PathLike, configuracao: Configuracao | None = None) -> ResultadoAnalise:
    """Etapa 1 + análise. A pasta temporária é apagada ao final: o código
    enviado não fica armazenado, apenas as referências (arquivo e linhas)."""
    cfg = configuracao or Configuracao()
    inicio = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="manual-dev-") as temporario:
        extracao = extrair_zip(caminho_zip, temporario, cfg.limites)
        resultado = analisar_diretorio(extracao.raiz, extracao.arquivos, cfg)
    resultado.metricas.update(
        {
            "tempo_ms": round((time.perf_counter() - inicio) * 1000, 1),
            "arquivos_ignorados": extracao.ignorados,
            "arquivos_sensiveis_ignorados": len(extracao.sensiveis),
        }
    )
    if extracao.sensiveis:
        resultado.avisos.insert(
            0,
            f"{len(extracao.sensiveis)} arquivo(s) sensível(is) foram ignorados por segurança "
            f"e não foram lidos: {', '.join(extracao.sensiveis[:5])}"
            + ("..." if len(extracao.sensiveis) > 5 else ""),
        )
    return resultado
