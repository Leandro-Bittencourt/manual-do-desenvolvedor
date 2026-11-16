"""Avaliação da 1ª etapa: os 4 projetos controlados contra seus gabaritos.

Para cada projeto: compacta a pasta em ZIP, executa a análise completa
(Etapas 1 a 4) e calcula precisão, revocação e F1 por estratégia, por tipo
de vínculo e para a combinação. Os resultados são gravados em
``exemplos/etapa1/resultados/`` (Markdown e CSV), prontos para o Capítulo 4.

Uso:
    python scripts/avaliar_etapa1.py
"""

from __future__ import annotations

import csv
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app.analysis.avaliacao import Metricas, avaliar, carregar_gabarito  # noqa: E402
from app.analysis.pipeline import Configuracao, analisar_zip  # noqa: E402

ETAPA1 = RAIZ / "exemplos" / "etapa1"
SAIDA = ETAPA1 / "resultados"
PROJETOS = [
    ("biblioteca_python", "Python", "PostgreSQL (relacional)"),
    ("biblioteca_java", "Java", "Neo4j (grafo)"),
    ("biblioteca_javascript", "JavaScript", "MongoDB (documentos)"),
    ("biblioteca_html", "HTML + JavaScript", "localStorage (chave-valor)"),
]
IGNORAR = {"node_modules", "__pycache__", ".pytest_cache", "target"}


def compactar(pasta: Path, destino: Path) -> Path:
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        for arquivo in sorted(pasta.rglob("*")):
            if arquivo.is_file() and not (set(arquivo.relative_to(pasta).parts) & IGNORAR):
                zf.write(arquivo, f"{pasta.name}/{arquivo.relative_to(pasta).as_posix()}")
    return destino


def tipo_do_par(resultado, par) -> str:
    origem = resultado.artefato(par[0])
    destino = resultado.artefato(par[1])
    if origem.eh_requisito:
        return "Requisito–teste" if destino.eh_teste else "Requisito–código"
    return "Teste–código"


def por_tipo(resultado, esperados) -> dict[str, Metricas]:
    tabela = {}
    for tipo in ("Requisito–código", "Requisito–teste", "Teste–código"):
        sugeridos = {p for p in resultado.vinculos if tipo_do_par(resultado, p) == tipo}
        esperados_tipo = {p for p in esperados if tipo_do_par(resultado, p) == tipo}
        tabela[tipo] = Metricas(len(sugeridos), len(sugeridos & esperados_tipo), len(esperados_tipo))
    return tabela


def fmt(valor: float) -> str:
    return f"{valor:.2f}".replace(".", ",")


def main() -> int:
    SAIDA.mkdir(parents=True, exist_ok=True)
    configuracao = Configuracao()
    linhas_estrategia, linhas_tipo, linhas_projeto = [], [], []
    totais: dict[str, list[int]] = {}
    limiares = {"todos os vínculos": 0.0, "confiança média ou alta (≥ 0,50)": configuracao.faixas["media"],
                "somente confiança alta (≥ 0,80)": configuracao.faixas["alta"]}
    por_limiar: dict[str, list[int]] = {nome: [0, 0, 0] for nome in limiares}

    with tempfile.TemporaryDirectory() as temporario:
        for nome, linguagem, banco in PROJETOS:
            zip_projeto = compactar(ETAPA1 / nome, Path(temporario) / f"{nome}.zip")
            resultado = analisar_zip(zip_projeto, configuracao)
            esperados, problemas = carregar_gabarito(ETAPA1 / f"gabarito_{nome}.json", resultado)
            if problemas:
                print(f"[{nome}] referências do gabarito não encontradas:", *problemas, sep="\n  ")
                return 1
            m = resultado.metricas
            linhas_projeto.append([linguagem, banco, m["requisitos"], m["testes"], m["elementos_codigo"],
                                   m["vinculos"], len(esperados), m["tempo_ms"]])
            for estrategia, met in avaliar(resultado, esperados).items():
                linhas_estrategia.append([linguagem, estrategia, met.sugeridos, met.corretos, met.esperados,
                                          met.precisao, met.revocacao, met.f1])
                soma = totais.setdefault(estrategia, [0, 0, 0])
                soma[0] += met.sugeridos
                soma[1] += met.corretos
                soma[2] += met.esperados
            for nome_limiar, limiar in limiares.items():
                met = avaliar(resultado, esperados, limiar)["Combinação"]
                soma = por_limiar[nome_limiar]
                soma[0] += met.sugeridos
                soma[1] += met.corretos
                soma[2] += met.esperados
            for tipo, met in por_tipo(resultado, esperados).items():
                linhas_tipo.append([linguagem, tipo, met.sugeridos, met.corretos, met.esperados,
                                    met.precisao, met.revocacao, met.f1])

    geral = {e: Metricas(*v) for e, v in totais.items()}

    with open(SAIDA / "metricas_por_estrategia.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(["linguagem", "estrategia", "sugeridos", "corretos", "esperados", "precisao", "revocacao", "f1"])
        escritor.writerows([*linhas_estrategia, *[["Total", e, m.sugeridos, m.corretos, m.esperados, m.precisao,
                                                     m.revocacao, m.f1] for e, m in geral.items()]])

    md = ["# Resultados da 1ª etapa — projetos controlados", ""]
    md += ["## Projetos analisados", "",
           "| Linguagem | Banco de dados (modelo) | Requisitos | Testes | Elementos de código | Vínculos sugeridos | Vínculos no gabarito | Tempo (ms) |",
           "|---|---|---:|---:|---:|---:|---:|---:|"]
    md += [f"| {l} | {b} | {r} | {t} | {c} | {v} | {g} | {fmt(ms)} |" for l, b, r, t, c, v, g, ms in linhas_projeto]
    md += ["", "## Combinação das estratégias por projeto", "",
           "| Linguagem | Sugeridos | Corretos | Esperados | Precisão | Revocação | F1 |", "|---|---:|---:|---:|---:|---:|---:|"]
    md += [f"| {l} | {s} | {c} | {e} | {fmt(p)} | {fmt(r)} | {fmt(f1)} |"
           for l, est, s, c, e, p, r, f1 in linhas_estrategia if est == "Combinação"]
    g = geral["Combinação"]
    md += [f"| **Total** | {g.sugeridos} | {g.corretos} | {g.esperados} | **{fmt(g.precisao)}** | **{fmt(g.revocacao)}** | **{fmt(g.f1)}** |"]
    md += ["", "## Desempenho de cada estratégia (4 projetos somados)", "",
           "| Estratégia | Sugeridos | Corretos | Precisão | Revocação | F1 |", "|---|---:|---:|---:|---:|---:|"]
    md += [f"| {e} | {m.sugeridos} | {m.corretos} | {fmt(m.precisao)} | {fmt(m.revocacao)} | {fmt(m.f1)} |" for e, m in geral.items()]
    md += ["", "## Efeito do limiar de confiança (4 projetos somados)", "",
           "| Vínculos considerados | Sugeridos | Corretos | Precisão | Revocação | F1 |", "|---|---:|---:|---:|---:|---:|"]
    for nome_limiar, valores in por_limiar.items():
        m = Metricas(*valores)
        md.append(f"| {nome_limiar} | {m.sugeridos} | {m.corretos} | {fmt(m.precisao)} | {fmt(m.revocacao)} | {fmt(m.f1)} |")
    md += ["", "## Combinação por tipo de vínculo", "",
           "| Linguagem | Tipo | Sugeridos | Corretos | Esperados | Precisão | Revocação |", "|---|---|---:|---:|---:|---:|---:|"]
    md += [f"| {l} | {t} | {s} | {c} | {e} | {fmt(p)} | {fmt(r)} |" for l, t, s, c, e, p, r, _ in linhas_tipo]
    md += ["", "## Detalhe por projeto e estratégia", "",
           "| Linguagem | Estratégia | Sugeridos | Corretos | Precisão | Revocação | F1 |", "|---|---|---:|---:|---:|---:|---:|"]
    md += [f"| {l} | {e} | {s} | {c} | {fmt(p)} | {fmt(r)} | {fmt(f1)} |" for l, e, s, c, _, p, r, f1 in linhas_estrategia]

    (SAIDA / "resultados_etapa1.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
