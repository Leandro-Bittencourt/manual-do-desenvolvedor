"""Leitura de Java, JavaScript e HTML."""

from app.analysis.codigo import analisar_codigo
from app.analysis.codigo_base import eh_arquivo_de_producao, eh_arquivo_de_teste, modulo_de
from app.analysis.estrategias import estrategia_e1, estrategia_e2
from app.analysis.localizador import extrair_quadros
from app.analysis.modelos import Artefato
from app.analysis.requisitos import compilar_padrao
from app.analysis.resolvedor import Resolvedor

JAVA_SERVICO = """package br.biblioteca;

import br.biblioteca.modelo.Livro;

public class Servico {
    private final Repositorio repositorio;

    public Servico(Repositorio repositorio) { this.repositorio = repositorio; }

    /** Implementa RF-03: empréstimo de livros. */
    public Emprestimo emprestar(String isbn) {
        Livro livro = repositorio.buscar(isbn);
        // verifica a disponibilidade
        return new Emprestimo(livro);
    }
}

interface Repositorio {
    Livro buscar(String isbn);
}
"""

JAVA_TESTE = """package br.biblioteca;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ServicoTest {
    @Test
    void rf03EmprestaLivro() {
        Servico servico = new Servico(new RepositorioFalso());
        assertNotNull(servico.emprestar("123"));
    }

    void auxiliar() {}
}
"""

JS_MODULO = """import { MongoClient } from "mongodb";

// @traces RF-01
export function cadastrarLivro(repo, livro) {
  return repo.inserir(livro);
}

export const buscarLivros = (repo, termo) => repo.todos().filter((l) => l.titulo.includes(termo));

export class Biblioteca {
  constructor(repo) { this.repo = repo; }
  emprestar(isbn) { return this.repo.marcarEmprestado(isbn); }
}
"""

JS_TESTE = """import { test, describe } from "node:test";
import assert from "node:assert";
import { cadastrarLivro, Biblioteca } from "../src/livros.js";

describe("Livros", () => {
  test("RF-01 cadastra livro", () => {
    assert.ok(cadastrarLivro(repoFalso(), {}));
  });
  it("empresta livro", async () => {
    const b = new Biblioteca(repoFalso());
    await b.emprestar("1");
  });
});

test("formulário de cadastro", async ({ page }) => {
  await page.fill("#titulo", "Dom Casmurro");
  await page.click("#btn-cadastrar-livro");
});
"""

HTML = """<!doctype html>
<html>
<body>
  <!-- @traces RF-01 -->
  <form id="form-livro">
    <h2>Cadastrar livro</h2>
    <input id="titulo" placeholder="Título do livro">
    <button id="btn-cadastrar-livro" type="submit">Cadastrar</button>
  </form>
  <section id="busca" data-requisito="RF-05">
    <input id="termo" aria-label="Buscar por título ou autor">
  </section>
  <script>const x = "#nao-conta";</script>
</body>
</html>
"""


def _escrever(tmp_path, arquivos):
    for relativo, conteudo in arquivos.items():
        caminho = tmp_path / relativo
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(conteudo, encoding="utf-8")
    artefatos, avisos, por_linguagem = analisar_codigo(tmp_path, list(arquivos))
    return {a.identificador: a for a in artefatos}, avisos, por_linguagem


def test_classificacao_de_arquivos_por_linguagem():
    assert eh_arquivo_de_teste("src/test/java/br/app/ServicoTest.java")
    assert eh_arquivo_de_teste("test/livros.test.js") and eh_arquivo_de_teste("e2e/app.spec.js")
    assert not eh_arquivo_de_teste("web/index.html")
    assert eh_arquivo_de_producao("src/main/java/br/app/Servico.java")
    assert eh_arquivo_de_producao("web/index.html")
    assert not eh_arquivo_de_producao("playwright.config.js")
    assert modulo_de("src/main/java/br/app/Servico.java") == "src.main.java.br.app"
    assert modulo_de("src/livros.js") == "src.livros"


def test_java_classes_metodos_testes_e_chamadas(tmp_path):
    artefatos, avisos, por_linguagem = _escrever(tmp_path, {
        "src/main/java/br/biblioteca/Servico.java": JAVA_SERVICO,
        "src/test/java/br/biblioteca/ServicoTest.java": JAVA_TESTE,
    })
    assert por_linguagem == {"java": 2} and avisos == []
    tipos = {nome: a.tipo for nome, a in artefatos.items()}
    # construtor, método abstrato da interface e método sem @Test ficam de fora
    assert tipos == {"Servico": "classe", "Servico.emprestar": "metodo", "Repositorio": "classe",
                     "ServicoTest.rf03EmprestaLivro": "teste"}
    emprestar = artefatos["Servico.emprestar"]
    assert (emprestar.linha_inicio, emprestar.linha_fim) == (11, 15)  # o Javadoc (linha 10) vira comentário
    assert {c.alvo for c in emprestar.chamadas} == {"repositorio.buscar", "Emprestimo"}
    assert [t for _, t in emprestar.comentarios] == ["Implementa RF-03: empréstimo de livros.",
                                                    "verifica a disponibilidade"]
    assert emprestar.importacoes["Livro"] == "br.biblioteca.modelo.Livro"
    teste = artefatos["ServicoTest.rf03EmprestaLivro"]
    assert {"Servico", "servico.emprestar"} <= {c.alvo for c in teste.chamadas}


def test_javascript_funcoes_classes_testes_e_importacoes(tmp_path):
    artefatos, avisos, _ = _escrever(tmp_path, {"src/livros.js": JS_MODULO, "test/livros.test.js": JS_TESTE})
    assert avisos == []
    tipos = {nome: a.tipo for nome, a in artefatos.items()}
    assert tipos == {
        "cadastrarLivro": "funcao", "buscarLivros": "funcao", "Biblioteca": "classe",
        "Biblioteca.emprestar": "metodo", "Livros > RF-01 cadastra livro": "teste",
        "Livros > empresta livro": "teste", "formulário de cadastro": "teste",
    }
    assert [t for _, t in artefatos["cadastrarLivro"].comentarios] == ["@traces RF-01"]
    teste = artefatos["Livros > RF-01 cadastra livro"]
    assert teste.importacoes["cadastrarLivro"] == "src.livros.cadastrarLivro"
    assert "cadastrarLivro" in {c.alvo for c in teste.chamadas}
    interface = artefatos["formulário de cadastro"]
    assert {"#titulo", "#btn-cadastrar-livro"} <= {c.alvo for c in interface.chamadas}


def test_html_elementos_de_interface(tmp_path):
    artefatos, _, por_linguagem = _escrever(tmp_path, {"web/index.html": HTML})
    assert por_linguagem == {"html": 1}
    assert set(artefatos) == {"form#form-livro", "button#btn-cadastrar-livro", "section#busca"}
    formulario = artefatos["form#form-livro"]
    assert (formulario.tipo, formulario.linha_inicio, formulario.linha_fim) == ("interface", 5, 9)
    assert "Cadastrar livro" in formulario.descricao and "Título do livro" in formulario.descricao
    assert "#titulo" in formulario.termos  # campo interno, usado pelos seletores dos testes
    assert [t for _, t in formulario.comentarios] == ["@traces RF-01"]
    assert artefatos["section#busca"].docstring == "RF-05"
    assert "#nao-conta" not in " ".join(a.descricao for a in artefatos.values())  # conteúdo de <script> ignorado


def test_testes_de_interface_ligam_ao_html_e_marcacoes_funcionam(tmp_path):
    artefatos, _, _ = _escrever(tmp_path, {"web/index.html": HTML, "test/livros.test.js": JS_TESTE,
                                          "src/livros.js": JS_MODULO})
    lista = list(artefatos.values())
    codigo = [a for a in lista if a.eh_codigo]
    testes = [a for a in lista if a.eh_teste]
    e2 = estrategia_e2(testes, Resolvedor(codigo))
    nomes = {(artefatos_por_chave(lista)[o], artefatos_por_chave(lista)[d]) for o, d in e2}
    assert ("formulário de cadastro", "form#form-livro") in nomes
    assert ("formulário de cadastro", "button#btn-cadastrar-livro") in nomes
    assert ("Livros > empresta livro", "Biblioteca.emprestar") in nomes

    requisitos = {f"REQ:{i}": Artefato(chave=f"REQ:{i}", tipo="requisito", identificador=i, nome=i)
                  for i in ("RF-1", "RF-5")}
    e1, _ = estrategia_e1(requisitos, codigo + testes, compilar_padrao())
    destinos = {(o, artefatos_por_chave(lista)[d]) for o, d in e1}
    assert {("REQ:RF-1", "form#form-livro"), ("REQ:RF-5", "section#busca"),
            ("REQ:RF-1", "cadastrarLivro"), ("REQ:RF-1", "Livros > RF-01 cadastra livro")} <= destinos


def artefatos_por_chave(lista):
    return {a.chave: a.identificador for a in lista}


def test_pilhas_de_java_e_javascript_sao_invertidas():
    java = """java.lang.IllegalStateException: Livro indisponível
	at br.biblioteca.Servico.emprestar(Servico.java:13)
	at br.biblioteca.ServicoTest.rf03EmprestaLivro(ServicoTest.java:10)
	at java.base/jdk.internal.reflect.Method.invoke(Method.java:568)"""
    quadros = extrair_quadros(java)
    assert [(q.arquivo, q.linha) for q in quadros][-2:] == [("ServicoTest.java", 10), ("Servico.java", 13)]

    js = """Error: Livro indisponível
    at emprestar (file:///C:/projeto/src/emprestimos.js:42:11)
    at TestContext.<anonymous> (file:///C:/projeto/test/emprestimos.test.js:20:5)
    at node:internal/test_runner/test:935:25"""
    quadros = extrair_quadros(js)
    assert [(q.arquivo, q.linha) for q in quadros] == [
        ("C:/projeto/test/emprestimos.test.js", 20), ("C:/projeto/src/emprestimos.js", 42)]


def test_relatorio_do_node_test_ignora_cabecalho_e_aceita_async():
    saida = """test at test\\emprestimos.test.js:36:3
✖ devolução no prazo não gera multa (1.2ms)
  TypeError [Error]: Cannot read properties of undefined (reading 'ativo')
      at ServicoBiblioteca.devolver (file:///C:/tmp/src/servicoBiblioteca.js:61:39)
      at async TestContext.<anonymous> (file:///C:/tmp/test/emprestimos.test.js:39:18)
      at async Test.run (node:internal/test_runner/test:980:9)"""
    quadros = extrair_quadros(saida)
    assert [(q.arquivo.split("/")[-1], q.linha) for q in quadros] == [
        ("emprestimos.test.js", 39), ("servicoBiblioteca.js", 61)]  # o mais interno (origem) fica por último
