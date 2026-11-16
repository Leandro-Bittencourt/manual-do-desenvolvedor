import pytest

from app.analysis import texto
from app.analysis.confianca import combinar, faixa
from app.analysis.estrategias import estrategia_e1, estrategia_e2, estrategia_e3, estrategia_e4
from app.analysis.modelos import Artefato, Chamada, Evidencia
from app.analysis.requisitos import compilar_padrao
from app.analysis.resolvedor import Resolvedor

PADRAO = compilar_padrao()


def req(ident, titulo, descricao=""):
    canon = ident.split("-")[0] + "-" + str(int(ident.split("-")[1]))
    return Artefato(chave=f"REQ:{canon}", tipo="requisito", identificador=ident, nome=titulo, descricao=descricao)


def codigo(qual, modulo="loja.carrinho", tipo="metodo", **extra):
    return Artefato(chave=f"CODE:{modulo}::{qual}", tipo=tipo, identificador=qual,
                    nome=qual.split(".")[-1], modulo=modulo, arquivo=modulo.replace(".", "/") + ".py",
                    linha_inicio=1, linha_fim=5, **extra)


def um_teste(nome, **extra):
    return Artefato(chave=f"TEST:tests/test_x.py::{nome}", tipo="teste", identificador=nome, nome=nome,
                    arquivo="tests/test_x.py", linha_inicio=1, linha_fim=5, **extra)


# --- E1 ------------------------------------------------------------------
def test_e1_encontra_marcacoes_em_nome_docstring_e_comentario():
    requisitos = {r.chave: r for r in [req("RF-01", "Login"), req("RF-02", "Logout"), req("RF-03", "Busca")]}
    alvos = [
        um_teste("test_rf01_login"),
        codigo("Sessao.sair", docstring="Implementa RF-02."),
        codigo("buscar", tipo="funcao", comentarios=[(3, "@traces RF-03 e RF-99")]),
    ]
    vinculos, avisos = estrategia_e1(requisitos, alvos, PADRAO)
    assert set(vinculos) == {
        ("REQ:RF-1", alvos[0].chave), ("REQ:RF-2", alvos[1].chave), ("REQ:RF-3", alvos[2].chave),
    }
    assert all(e.pontuacao == 1.0 for evid in vinculos.values() for e in evid)
    assert "RF-99" in avisos[0]  # identificador citado que não existe nos requisitos


# --- E2 ------------------------------------------------------------------
def test_e2_resolve_chamadas_por_importacao_e_por_nome():
    adicionar = codigo("Carrinho.adicionar")
    classe = codigo("Carrinho", tipo="classe")
    pagar = codigo("processar", modulo="loja.pagamento", tipo="funcao")
    t = um_teste(
        "test_compra",
        chamadas=[Chamada("Carrinho", 3), Chamada("c.adicionar", 4), Chamada("processar", 5), Chamada("len", 6)],
        importacoes={"Carrinho": "loja.carrinho.Carrinho", "processar": "loja.pagamento.processar"},
    )
    vinculos = estrategia_e2([t], Resolvedor([adicionar, classe, pagar]))
    assert {d for _, d in vinculos} == {adicionar.chave, classe.chave, pagar.chave}
    assert all(e.pontuacao == 1.0 for evid in vinculos.values() for e in evid)


def test_e2_nome_ambiguo_divide_a_pontuacao():
    a = codigo("Pedido.salvar", modulo="loja.pedido")
    b = codigo("Cliente.salvar", modulo="loja.cliente")
    t = um_teste("test_salvar", chamadas=[Chamada("obj.salvar", 3)])
    vinculos = estrategia_e2([t], Resolvedor([a, b]))
    assert sorted(e.pontuacao for evid in vinculos.values() for e in evid) == [0.5, 0.5]


def test_e2_ambiguidade_resolvida_pelo_modulo_importado():
    a = codigo("Pedido.salvar", modulo="loja.pedido")
    b = codigo("Cliente.salvar", modulo="loja.cliente")
    t = um_teste("test_salvar", chamadas=[Chamada("p.salvar", 3)], importacoes={"Pedido": "loja.pedido.Pedido"})
    vinculos = estrategia_e2([t], Resolvedor([a, b]))
    assert list(vinculos) == [(t.chave, a.chave)]


# --- E3 ------------------------------------------------------------------
def test_e3_infere_requisito_para_codigo_via_teste():
    r, t, f, classe = req("RF-01", "Login"), um_teste("test_login"), codigo("login", tipo="funcao"), codigo("Sessao", tipo="classe")
    artefatos = {a.chave: a for a in (r, t, f, classe)}
    vinculos = estrategia_e3({(r.chave, t.chave): 0.9}, {(t.chave, f.chave): 1.0, (t.chave, classe.chave): 1.0}, artefatos)
    assert list(vinculos) == [(r.chave, f.chave)]  # classes não recebem vínculo transitivo
    assert vinculos[(r.chave, f.chave)][0].pontuacao == pytest.approx(0.9)


def test_e3_respeita_limiar():
    r, t, f = req("RF-01", "Login"), um_teste("test_login"), codigo("login", tipo="funcao")
    artefatos = {a.chave: a for a in (r, t, f)}
    assert estrategia_e3({(r.chave, t.chave): 0.2}, {(t.chave, f.chave): 0.3}, artefatos, limiar=0.1) == {}


# --- E4 ------------------------------------------------------------------
def test_e4_relaciona_requisito_ao_codigo_mais_parecido():
    requisitos = [req("RF-01", "Pagamento", "Processar o pagamento com cartão e recusar cartões inválidos")]
    alvos = [
        codigo("processar_pagamento", modulo="loja.pagamento", tipo="funcao",
               docstring="Processa o pagamento do pedido com cartão."),
        codigo("Carrinho.adicionar", docstring="Adiciona um produto ao carrinho."),
        codigo("Carrinho.__init__"),
    ]
    vinculos = estrategia_e4(requisitos, alvos, limiar=0.1, top_k=5)
    destinos = {d for _, d in vinculos}
    assert alvos[0].chave in destinos
    assert alvos[2].chave not in destinos  # métodos especiais ficam de fora
    evid = vinculos[(requisitos[0].chave, alvos[0].chave)][0]
    assert evid.estrategia == "E4" and "pagamento" in evid.detalhe


def test_e4_glossario_aproxima_portugues_e_ingles():
    requisitos = [req("RF-01", "Carrinho", "Adicionar produto ao carrinho")]
    alvos = [codigo("Cart.add_product", modulo="shop.cart"), codigo("Invoice.render", modulo="shop.invoice")]
    vinculos = estrategia_e4(requisitos, alvos, limiar=0.1)
    assert {d for _, d in vinculos} == {alvos[0].chave}


def test_preprocessamento_divide_identificadores_e_remove_acentos():
    termos = texto.preparar("validarLoginUsuário validar_login_usuario e-mail", glossario={})
    assert termos.count(texto.radical("validar")) == 2
    assert texto.radical("email") in termos
    assert all(t.isascii() for t in termos)


# --- Etapa 4 -------------------------------------------------------------
def test_combinacao_das_evidencias():
    pesos = {"E1": 0.95, "E4": 0.7}
    assert combinar([Evidencia("E1", 1.0, "")], pesos) == pytest.approx(0.95)
    assert combinar([Evidencia("E4", 0.5, "")], pesos) == pytest.approx(0.35)
    # duas evidências independentes aumentam a confiança: 1 - (0.05 * 0.65)
    assert combinar([Evidencia("E1", 1.0, ""), Evidencia("E4", 0.5, "")], pesos) == pytest.approx(0.9675)
    assert combinar([], pesos) == 0


def test_faixas_de_confianca():
    assert faixa(0.95) == "alta" and faixa(0.6) == "media" and faixa(0.2) == "baixa"
