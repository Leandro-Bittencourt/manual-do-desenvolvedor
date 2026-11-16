import re

from app import create_app
from app.config import ConfigTeste
from app.extensions import db
from app.models import Decisao, Projeto, Usuario, Vinculo
from conftest import EXEMPLO, enviar_zip, zip_de_dicionario, zip_de_pasta


def _projeto(app) -> Projeto:
    with app.app_context():
        return db.session.query(Projeto).one()


def test_paginas_exigem_login(cliente):
    resposta = cliente.get("/painel")
    assert resposta.status_code == 302 and "/entrar" in resposta.headers["Location"]


def test_cadastro_login_e_logout(cliente, app):
    resposta = cliente.post("/cadastrar", data={
        "nome": "Ana", "email": "Ana@Exemplo.com", "senha": "senha-segura", "confirmacao": "senha-segura",
    })
    assert resposta.status_code == 302
    with app.app_context():
        usuario = db.session.query(Usuario).one()
        assert usuario.email == "ana@exemplo.com"
        assert usuario.senha_hash != "senha-segura"  # senha nunca em texto puro

    cliente.post("/sair")
    errado = cliente.post("/entrar", data={"email": "ana@exemplo.com", "senha": "errada"})
    assert "E-mail ou senha incorretos" in errado.get_data(as_text=True)
    certo = cliente.post("/entrar", data={"email": "ana@exemplo.com", "senha": "senha-segura"})
    assert certo.status_code == 302


def test_cadastro_valida_dados(cliente):
    resposta = cliente.post("/cadastrar", data={"nome": "", "email": "x", "senha": "123", "confirmacao": "321"})
    html = resposta.get_data(as_text=True)
    for mensagem in ["Informe seu nome", "e-mail válido", "pelo menos 8", "não confere"]:
        assert mensagem in html


def test_envio_do_projeto_e_telas(cliente_logado, app, tmp_path):
    resposta = enviar_zip(cliente_logado, zip_de_pasta(EXEMPLO, tmp_path / "loja.zip"))
    assert resposta.status_code == 302
    projeto = _projeto(app)

    for caminho in ["", "/requisitos", "/requisitos?filtro=sem_teste", "/codigo", "/testes",
                    "/revisao", "/revisao?situacao=todos&faixa=alta", "/localizar"]:
        pagina = cliente_logado.get(f"/projetos/{projeto.id}{caminho}")
        assert pagina.status_code == 200, caminho

    html = cliente_logado.get(f"/projetos/{projeto.id}/requisitos").get_data(as_text=True)
    assert "RF-05" in html and "processar_pagamento" in html
    assert cliente_logado.get("/painel").status_code == 200

    exportado = cliente_logado.get(f"/projetos/{projeto.id}/exportar.json").get_json()
    assert exportado["metricas"]["requisitos"] == 6 and exportado["vinculos"]


def test_zip_invalido_mostra_erro(cliente_logado, tmp_path):
    falso = tmp_path / "falso.zip"
    falso.write_text("não é zip")
    resposta = enviar_zip(cliente_logado, falso)
    assert resposta.status_code == 200
    assert "não é um ZIP válido" in resposta.get_data(as_text=True)


def test_localizar_erro_a_partir_do_traceback(cliente_logado, app, tmp_path):
    enviar_zip(cliente_logado, zip_de_pasta(EXEMPLO, tmp_path / "loja.zip"))
    projeto = _projeto(app)
    linha = next(i for i, l in enumerate((EXEMPLO / "src/loja/carrinho.py").read_text().splitlines(), 1)
                 if "return aplicar_desconto" in l)
    traceback = (
        'Traceback (most recent call last):\n'
        '  File "/home/dev/loja/tests/test_carrinho.py", line 20, in test_total_com_cupom\n'
        f'  File "/home/dev/loja/src/loja/carrinho.py", line {linha}, in calcular_total\n'
        "KeyError: 'XYZ'\n"
    )
    html = cliente_logado.post(f"/projetos/{projeto.id}/localizar", data={"erro": traceback}).get_data(as_text=True)
    assert "Provável origem" in html and "Carrinho.calcular_total" in html
    assert "RF-04" in html  # requisito relacionado
    assert "test_total_com_cupom" in html  # teste a executar novamente
    assert "processar_pagamento" in html  # função que chama a origem (impacto)

    por_nome = cliente_logado.post(f"/projetos/{projeto.id}/localizar",
                                   data={"erro": "tests/test_pagamento.py::test_cartao_invalido_recusado"})
    html_teste = por_nome.get_data(as_text=True)
    assert "processar_pagamento" in html_teste
    assert "Chamado indiretamente" in html_teste and "validar_cartao" in html_teste  # chamado por processar_pagamento


def test_requisito_herdado_pelo_grafo_de_chamadas(cliente_logado, app, tmp_path):
    arquivos = {
        "requisitos.md": "## RF-01 Cadastro\nCadastrar clientes.\n",
        "app.py": "def cadastrar(c):\n    # @traces RF-01\n    return normalizar(c)\n\n\n"
                  "def normalizar(c):\n    return c.strip()\n",
    }
    enviar_zip(cliente_logado, zip_de_dicionario(tmp_path / "p.zip", arquivos))
    projeto = _projeto(app)
    traceback = 'Traceback (most recent call last):\n  File "/x/app.py", line 7, in normalizar\nAttributeError\n'
    html = cliente_logado.post(f"/projetos/{projeto.id}/localizar", data={"erro": traceback}).get_data(as_text=True)
    assert "Provável origem" in html and "normalizar" in html
    assert "herdados pelo grafo de chamadas" in html and "RF-01" in html


def test_decisoes_sao_mantidas_e_mudancas_vao_para_revisao(cliente_logado, app, tmp_path):
    arquivos = {
        "requisitos.md": "## RF-01 Somar\nSomar dois números.\n## RF-02 Subtrair\nSubtrair dois números.\n",
        "calc.py": "def somar(a, b):\n    # @traces RF-01\n    return a + b\n\n\n"
                   "def subtrair(a, b):\n    # RF-02\n    return a - b\n",
    }
    enviar_zip(cliente_logado, zip_de_dicionario(tmp_path / "v1.zip", arquivos))
    projeto = _projeto(app)

    with app.app_context():
        vinculos = {v.destino.identificador: v.id for v in db.session.query(Vinculo).all() if v.origem.eh_requisito}
    for nome, acao in [("somar", "confirmar"), ("subtrair", "rejeitar")]:
        r = cliente_logado.post(f"/projetos/{projeto.id}/vinculos/{vinculos[nome]}/decisao", data={"acao": acao})
        assert r.status_code == 302
    with app.app_context():
        assert db.session.query(Decisao).count() == 2

    # versão 2: "somar" mudou; "subtrair" continua igual
    arquivos["calc.py"] = arquivos["calc.py"].replace("return a + b", "return float(a) + float(b)")
    r = enviar_zip(cliente_logado, zip_de_dicionario(tmp_path / "v2.zip", arquivos),
                   url=f"/projetos/{projeto.id}/versoes")
    assert r.status_code == 302
    with app.app_context():
        projeto = db.session.get(Projeto, projeto.id)
        situacao = {v.destino.identificador: v.status for v in projeto.versao_atual.vinculos if v.origem.eh_requisito}
    assert situacao == {"somar": "a_revisar", "subtrair": "rejeitado"}


def test_projeto_html_exibe_elementos_de_interface(cliente_logado, app, tmp_path):
    pasta = EXEMPLO.parent / "etapa1" / "biblioteca_html"
    enviar_zip(cliente_logado, zip_de_pasta(pasta, tmp_path / "html.zip", prefixo="biblioteca_html"))
    projeto = _projeto(app)
    codigo = cliente_logado.get(f"/projetos/{projeto.id}/codigo").get_data(as_text=True)
    assert "form#form-livro" in codigo and "Interface" in codigo
    visao = cliente_logado.get(f"/projetos/{projeto.id}").get_data(as_text=True)
    assert "HTML" in visao and "JavaScript" in visao  # arquivos por linguagem


def test_usuario_nao_acessa_projeto_de_outro(cliente_logado, app, tmp_path):
    enviar_zip(cliente_logado, zip_de_pasta(EXEMPLO, tmp_path / "loja.zip"))
    projeto = _projeto(app)
    cliente_logado.post("/sair")
    cliente_logado.post("/cadastrar", data={
        "nome": "Bia", "email": "bia@exemplo.com", "senha": "outra-senha", "confirmacao": "outra-senha",
    })
    assert cliente_logado.get(f"/projetos/{projeto.id}").status_code == 404
    assert cliente_logado.post(f"/projetos/{projeto.id}/excluir").status_code == 404


def test_excluir_projeto_remove_todos_os_dados(cliente_logado, app, tmp_path):
    enviar_zip(cliente_logado, zip_de_pasta(EXEMPLO, tmp_path / "loja.zip"))
    projeto = _projeto(app)
    cliente_logado.post(f"/projetos/{projeto.id}/excluir")
    with app.app_context():
        assert db.session.query(Projeto).count() == 0
        assert db.session.query(Vinculo).count() == 0


def test_formularios_exigem_token_csrf(tmp_path):
    class ConfigComCsrf(ConfigTeste):
        CSRF_ATIVO = True

    app = create_app(ConfigComCsrf)
    cliente = app.test_client()
    dados = {"nome": "Ana", "email": "ana@exemplo.com", "senha": "senha-segura", "confirmacao": "senha-segura"}
    assert cliente.post("/cadastrar", data=dados).status_code == 400

    pagina = cliente.get("/cadastrar").get_data(as_text=True)
    token = re.search(r'name="csrf_token" value="([^"]+)"', pagina).group(1)
    assert cliente.post("/cadastrar", data={**dados, "csrf_token": token}).status_code == 302
    with app.app_context():
        db.drop_all()


def test_cabecalhos_de_seguranca(cliente):
    resposta = cliente.get("/entrar")
    assert resposta.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in resposta.headers["Content-Security-Policy"]
