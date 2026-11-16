"""Etapa 1 — Recepção e extração segura do projeto enviado em ZIP.

Medidas de segurança aplicadas:

* rejeição de caminhos absolutos ou com ``..`` (*path traversal*);
* rejeição de links simbólicos;
* limites de quantidade de arquivos, de tamanho por arquivo e de tamanho total;
* detecção de taxa de compressão anormal (proteção contra *zip bomb*);
* arquivos sensíveis (``.env``, chaves, credenciais) nunca são extraídos;
* apenas arquivos de texto relevantes para a análise são extraídos.

O código do projeto é apenas lido: nada é executado.
"""

from __future__ import annotations

import os
import stat
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

DIRETORIOS_IGNORADOS = frozenset(
    {
        ".git", ".hg", ".svn", "__pycache__", "node_modules", "venv", ".venv", "env",
        ".env", "site-packages", ".tox", ".nox", ".mypy_cache", ".pytest_cache",
        ".ruff_cache", ".idea", ".vscode", ".eggs", "dist", "build", "htmlcov",
        "target", "out", ".gradle", ".mvn", "coverage", ".next", "playwright-report", "test-results",
    }
)

EXTENSOES_ANALISADAS = frozenset(
    {".py", ".java", ".js", ".mjs", ".cjs", ".jsx", ".html", ".htm", ".md", ".markdown", ".csv", ".json"}
)

NOMES_SENSIVEIS = frozenset(
    {
        "credentials.json", "secrets.json", "secrets.yaml", "secrets.yml", "secrets.toml",
        ".netrc", ".pypirc", ".npmrc", ".htpasswd", "service-account.json",
    }
)
EXTENSOES_SENSIVEIS = (".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".kdbx")
PREFIXOS_CHAVES_SSH = ("id_rsa", "id_dsa", "id_ecdsa", "id_ed25519")

UM_MEGABYTE = 1024 * 1024


class ErroExtracao(Exception):
    """Erro apresentado ao usuário quando o ZIP não pode ser processado."""


@dataclass
class LimitesExtracao:
    max_arquivos: int = 5000
    max_arquivo_bytes: int = 10 * UM_MEGABYTE
    max_total_bytes: int = 200 * UM_MEGABYTE
    max_razao_compressao: int = 100


@dataclass
class ResultadoExtracao:
    raiz: Path
    arquivos: list[str] = field(default_factory=list)
    ignorados: int = 0
    sensiveis: list[str] = field(default_factory=list)


def eh_sensivel(nome_arquivo: str) -> bool:
    """Indica se o arquivo pode conter segredos e deve ser descartado."""
    nome = nome_arquivo.lower()
    if nome == ".env" or nome.startswith(".env."):
        return True
    if nome in NOMES_SENSIVEIS or nome.endswith(EXTENSOES_SENSIVEIS):
        return True
    if nome.startswith(PREFIXOS_CHAVES_SSH):
        return True
    if nome.startswith("credentials"):
        return True
    return "secret" in nome and nome.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".txt"))


def _caminho_seguro(nome: str) -> PurePosixPath | None:
    """Normaliza o nome interno do ZIP e devolve ``None`` se ele for inseguro."""
    nome = nome.replace("\\", "/")
    if not nome or nome.startswith("/") or (len(nome) > 1 and nome[1] == ":"):
        return None
    caminho = PurePosixPath(nome)
    if any(parte == ".." for parte in caminho.parts):
        return None
    return caminho


def _eh_link_simbolico(info: zipfile.ZipInfo) -> bool:
    modo = (info.external_attr >> 16) & 0o170000
    return modo == stat.S_IFLNK


def extrair_zip(caminho_zip: str | os.PathLike, destino: str | os.PathLike,
                limites: LimitesExtracao | None = None) -> ResultadoExtracao:
    limites = limites or LimitesExtracao()
    destino = Path(destino).resolve()
    destino.mkdir(parents=True, exist_ok=True)

    if not zipfile.is_zipfile(caminho_zip):
        raise ErroExtracao("O arquivo enviado não é um ZIP válido.")

    resultado = ResultadoExtracao(raiz=destino)
    total = 0

    with zipfile.ZipFile(caminho_zip) as zf:
        infos = zf.infolist()
        if len(infos) > limites.max_arquivos:
            raise ErroExtracao(
                f"O ZIP contém {len(infos)} entradas; o limite é {limites.max_arquivos}."
            )

        for info in infos:
            if info.is_dir():
                continue
            if _eh_link_simbolico(info):
                resultado.ignorados += 1
                continue

            relativo = _caminho_seguro(info.filename)
            if relativo is None:
                raise ErroExtracao(
                    f"O ZIP contém um caminho inválido ou inseguro: {info.filename}"
                )

            if any(parte in DIRETORIOS_IGNORADOS for parte in relativo.parts[:-1]):
                resultado.ignorados += 1
                continue
            if eh_sensivel(relativo.name):
                resultado.sensiveis.append(relativo.as_posix())
                continue
            if relativo.suffix.lower() not in EXTENSOES_ANALISADAS:
                resultado.ignorados += 1
                continue
            if info.file_size > limites.max_arquivo_bytes:
                resultado.ignorados += 1
                continue
            if (
                info.compress_size
                and info.file_size > UM_MEGABYTE
                and info.file_size / info.compress_size > limites.max_razao_compressao
            ):
                raise ErroExtracao(
                    "O ZIP tem taxa de compressão anormal e foi recusado por segurança."
                )

            total += info.file_size
            if total > limites.max_total_bytes:
                raise ErroExtracao("O conteúdo descompactado excede o limite permitido.")

            alvo = (destino / relativo.as_posix()).resolve()
            if os.path.commonpath([str(destino), str(alvo)]) != str(destino):
                raise ErroExtracao(f"Caminho fora do diretório de destino: {info.filename}")

            alvo.parent.mkdir(parents=True, exist_ok=True)
            lidos = 0
            with zf.open(info) as origem, open(alvo, "wb") as saida:
                while bloco := origem.read(64 * 1024):
                    lidos += len(bloco)
                    if lidos > limites.max_arquivo_bytes:
                        raise ErroExtracao(f"O arquivo {info.filename} excede o limite de tamanho.")
                    saida.write(bloco)
            resultado.arquivos.append(relativo.as_posix())

    _remover_pasta_raiz_unica(resultado)
    return resultado


def _remover_pasta_raiz_unica(resultado: ResultadoExtracao) -> None:
    """Se todo o projeto estiver dentro de uma única pasta, ela vira a raiz.

    Assim ``loja-main/src/app.py`` passa a ser exibido como ``src/app.py``.
    """
    if not resultado.arquivos:
        return
    primeiras = {PurePosixPath(a).parts[0] for a in resultado.arquivos}
    if len(primeiras) != 1:
        return
    pasta = primeiras.pop()
    if any(len(PurePosixPath(a).parts) == 1 for a in resultado.arquivos):
        return
    resultado.raiz = resultado.raiz / pasta
    resultado.arquivos = [PurePosixPath(*PurePosixPath(a).parts[1:]).as_posix() for a in resultado.arquivos]
