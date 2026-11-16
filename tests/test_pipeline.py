from app.analysis.avaliacao import avaliar, carregar_gabarito, main
from app.analysis.pipeline import analisar_zip
from conftest import GABARITO, zip_de_dicionario


def _chaves(resultado):
    nomes = {a.chave: a.identificador for a in resultado.artefatos}
    return {(nomes[o], nomes[d]) for o, d in resultado.vinculos}


def test_analisa_o_projeto_de_exemplo(zip_exemplo):
    resultado = analisar_zip(zip_exemplo)
    m = resultado.metricas
    assert (m["requisitos"], m["testes"], m["elementos_codigo"]) == (6, 9, 15)
    vinculos = _chaves(resultado)
    # E1: marcações explícitas
    assert ("RF-01", "CadastroUsuarios.cadastrar") in vinculos
    assert ("RF-02", "test_autentica_usuario") in vinculos
    # E2: chamadas dos testes
    assert ("test_total_com_cupom", "Carrinho.calcular_total") in vinculos
    # E3/E4: pagamento não tem marcação, mas é encontrado
    assert ("RF-05", "processar_pagamento") in vinculos
    assert ("RF-05", "test_cartao_invalido_recusado") in vinculos
    assert m["tempo_ms"] > 0 and m["arquivos_sensiveis_ignorados"] == 0


def test_qualidade_minima_contra_o_gabarito(zip_exemplo):
    resultado = analisar_zip(zip_exemplo)
    esperados, problemas = carregar_gabarito(GABARITO, resultado)
    assert problemas == []
    metricas = avaliar(resultado, esperados)
    assert metricas["E2"].precisao == 1.0
    assert metricas["Combinação"].revocacao >= 0.9
    assert metricas["Combinação"].precisao >= 0.7


def test_confianca_maior_quando_estrategias_concordam(zip_exemplo):
    resultado = analisar_zip(zip_exemplo)
    nomes = {a.identificador: a.chave for a in resultado.artefatos}
    explicito = resultado.confiancas[(nomes["RF-01"], nomes["CadastroUsuarios.cadastrar"])]
    so_texto = [c for (o, d), c in resultado.confiancas.items()
                if all(e.estrategia == "E4" for e in resultado.vinculos[(o, d)])]
    assert explicito > max(so_texto)


def test_projeto_sem_requisitos_ainda_vincula_testes_ao_codigo(tmp_path):
    origem = zip_de_dicionario(tmp_path / "p.zip", {
        "app/calc.py": "def somar(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from app.calc import somar\n\ndef test_somar():\n    assert somar(1, 2) == 3\n",
        ".env": "SEGREDO=1",
    })
    resultado = analisar_zip(origem)
    assert _chaves(resultado) == {("test_somar", "somar")}
    assert any("Nenhum arquivo de requisitos" in a for a in resultado.avisos)
    assert any("sensível" in a for a in resultado.avisos)


def test_linha_de_comando_da_avaliacao(zip_exemplo, capsys):
    assert main([str(zip_exemplo), str(GABARITO)]) == 0
    saida = capsys.readouterr().out
    assert "Combinação" in saida and "Precisão" in saida
