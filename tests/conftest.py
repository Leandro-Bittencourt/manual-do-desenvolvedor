import io
import sys
import zipfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app import create_app  # noqa: E402
from app.config import ConfigTeste  # noqa: E402
from app.extensions import db  # noqa: E402

EXEMPLO = RAIZ / "exemplos" / "loja_virtual"
GABARITO = RAIZ / "exemplos" / "gabarito_loja_virtual.json"


def zip_de_pasta(pasta: Path, destino: Path, prefixo: str = "loja_virtual") -> Path:
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        for arquivo in sorted(pasta.rglob("*")):
            if arquivo.is_file() and "__pycache__" not in arquivo.parts:
                zf.write(arquivo, f"{prefixo}/{arquivo.relative_to(pasta).as_posix()}")
    return destino


def zip_de_dicionario(destino: Path, arquivos: dict[str, str]) -> Path:
    with zipfile.ZipFile(destino, "w") as zf:
        for nome, conteudo in arquivos.items():
            zf.writestr(nome, conteudo)
    return destino


@pytest.fixture
def zip_exemplo(tmp_path) -> Path:
    return zip_de_pasta(EXEMPLO, tmp_path / "loja_virtual.zip")


@pytest.fixture
def app():
    aplicacao = create_app(ConfigTeste)
    yield aplicacao
    with aplicacao.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def cliente(app):
    return app.test_client()


@pytest.fixture
def cliente_logado(cliente):
    cliente.post("/cadastrar", data={
        "nome": "Ana", "email": "ana@exemplo.com", "senha": "senha-segura", "confirmacao": "senha-segura",
    })
    return cliente


def enviar_zip(cliente, caminho: Path, nome: str = "Loja", url: str = "/projetos/novo"):
    with open(caminho, "rb") as arquivo:
        dados = {"nome": nome, "arquivo": (io.BytesIO(arquivo.read()), caminho.name)}
    return cliente.post(url, data=dados, content_type="multipart/form-data", follow_redirects=False)
