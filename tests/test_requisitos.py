import json

from app.analysis.requisitos import (
    compilar_padrao,
    eh_arquivo_de_requisitos,
    encontrar_ids,
    ler_csv,
    ler_json,
    ler_markdown,
    ler_requisitos,
)

PADRAO = compilar_padrao()


def test_ids_em_formatos_variados_sao_normalizados():
    ids = encontrar_ids("RF-01, rf02, RF_3, RNF-01, REQ-001 e test_rf04_login", PADRAO)
    assert [i.canonico for i in ids] == ["RF-1", "RF-2", "RF-3", "RNF-1", "REQ-1", "RF-4"]
    assert ids[0].exibicao == "RF-01"


def test_nao_confunde_palavras_com_identificadores():
    assert encontrar_ids("perf01 interface URF-1", PADRAO) == []


def test_markdown_com_titulos_e_descricao():
    texto = """# Requisitos
## RF-01 — Cadastro de usuário
O sistema deve cadastrar usuários.
Deve validar o e-mail.

## RNF-01: Desempenho
Responder em até 2 segundos.

## Glossário
Termo qualquer.
"""
    reqs = ler_markdown(texto, "requisitos.md", PADRAO)
    assert [(r.identificador, r.titulo) for r in reqs] == [("RF-01", "Cadastro de usuário"), ("RNF-01", "Desempenho")]
    assert reqs[0].descricao == "O sistema deve cadastrar usuários. Deve validar o e-mail."
    assert reqs[1].descricao == "Responder em até 2 segundos."


def test_markdown_em_lista_e_tabela():
    texto = """- **RF-01**: Login — O usuário entra com e-mail e senha.
| ID | Título | Descrição |
|----|--------|-----------|
| RF-02 | Logout | Encerra a sessão. |
"""
    reqs = ler_markdown(texto, "req.md", PADRAO)
    assert [(r.identificador, r.titulo, r.descricao) for r in reqs] == [
        ("RF-01", "Login", "O usuário entra com e-mail e senha."),
        ("RF-02", "Logout", "Encerra a sessão."),
    ]


def test_csv_com_ponto_e_virgula_e_cabecalho_acentuado():
    texto = "Identificador;Título;Descrição\nRF-01;Login;Entrar no sistema\nRF-02;Logout;Sair\n"
    reqs = ler_csv(texto, "requisitos.csv", PADRAO)
    assert [(r.identificador, r.titulo, r.descricao) for r in reqs] == [
        ("RF-01", "Login", "Entrar no sistema"), ("RF-02", "Logout", "Sair"),
    ]


def test_json_lista_ou_objeto():
    lista = json.dumps([{"id": "RF-01", "titulo": "Login", "descricao": "Entrar"}])
    objeto = json.dumps({"requisitos": [{"id": "RF-02", "title": "Logout", "description": "Sair"}]})
    assert ler_json(lista, "r.json", PADRAO)[0].titulo == "Login"
    assert ler_json(objeto, "r.json", PADRAO)[0].descricao == "Sair"


def test_identifica_arquivos_de_requisitos():
    assert eh_arquivo_de_requisitos("docs/requisitos.md")
    assert eh_arquivo_de_requisitos("Requirements.csv")
    assert eh_arquivo_de_requisitos("especificacao_de_requisitos.json")
    assert not eh_arquivo_de_requisitos("requirements.txt")  # dependências do pip
    assert not eh_arquivo_de_requisitos("README.md")


def test_ler_requisitos_avisa_duplicados_e_ausencia(tmp_path):
    (tmp_path / "requisitos.md").write_text("## RF-01 A\n## RF-1 B\n", encoding="utf-8")
    reqs, avisos = ler_requisitos(tmp_path, ["requisitos.md"], PADRAO)
    assert len(reqs) == 1 and "mais de uma vez" in avisos[0]

    _, avisos = ler_requisitos(tmp_path, ["app.py"], PADRAO)
    assert "Nenhum arquivo de requisitos" in avisos[0]
