"""Gera os gabaritos de referência dos 4 projetos controlados da 1ª etapa.

Os vínculos corretos foram definidos pelo pesquisador antes da avaliação,
seguindo os critérios registrados em cada arquivo.

Uso:
    python scripts/gerar_gabaritos_etapa1.py
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "exemplos" / "etapa1"
CRITERIOS = [
    "Requisito -> código: elementos que implementam diretamente o comportamento do requisito (método de serviço, "
    "funções de validação e de cálculo e, no projeto HTML, também o formulário e a função de tela). "
    "Para o RNF-01 (persistência), a classe de acesso ao banco de dados.",
    "Requisito -> teste: testes que verificam o requisito.",
    "Teste -> código: elementos de produção chamados diretamente no corpo do teste (inclui classes instanciadas, "
    "getters e referências a métodos). Dublês de teste e funções auxiliares não entram.",
]


def gabarito(nome, descricao, rc, rt, tc):
    vinculos = []
    for req, alvos in rc.items():
        vinculos += [{"origem": req, "destino": a} for a in alvos]
    for req, testes in rt.items():
        vinculos += [{"origem": req, "destino": t} for t in testes]
    for teste, alvos in tc.items():
        vinculos += [{"origem": teste, "destino": a} for a in alvos]
    dados = {"projeto": nome, "descricao": descricao, "criterios": CRITERIOS, "vinculos": vinculos}
    destino = BASE / f"gabarito_{nome}.json"
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{destino.name}: {len(vinculos)} vínculos")


def python():
    s, m = "src/biblioteca/servicos.py::", "src/biblioteca/modelos.py::"
    sv = s + "ServicoBiblioteca"

    def t(arquivo, nome):
        return f"tests/{arquivo}::{nome}"

    rf01 = [t("test_livros.py", n) for n in ("test_rf01_cadastra_livro_com_isbn_valido", "test_rejeita_isbn_invalido",
                                             "test_rejeita_isbn_repetido")]
    rf02 = [t("test_leitores.py", n) for n in ("test_cadastra_leitor", "test_rf02_rejeita_email_invalido")]
    rf03 = [t("test_emprestimos.py", n) for n in ("test_empresta_livro_disponivel", "test_limite_de_tres_emprestimos_ativos")]
    rf04 = [t("test_emprestimos.py", n) for n in ("test_devolucao_no_prazo_nao_gera_multa", "test_multa_por_dias_de_atraso")]
    rf05 = [t("test_busca.py", "test_busca_por_titulo_ou_autor_sem_diferenciar_maiusculas")]
    gabarito(
        "biblioteca_python", "Projeto 1 — Python + PostgreSQL (relacional)",
        {"RF-01": [sv + ".cadastrar_livro", s + "validar_isbn"], "RF-02": [sv + ".cadastrar_leitor", s + "validar_email"],
         "RF-03": [sv + ".emprestar"], "RF-04": [sv + ".devolver", s + "calcular_multa", m + "Emprestimo.dias_de_atraso"],
         "RF-05": [sv + ".buscar_livros"], "RNF-01": ["src/biblioteca/repositorio.py::RepositorioPostgres"]},
        {"RF-01": rf01, "RF-02": rf02, "RF-03": rf03, "RF-04": rf04, "RF-05": rf05},
        {**{x: [sv, sv + ".cadastrar_livro"] for x in rf01},
         **{x: [sv, sv + ".cadastrar_leitor"] for x in rf02},
         **{x: [sv + ".emprestar"] for x in rf03},
         **{x: [sv + ".emprestar", sv + ".devolver"] for x in rf04},
         rf05[0]: [sv, sv + ".cadastrar_livro", sv + ".buscar_livros"]},
    )


def java():
    j = "src/main/java/br/biblioteca/"
    sv = j + "servico/ServicoBiblioteca.java::ServicoBiblioteca"
    v = j + "servico/Validacoes.java::Validacoes."
    livro = j + "modelo/Livro.java::Livro."

    def t(classe, nome):
        return f"src/test/java/br/biblioteca/{classe}.java::{classe}.{nome}"

    rf01 = [t("LivrosTest", n) for n in ("rf01CadastraLivroComIsbnValido", "rejeitaIsbnInvalido", "rejeitaIsbnRepetido")]
    rf02 = [t("LeitoresTest", n) for n in ("cadastraLeitor", "rf02RejeitaEmailInvalido")]
    rf03 = [t("EmprestimosTest", n) for n in ("emprestaLivroDisponivel", "limiteDeTresEmprestimosAtivos")]
    rf04 = [t("EmprestimosTest", n) for n in ("devolucaoNoPrazoNaoGeraMulta", "multaPorDiasDeAtraso")]
    rf05 = [t("BuscaTest", "buscaPorTituloOuAutorSemDiferenciarMaiusculas")]
    gabarito(
        "biblioteca_java", "Projeto 2 — Java + Neo4j (grafo)",
        {"RF-01": [sv + ".cadastrarLivro", v + "validarIsbn"], "RF-02": [sv + ".cadastrarLeitor", v + "validarEmail"],
         "RF-03": [sv + ".emprestar"],
         "RF-04": [sv + ".devolver", v + "calcularMulta", j + "modelo/Emprestimo.java::Emprestimo.diasDeAtraso"],
         "RF-05": [sv + ".buscarLivros"], "RNF-01": [j + "repositorio/RepositorioNeo4j.java::RepositorioNeo4j"]},
        {"RF-01": rf01, "RF-02": rf02, "RF-03": rf03, "RF-04": rf04, "RF-05": rf05},
        {rf01[0]: [sv, sv + ".cadastrarLivro", livro + "isDisponivel"],
         rf01[1]: [sv, sv + ".cadastrarLivro"], rf01[2]: [sv, sv + ".cadastrarLivro"],
         **{x: [sv, sv + ".cadastrarLeitor"] for x in rf02},
         rf03[0]: [sv + ".emprestar", livro + "isDisponivel"], rf03[1]: [sv + ".emprestar"],
         **{x: [sv + ".emprestar", sv + ".devolver"] for x in rf04},
         rf05[0]: [sv, sv + ".cadastrarLivro", sv + ".buscarLivros", livro + "getTitulo"]},
    )


def javascript():
    sv = "src/servicoBiblioteca.js::ServicoBiblioteca"
    va = "src/validacoes.js::"
    rf01 = [f"test/livros.test.js::Cadastro de livros > {n}" for n in
            ("RF-01 cadastra livro com ISBN válido", "rejeita ISBN inválido", "rejeita ISBN repetido")]
    rf02 = [f"test/leitores.test.js::Cadastro de leitores > {n}" for n in ("cadastra leitor", "RF-02 rejeita e-mail inválido")]
    emp = "test/emprestimos.test.js::Empréstimos e devoluções > "
    rf03 = [emp + "empresta livro disponível", emp + "limite de três empréstimos ativos"]
    rf04 = [emp + "devolução no prazo não gera multa", emp + "multa por dias de atraso"]
    rf05 = ["test/busca.test.js::busca por título ou autor sem diferenciar maiúsculas"]
    gabarito(
        "biblioteca_javascript", "Projeto 3 — JavaScript (Node.js) + MongoDB (documentos)",
        {"RF-01": [sv + ".cadastrarLivro", va + "validarIsbn"], "RF-02": [sv + ".cadastrarLeitor", va + "validarEmail"],
         "RF-03": [sv + ".emprestar"], "RF-04": [sv + ".devolver", va + "calcularMulta", "src/modelos.js::Emprestimo.diasDeAtraso"],
         "RF-05": [sv + ".buscarLivros"], "RNF-01": ["src/repositorioMongo.js::RepositorioMongo"]},
        {"RF-01": rf01, "RF-02": rf02, "RF-03": rf03, "RF-04": rf04, "RF-05": rf05},
        {**{x: [sv, sv + ".cadastrarLivro"] for x in rf01},
         **{x: [sv, sv + ".cadastrarLeitor"] for x in rf02},
         **{x: [sv + ".emprestar"] for x in rf03},
         **{x: [sv + ".emprestar", sv + ".devolver"] for x in rf04},
         rf05[0]: [sv, sv + ".cadastrarLivro", sv + ".buscarLivros"]},
    )


def html():
    b, ap, h = "js/biblioteca.js::", "js/app.js::", "index.html::"
    sv = b + "ServicoBiblioteca"
    un = "test/biblioteca.test.js::"
    e2e = "e2e/biblioteca.spec.js::"
    rf01 = [un + "Cadastro de livros > " + n for n in
            ("RF-01 cadastra livro com ISBN válido", "rejeita ISBN inválido", "rejeita ISBN repetido")]
    rf02 = [un + "Cadastro de leitores > " + n for n in ("cadastra leitor", "RF-02 rejeita e-mail inválido")]
    emp = un + "Empréstimos e devoluções > "
    rf03 = [emp + "empresta livro disponível", emp + "limite de três empréstimos ativos"]
    rf04 = [emp + "devolução no prazo não gera multa", emp + "multa por dias de atraso"]
    rf05 = [un + "busca por título ou autor sem diferenciar maiúsculas"]
    i_livro, i_emp, i_busca = (e2e + "RF-01 cadastra livro pela interface", e2e + "empresta e devolve livro pela interface",
                               e2e + "busca livros pela interface")
    gabarito(
        "biblioteca_html", "Projeto 4 — HTML + JavaScript no navegador + localStorage (chave-valor)",
        {"RF-01": [sv + ".cadastrarLivro", b + "validarIsbn", ap + "aoCadastrarLivro", h + "form#form-livro"],
         "RF-02": [sv + ".cadastrarLeitor", b + "validarEmail", ap + "aoCadastrarLeitor", h + "form#form-leitor"],
         "RF-03": [sv + ".emprestar", ap + "aoEmprestar", h + "form#form-emprestimo"],
         "RF-04": [sv + ".devolver", b + "calcularMulta", b + "diasDeAtraso", ap + "aoDevolver", h + "form#form-devolucao"],
         "RF-05": [sv + ".buscarLivros", ap + "aoBuscar", h + "form#form-busca", h + "ul#lista-resultados"],
         "RNF-01": ["js/armazenamento.js::ArmazenamentoLocal"]},
        {"RF-01": [*rf01, i_livro], "RF-02": rf02, "RF-03": [*rf03, i_emp], "RF-04": [*rf04, i_emp], "RF-05": [*rf05, i_busca]},
        {**{x: [sv + ".cadastrarLivro"] for x in rf01},
         **{x: [sv + ".cadastrarLeitor"] for x in rf02},
         rf03[0]: [sv + ".emprestar", "js/armazenamento.js::ArmazenamentoLocal.buscarLivro"], rf03[1]: [sv + ".emprestar"],
         **{x: [sv + ".emprestar", sv + ".devolver"] for x in rf04},
         rf05[0]: [sv + ".cadastrarLivro", sv + ".buscarLivros"],
         i_livro: [h + "form#form-livro"],
         i_emp: [h + "form#form-livro", h + "form#form-leitor", h + "form#form-emprestimo", h + "form#form-devolucao"],
         i_busca: [h + "form#form-livro", h + "form#form-busca", h + "ul#lista-resultados"]},
    )


if __name__ == "__main__":
    python()
    java()
    javascript()
    html()
