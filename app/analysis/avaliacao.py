"""Avaliação da ferramenta contra um gabarito (Seção 3.5 do TCC).

Compara os vínculos sugeridos com os vínculos corretos definidos
previamente e calcula precisão, revocação e F1 por estratégia e para a
combinação das estratégias.

Uso:
    python -m app.analysis.avaliacao exemplos/loja_virtual.zip exemplos/gabarito_loja_virtual.json

Formato do gabarito (JSON):
    {
      "vinculos": [
        {"origem": "RF-01", "destino": "src/loja/usuarios.py::CadastroUsuarios.cadastrar"},
        {"origem": "RF-01", "destino": "tests/test_usuarios.py::test_rf01_cadastra_usuario"},
        {"origem": "tests/test_usuarios.py::test_rf01_cadastra_usuario",
         "destino": "src/loja/usuarios.py::CadastroUsuarios.cadastrar"}
      ]
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from .confianca import faixa
from .modelos import ResultadoAnalise
from .pipeline import Configuracao, analisar_zip
from .requisitos import chave_requisito, compilar_padrao, encontrar_ids

ESTRATEGIAS = ("E1", "E2", "E3", "E4")


@dataclass
class Metricas:
    sugeridos: int
    corretos: int
    esperados: int

    @property
    def precisao(self) -> float:
        return self.corretos / self.sugeridos if self.sugeridos else 0.0

    @property
    def revocacao(self) -> float:
        return self.corretos / self.esperados if self.esperados else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precisao, self.revocacao
        return 2 * p * r / (p + r) if p + r else 0.0


def _resolver_referencia(referencia: str, resultado: ResultadoAnalise, padrao) -> str | None:
    """Converte ``RF-01`` ou ``arquivo.py::Nome`` na chave interna do artefato."""
    if "::" in referencia:
        arquivo, nome = referencia.split("::", 1)
        for artefato in resultado.artefatos:
            if artefato.arquivo == arquivo and artefato.identificador == nome:
                return artefato.chave
        return None
    ids = encontrar_ids(referencia, padrao)
    return chave_requisito(ids[0].canonico) if ids else None


def carregar_gabarito(caminho: str | Path, resultado: ResultadoAnalise,
                      padrao_ids: str | None = None) -> tuple[set[tuple[str, str]], list[str]]:
    padrao = compilar_padrao(padrao_ids)
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    esperados, problemas = set(), []
    for item in dados.get("vinculos", []):
        origem = _resolver_referencia(item["origem"], resultado, padrao)
        destino = _resolver_referencia(item["destino"], resultado, padrao)
        if origem and destino:
            esperados.add((origem, destino))
        else:
            problemas.append(f"Referência não encontrada no projeto: {item}")
    return esperados, problemas


def avaliar(resultado: ResultadoAnalise, esperados: set[tuple[str, str]],
            confianca_minima: float = 0.0) -> dict[str, Metricas]:
    metricas = {}
    for estrategia in ESTRATEGIAS:
        sugeridos = {par for par, evid in resultado.vinculos.items() if any(e.estrategia == estrategia for e in evid)}
        metricas[estrategia] = Metricas(len(sugeridos), len(sugeridos & esperados), len(esperados))
    combinados = {par for par, c in resultado.confiancas.items() if c >= confianca_minima}
    metricas["Combinação"] = Metricas(len(combinados), len(combinados & esperados), len(esperados))
    return metricas


def formatar_tabela(metricas: dict[str, Metricas]) -> str:
    linhas = [
        f"{'Estratégia':<12}{'Sugeridos':>10}{'Corretos':>10}{'Esperados':>10}"
        f"{'Precisão':>10}{'Revocação':>11}{'F1':>8}"
    ]
    for nome, m in metricas.items():
        linhas.append(
            f"{nome:<12}{m.sugeridos:>10}{m.corretos:>10}{m.esperados:>10}"
            f"{m.precisao:>10.2f}{m.revocacao:>11.2f}{m.f1:>8.2f}"
        )
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Avalia a ferramenta contra um gabarito de vínculos.")
    parser.add_argument("zip", help="Projeto em formato ZIP")
    parser.add_argument("gabarito", help="Arquivo JSON com os vínculos corretos")
    parser.add_argument("--confianca-minima", type=float, default=0.0,
                        help="Considera na combinação apenas vínculos com confiança maior ou igual a este valor")
    parser.add_argument("--detalhar", action="store_true", help="Lista falsos positivos e vínculos não encontrados")
    args = parser.parse_args(argv)

    configuracao = Configuracao()
    resultado = analisar_zip(args.zip, configuracao)
    esperados, problemas = carregar_gabarito(args.gabarito, resultado)
    for problema in problemas:
        print(f"[aviso] {problema}", file=sys.stderr)

    print(f"Artefatos: {resultado.metricas['requisitos']} requisitos, {resultado.metricas['testes']} testes, "
          f"{resultado.metricas['elementos_codigo']} elementos de código")
    print(f"Tempo de processamento: {resultado.metricas['tempo_ms']} ms\n")
    print(formatar_tabela(avaliar(resultado, esperados, args.confianca_minima)))

    if args.detalhar:
        nomes = {a.chave: a.identificador for a in resultado.artefatos}
        sugeridos = {par for par, c in resultado.confiancas.items() if c >= args.confianca_minima}
        print("\nFalsos positivos (sugeridos e fora do gabarito):")
        for o, d in sorted(sugeridos - esperados):
            c = resultado.confiancas[(o, d)]
            print(f"  {nomes[o]} -> {nomes[d]}  (confiança {c:.2f}, {faixa(c, configuracao.faixas)})")
        print("\nNão encontrados (no gabarito e não sugeridos):")
        for o, d in sorted(esperados - sugeridos):
            print(f"  {nomes.get(o, o)} -> {nomes.get(d, d)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
