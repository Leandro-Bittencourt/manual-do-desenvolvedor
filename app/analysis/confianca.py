"""Etapa 4 — Combinação das evidências em um grau de confiança.

c = 1 − ∏ (1 − wᵢ · sᵢ)

em que sᵢ é a pontuação da evidência produzida pela estratégia *i* e wᵢ é o
peso atribuído a ela. O resultado fica entre 0 e 1 e aumenta quando
estratégias independentes concordam. Os pesos e os limiares das faixas
são calibrados na primeira etapa de avaliação (projetos controlados).
"""

from __future__ import annotations

from collections.abc import Iterable

from .modelos import Evidencia

PESOS_PADRAO = {"E1": 0.95, "E2": 0.85, "E3": 0.60, "E4": 0.70, "REV": 1.0}
FAIXAS_PADRAO = {"alta": 0.80, "media": 0.50}


def combinar(evidencias: Iterable[Evidencia], pesos: dict[str, float] | None = None) -> float:
    pesos = pesos or PESOS_PADRAO
    produto = 1.0
    for evidencia in evidencias:
        peso = pesos.get(evidencia.estrategia, 0.5)
        pontuacao = min(max(evidencia.pontuacao, 0.0), 1.0)
        produto *= 1 - peso * pontuacao
    return round(1 - produto, 4)


def faixa(confianca: float, limites: dict[str, float] | None = None) -> str:
    limites = limites or FAIXAS_PADRAO
    if confianca >= limites["alta"]:
        return "alta"
    if confianca >= limites["media"]:
        return "media"
    return "baixa"
