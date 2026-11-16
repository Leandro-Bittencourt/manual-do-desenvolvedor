import zipfile

import pytest

from app.analysis.extrator import ErroExtracao, LimitesExtracao, eh_sensivel, extrair_zip
from conftest import zip_de_dicionario


def test_extrai_apenas_arquivos_relevantes(tmp_path):
    origem = zip_de_dicionario(tmp_path / "p.zip", {
        "projeto/src/app.py": "x = 1\n",
        "projeto/requisitos.md": "# RF-01 Teste\n",
        "projeto/imagem.png": "binario",
        "projeto/.venv/lib/pacote.py": "y = 2\n",
        "projeto/node_modules/x.json": "{}",
    })
    resultado = extrair_zip(origem, tmp_path / "saida")
    assert sorted(resultado.arquivos) == ["requisitos.md", "src/app.py"]  # pasta raiz única removida
    assert resultado.ignorados == 3
    assert (resultado.raiz / "src" / "app.py").exists()


def test_arquivos_sensiveis_nunca_sao_extraidos(tmp_path):
    origem = zip_de_dicionario(tmp_path / "p.zip", {
        "app.py": "x = 1\n",
        ".env": "SENHA=123",
        "config/credentials.json": "{}",
        "chaves/id_rsa": "segredo",
        "certificado.pem": "segredo",
    })
    resultado = extrair_zip(origem, tmp_path / "saida")
    assert resultado.arquivos == ["app.py"]
    assert len(resultado.sensiveis) == 4
    assert not (tmp_path / "saida" / ".env").exists()


@pytest.mark.parametrize("nome", ["../fora.py", "/etc/passwd.py", "C:/Windows/x.py", "a/../../b.py"])
def test_recusa_caminhos_inseguros(tmp_path, nome):
    origem = tmp_path / "p.zip"
    with zipfile.ZipFile(origem, "w") as zf:
        info = zipfile.ZipInfo(nome)
        zf.writestr(info, "x = 1")
    with pytest.raises(ErroExtracao):
        extrair_zip(origem, tmp_path / "saida")
    assert not (tmp_path / "fora.py").exists()


def test_recusa_arquivo_que_nao_e_zip(tmp_path):
    falso = tmp_path / "falso.zip"
    falso.write_text("não sou um zip")
    with pytest.raises(ErroExtracao, match="ZIP válido"):
        extrair_zip(falso, tmp_path / "saida")


def test_recusa_zip_bomb(tmp_path):
    origem = tmp_path / "bomba.zip"
    with zipfile.ZipFile(origem, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("grande.py", "0" * (5 * 1024 * 1024))
    with pytest.raises(ErroExtracao, match="compressão"):
        extrair_zip(origem, tmp_path / "saida")


def test_limite_de_quantidade_de_arquivos(tmp_path):
    origem = zip_de_dicionario(tmp_path / "p.zip", {f"m{i}.py": "x=1" for i in range(5)})
    with pytest.raises(ErroExtracao, match="limite"):
        extrair_zip(origem, tmp_path / "saida", LimitesExtracao(max_arquivos=3))


@pytest.mark.parametrize("nome,esperado", [
    (".env", True), (".env.local", True), ("server.key", True), ("id_ed25519", True),
    ("secrets.yaml", True), ("credentials-prod.json", True),
    ("app.py", False), ("requisitos.md", False), ("environment.py", False),
])
def test_deteccao_de_arquivos_sensiveis(nome, esperado):
    assert eh_sensivel(nome) is esperado
