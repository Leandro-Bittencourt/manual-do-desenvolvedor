"""Experimento de localização de erros (1ª etapa).

Para cada projeto controlado, um defeito é inserido no código (mutação), o
teste afetado é executado de verdade e a mensagem de erro produzida
(traceback do Python, pilha do Java ou do Node.js) é entregue à ferramenta,
que deve apontar a origem do erro e o requisito relacionado.

Tipos de defeito:
* D1 — erro de cálculo na multa (o teste falha por asserção);
* D2 — exceção dentro do método de devolução;
* D3 — exceção dentro da validação do ISBN.

Uso:
    python scripts/experimento_localizacao.py

Requer Python (pytest), Node.js 18+ e JDK 17+ com as bibliotecas do JUnit 5
no repositório local do Maven (~/.m2). Projetos sem a ferramenta necessária
são ignorados com aviso.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app import create_app  # noqa: E402
from app.config import ConfigTeste  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Usuario  # noqa: E402
from app import services  # noqa: E402
from app.analysis.pipeline import analisar_zip  # noqa: E402

sys.path.insert(0, str(RAIZ / "scripts"))
from avaliar_etapa1 import ETAPA1, compactar  # noqa: E402

SAIDA = ETAPA1 / "resultados"


@dataclass
class Cenario:
    projeto: str
    linguagem: str
    defeito: str
    arquivo: str
    antes: str
    depois: str
    teste: str  # identificação do teste a executar
    elemento_defeituoso: str  # identificador do elemento onde o defeito foi inserido
    requisito: str


CENARIOS = [
    # --- Python -----------------------------------------------------------
    Cenario("biblioteca_python", "Python", "D1 — cálculo da multa", "src/biblioteca/servicos.py",
            "return dias_de_atraso * VALOR_MULTA_DIA", "return dias_de_atraso * VALOR_MULTA_DIA * 1.5",
            "tests/test_emprestimos.py::test_multa_por_dias_de_atraso", "calcular_multa", "RF-04"),
    Cenario("biblioteca_python", "Python", "D2 — exceção na devolução", "src/biblioteca/servicos.py",
            "livro.disponivel = True", "livro.disponivel = livro.situacao",
            "tests/test_emprestimos.py::test_devolucao_no_prazo_nao_gera_multa", "ServicoBiblioteca.devolver", "RF-04"),
    Cenario("biblioteca_python", "Python", "D3 — exceção na validação do ISBN", "src/biblioteca/servicos.py",
            "for c in isbn if c.isdigit()", "for c in isbn.digitos if c.isdigit()",
            "tests/test_livros.py::test_rf01_cadastra_livro_com_isbn_valido", "validar_isbn", "RF-01"),
    # --- Java -------------------------------------------------------------
    Cenario("biblioteca_java", "Java", "D1 — cálculo da multa", "src/main/java/br/biblioteca/servico/Validacoes.java",
            "return diasDeAtraso * VALOR_MULTA_DIA;", "return diasDeAtraso * VALOR_MULTA_DIA * 1.5;",
            "br.biblioteca.EmprestimosTest#multaPorDiasDeAtraso", "Validacoes.calcularMulta", "RF-04"),
    Cenario("biblioteca_java", "Java", "D2 — exceção na devolução", "src/main/java/br/biblioteca/servico/ServicoBiblioteca.java",
            "Livro livro = repositorio.buscarLivro(isbn).orElseThrow();",
            'Livro livro = repositorio.buscarLivro(isbn + "-").orElseThrow();',
            "br.biblioteca.EmprestimosTest#devolucaoNoPrazoNaoGeraMulta", "ServicoBiblioteca.devolver", "RF-04"),
    Cenario("biblioteca_java", "Java", "D3 — exceção na validação do ISBN", "src/main/java/br/biblioteca/servico/Validacoes.java",
            "isbn.replaceAll(", "isbn.substring(14).replaceAll(",
            "br.biblioteca.LivrosTest#rf01CadastraLivroComIsbnValido", "Validacoes.validarIsbn", "RF-01"),
    # --- JavaScript -------------------------------------------------------
    Cenario("biblioteca_javascript", "JavaScript", "D1 — cálculo da multa", "src/validacoes.js",
            "return diasDeAtraso * VALOR_MULTA_DIA;", "return diasDeAtraso * VALOR_MULTA_DIA * 1.5;",
            "test/emprestimos.test.js|multa por dias de atraso", "calcularMulta", "RF-04"),
    Cenario("biblioteca_javascript", "JavaScript", "D2 — exceção na devolução", "src/servicoBiblioteca.js",
            "livro.disponivel = true;", "livro.disponivel = livro.situacao.ativo;",
            "test/emprestimos.test.js|devolução no prazo não gera multa", "ServicoBiblioteca.devolver", "RF-04"),
    Cenario("biblioteca_javascript", "JavaScript", "D3 — exceção na validação do ISBN", "src/validacoes.js",
            "[...isbn]", "[...isbn.digitos]",
            "test/livros.test.js|RF-01 cadastra livro com ISBN válido", "validarIsbn", "RF-01"),
    # --- HTML + JavaScript ------------------------------------------------
    Cenario("biblioteca_html", "HTML + JavaScript", "D1 — cálculo da multa", "js/biblioteca.js",
            "return dias * VALOR_MULTA_DIA;", "return dias * VALOR_MULTA_DIA * 1.5;",
            "test/biblioteca.test.js|multa por dias de atraso", "calcularMulta", "RF-04"),
    Cenario("biblioteca_html", "HTML + JavaScript", "D2 — exceção na devolução", "js/biblioteca.js",
            "livro.disponivel = true;", "livro.disponivel = livro.situacao.ativo;",
            "test/biblioteca.test.js|devolução no prazo não gera multa", "ServicoBiblioteca.devolver", "RF-04"),
    Cenario("biblioteca_html", "HTML + JavaScript", "D3 — exceção na validação do ISBN", "js/biblioteca.js",
            "[...isbn]", "[...isbn.digitos]",
            "test/biblioteca.test.js|RF-01 cadastra livro com ISBN válido", "validarIsbn", "RF-01"),
]

RUNNER_JAVA = """
import java.lang.reflect.*;
/** Executor mínimo: roda um método @Test (JUnit 5) por reflexão e imprime a pilha da falha. */
public class ExecutorTestes {
    public static void main(String[] args) throws Exception {
        String[] partes = args[0].split("#");
        Class<?> c = Class.forName(partes[0]);
        Constructor<?> k = c.getDeclaredConstructor(); k.setAccessible(true);
        Method m = c.getDeclaredMethod(partes[1]); m.setAccessible(true);
        try { m.invoke(k.newInstance()); System.out.println("OK"); }
        catch (InvocationTargetException e) { e.getCause().printStackTrace(System.out); System.exit(1); }
    }
}
"""


def _classpath_junit() -> str | None:
    m2 = Path.home() / ".m2" / "repository"
    padroes = ["org/junit/jupiter/junit-jupiter-api/*/junit-jupiter-api-*.jar", "org/opentest4j/opentest4j/*/*.jar",
               "org/apiguardian/apiguardian-api/*/*.jar", "org/junit/platform/junit-platform-commons/*/*.jar"]
    jars = []
    for padrao in padroes:
        encontrados = sorted(m2.glob(padrao))
        if not encontrados:
            return None
        jars.append(str(encontrados[0]))
    return os.pathsep.join(jars)


def executar_teste(cenario: Cenario, pasta: Path) -> str:
    if cenario.linguagem == "Python":
        comando = [sys.executable, "-m", "pytest", "-q", "--tb=native", "-p", "no:cacheprovider", cenario.teste]
        return subprocess.run(comando, cwd=pasta, capture_output=True, text=True, encoding="utf-8").stdout
    if cenario.linguagem == "Java":
        classpath = _classpath_junit()
        if classpath is None or shutil.which("javac") is None:
            raise RuntimeError("JDK ou bibliotecas do JUnit não encontrados")
        saida = pasta / "_classes"
        (pasta / "ExecutorTestes.java").write_text(RUNNER_JAVA, encoding="utf-8")
        fontes = [str(p) for p in pasta.rglob("*.java") if p.name != "RepositorioNeo4j.java"]
        subprocess.run(["javac", "-encoding", "UTF-8", "-d", str(saida), "-cp", classpath, *fontes],
                       check=True, capture_output=True, text=True)
        resultado = subprocess.run(["java", "-cp", os.pathsep.join([str(saida), classpath]), "ExecutorTestes", cenario.teste],
                                   cwd=pasta, capture_output=True, text=True, encoding="utf-8")
        return resultado.stdout + resultado.stderr
    arquivo, nome = cenario.teste.split("|")
    if shutil.which("node") is None:
        raise RuntimeError("Node.js não encontrado")
    resultado = subprocess.run(["node", "--test", "--test-reporter=spec", f"--test-name-pattern=^{nome}$", arquivo],
                               cwd=pasta, capture_output=True, text=True, encoding="utf-8")
    return resultado.stdout + resultado.stderr


def main() -> int:
    app = create_app(ConfigTeste)
    linhas = []
    with app.app_context():
        usuario = Usuario(nome="Experimento", email="experimento@exemplo.test")
        usuario.definir_senha("senha-do-experimento")
        db.session.add(usuario)
        db.session.commit()
        projetos = {}

        for cenario in CENARIOS:
            with tempfile.TemporaryDirectory() as temporario:
                if cenario.projeto not in projetos:
                    zip_projeto = compactar(ETAPA1 / cenario.projeto, Path(temporario) / "projeto.zip")
                    projetos[cenario.projeto] = services.criar_projeto(
                        usuario, cenario.projeto, analisar_zip(zip_projeto, services.configuracao_da_app()), "projeto.zip")
                versao = projetos[cenario.projeto].versao_atual

                copia = Path(temporario) / cenario.projeto
                shutil.copytree(ETAPA1 / cenario.projeto, copia, ignore=shutil.ignore_patterns("node_modules", "__pycache__"))
                alvo = copia / cenario.arquivo
                conteudo = alvo.read_text(encoding="utf-8")
                if conteudo.count(cenario.antes) != 1:
                    raise SystemExit(f"Mutação ambígua ou ausente em {cenario.arquivo}: {cenario.antes!r}")
                alvo.write_text(conteudo.replace(cenario.antes, cenario.depois), encoding="utf-8")

                try:
                    mensagem = executar_teste(cenario, copia)
                except (RuntimeError, subprocess.CalledProcessError) as erro:
                    print(f"[ignorado] {cenario.linguagem} {cenario.defeito}: {erro}")
                    continue

                resultado = services.localizar_erro(versao, mensagem)
                origem = resultado.get("origem")
                requisitos = [v.origem.identificador for v in resultado.get("requisitos", [])]
                como = "direto"
                if not requisitos:
                    requisitos = [i["requisito"].identificador for i in resultado.get("requisitos_indiretos", [])]
                    como = "herdado" if requisitos else "—"
                suspeitos = set()
                if origem is not None:
                    suspeitos.add(origem.identificador)
                    suspeitos.update(v.destino.identificador for v in resultado.get("codigo", []))
                    suspeitos.update(e.identificador for e in resultado.get("codigo_indireto", []))
                linhas.append({
                    "linguagem": cenario.linguagem,
                    "defeito": cenario.defeito,
                    "origem": origem.identificador if origem else "—",
                    "tipo_origem": ("teste" if origem.eh_teste else "código") if origem else "—",
                    "requisitos": (", ".join(requisitos) + (" (herdado)" if como == "herdado" else "")) or "—",
                    "como": como,
                    "requisito_correto": cenario.requisito in requisitos,
                    "requisito_primeiro": bool(requisitos) and requisitos[0] == cenario.requisito,
                    "defeito_localizado": cenario.elemento_defeituoso in suspeitos,
                    "origem_e_o_defeito": origem is not None and origem.identificador == cenario.elemento_defeituoso,
                    "testes": len(resultado.get("testes", [])),
                    "impacto": len(resultado.get("impacto", [])),
                    "mensagem": mensagem,
                })

    def sim(valor):
        return "Sim" if valor else "Não"

    md = ["# Experimento de localização de erros — 1ª etapa", "",
          "| Linguagem | Defeito inserido | Origem apontada | Requisitos apontados | Requisito correto? | "
          "Elemento defeituoso entre os suspeitos? |",
          "|---|---|---|---|---|---|"]
    for l in linhas:
        md.append(f"| {l['linguagem']} | {l['defeito']} | `{l['origem']}` ({l['tipo_origem']}) | {l['requisitos']} | "
                  f"{sim(l['requisito_correto'])} | {sim(l['defeito_localizado'])} |")
    total = len(linhas)
    if total:
        herdados = sum(1 for l in linhas if l["requisito_correto"] and l["como"] == "herdado")
        md += ["", f"- Requisito correto apontado: {sum(l['requisito_correto'] for l in linhas)} de {total} cenários "
                   f"({sum(l['requisito_primeiro'] for l in linhas)} em 1º lugar; {herdados} herdado(s) pelo grafo de chamadas).",
               f"- Elemento defeituoso entre os suspeitos: {sum(l['defeito_localizado'] for l in linhas)} de {total}.",
               f"- Origem apontada exatamente no elemento defeituoso: {sum(l['origem_e_o_defeito'] for l in linhas)} de {total} "
               "(nos defeitos de cálculo o erro aparece na asserção do teste, e a ferramenta aponta o teste e o código que ele exercita)."]
    md += ["", "## Mensagens de erro utilizadas", ""]
    for l in linhas:
        trecho = "\n".join(l["mensagem"].strip().splitlines()[:25])
        md += [f"### {l['linguagem']} — {l['defeito']}", "", "```", trecho, "```", ""]

    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "experimento_localizacao.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[: 8 + total + 4]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
