"""Etapa 2 — Leitura dos requisitos.

Os requisitos são lidos de arquivos estruturados (Markdown, CSV ou JSON)
cujo nome contenha "requisito" ou "requirement" (ex.: ``requisitos.md``).
Os identificadores (``RF-01``, ``RNF-02``, ``REQ-001``...) são reconhecidos
por expressões regulares.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# Prefixos aceitos por padrão. "RNF" vem antes de "RF" para ter prioridade.
PADRAO_ID_PADRAO = r"(?<![A-Za-z0-9])(RNF|RF|REQ|RN|UC|US|HU)[-_ ]?(\d{1,4})(?![0-9])"

EXTENSOES_REQUISITOS = (".md", ".markdown", ".csv", ".json")

CAMPOS_ID = {"id", "identificador", "codigo", "requisito", "ref", "referencia"}
CAMPOS_TITULO = {"titulo", "title", "nome", "name", "resumo"}
CAMPOS_DESCRICAO = {"descricao", "description", "texto", "detalhe", "detalhes", "text"}
CHAVES_LISTA_JSON = ("requisitos", "requirements", "itens", "items")

_SEPARADORES_INICIAIS = " \t:-–—|.)*_"
_DIVISOR_TITULO = re.compile(r"\s[—–-]\s|:\s")


@dataclass
class IdEncontrado:
    canonico: str
    exibicao: str
    inicio: int
    fim: int


@dataclass
class RequisitoLido:
    identificador: str
    canonico: str
    titulo: str
    descricao: str
    arquivo: str
    linha: int

    @property
    def chave(self) -> str:
        return chave_requisito(self.canonico)

    @property
    def hash(self) -> str:
        conteudo = f"{self.titulo}\n{self.descricao}".strip()
        return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def compilar_padrao(padrao: str | None = None) -> re.Pattern:
    return re.compile(padrao or PADRAO_ID_PADRAO, re.IGNORECASE)


def chave_requisito(canonico: str) -> str:
    return f"REQ:{canonico}"


def encontrar_ids(texto: str, padrao: re.Pattern) -> list[IdEncontrado]:
    """Encontra identificadores de requisitos em um texto qualquer.

    ``RF01``, ``rf_01`` e ``RF-1`` são considerados o mesmo requisito
    (forma canônica ``RF-1``); a forma de exibição preserva os zeros.
    """
    encontrados = []
    for m in padrao.finditer(texto or ""):
        prefixo, numero = m.group(1).upper(), m.group(2)
        encontrados.append(
            IdEncontrado(
                canonico=f"{prefixo}-{int(numero)}",
                exibicao=f"{prefixo}-{numero}",
                inicio=m.start(),
                fim=m.end(),
            )
        )
    return encontrados


def eh_arquivo_de_requisitos(caminho: str) -> bool:
    p = PurePosixPath(caminho)
    if p.suffix.lower() not in EXTENSOES_REQUISITOS:
        return False
    nome = _normalizar_campo(p.stem)
    return "requisito" in nome or "requirement" in nome


def _normalizar_campo(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto)
    sem_acentos = "".join(c for c in sem_acentos if not unicodedata.combining(c))
    return sem_acentos.strip().lower()


def _dividir_titulo(texto: str) -> tuple[str, str]:
    texto = texto.strip().lstrip(_SEPARADORES_INICIAIS).strip()
    partes = _DIVISOR_TITULO.split(texto, maxsplit=1)
    if len(partes) == 2 and partes[0].strip():
        return partes[0].strip(), partes[1].strip()
    return texto, ""


def ler_markdown(texto: str, arquivo: str, padrao: re.Pattern) -> list[RequisitoLido]:
    requisitos: list[RequisitoLido] = []
    atual: RequisitoLido | None = None

    for numero_linha, linha in enumerate(texto.splitlines(), start=1):
        bruta = linha.strip()
        if not bruta:
            continue

        # Tabelas Markdown: | RF-01 | Título | Descrição |
        if bruta.startswith("|") and bruta.count("|") >= 3:
            atual = None
            celulas = [c.strip() for c in bruta.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in celulas):
                continue
            ids = encontrar_ids(celulas[0], padrao)
            if ids and ids[0].inicio <= 2:
                titulo = celulas[1] if len(celulas) > 1 else ""
                descricao = " ".join(c for c in celulas[2:] if c)
                requisitos.append(
                    RequisitoLido(ids[0].exibicao, ids[0].canonico, titulo, descricao, arquivo, numero_linha)
                )
            continue

        conteudo = bruta.lstrip("#>*-+ ").replace("**", "").replace("__", "").strip()
        ids = encontrar_ids(conteudo, padrao)
        if ids and ids[0].inicio == 0:
            titulo, descricao = _dividir_titulo(conteudo[ids[0].fim:])
            atual = RequisitoLido(ids[0].exibicao, ids[0].canonico, titulo, descricao, arquivo, numero_linha)
            requisitos.append(atual)
        elif bruta.startswith("#"):
            atual = None
        elif atual is not None:
            atual.descricao = f"{atual.descricao} {conteudo}".strip()

    return requisitos


def _valor(linha: dict, campos: set[str]) -> str:
    for chave, valor in linha.items():
        if chave is not None and _normalizar_campo(str(chave)) in campos and valor is not None:
            return str(valor).strip()
    return ""


def _de_registros(registros, arquivo: str, padrao: re.Pattern, linha_inicial: int) -> list[RequisitoLido]:
    requisitos = []
    for deslocamento, registro in enumerate(registros):
        if not isinstance(registro, dict):
            continue
        ids = encontrar_ids(_valor(registro, CAMPOS_ID), padrao)
        if not ids:
            continue
        requisitos.append(
            RequisitoLido(
                ids[0].exibicao,
                ids[0].canonico,
                _valor(registro, CAMPOS_TITULO),
                _valor(registro, CAMPOS_DESCRICAO),
                arquivo,
                linha_inicial + deslocamento,
            )
        )
    return requisitos


def ler_csv(texto: str, arquivo: str, padrao: re.Pattern) -> list[RequisitoLido]:
    try:
        dialeto = csv.Sniffer().sniff(texto[:2048], delimiters=";,\t")
    except csv.Error:
        dialeto = csv.excel
    leitor = csv.DictReader(io.StringIO(texto), dialect=dialeto)
    return _de_registros(list(leitor), arquivo, padrao, linha_inicial=2)


def ler_json(texto: str, arquivo: str, padrao: re.Pattern) -> list[RequisitoLido]:
    dados = json.loads(texto)
    if isinstance(dados, dict):
        for chave in CHAVES_LISTA_JSON:
            if isinstance(dados.get(chave), list):
                dados = dados[chave]
                break
    if not isinstance(dados, list):
        return []
    return _de_registros(dados, arquivo, padrao, linha_inicial=1)


def ler_requisitos(raiz: Path, arquivos: list[str], padrao: re.Pattern) -> tuple[list[RequisitoLido], list[str]]:
    """Lê todos os arquivos de requisitos do projeto."""
    requisitos: dict[str, RequisitoLido] = {}
    avisos: list[str] = []

    candidatos = sorted(a for a in arquivos if eh_arquivo_de_requisitos(a))
    if not candidatos:
        avisos.append(
            "Nenhum arquivo de requisitos foi encontrado (ex.: requisitos.md, requisitos.csv "
            "ou requisitos.json). Apenas os vínculos entre testes e código serão gerados."
        )

    for relativo in candidatos:
        texto = (Path(raiz) / relativo).read_text(encoding="utf-8-sig", errors="replace")
        extensao = PurePosixPath(relativo).suffix.lower()
        try:
            if extensao == ".csv":
                lidos = ler_csv(texto, relativo, padrao)
            elif extensao == ".json":
                lidos = ler_json(texto, relativo, padrao)
            else:
                lidos = ler_markdown(texto, relativo, padrao)
        except (ValueError, csv.Error) as erro:
            avisos.append(f"Não foi possível ler {relativo}: {erro}")
            continue

        for requisito in lidos:
            if requisito.canonico in requisitos:
                avisos.append(
                    f"O requisito {requisito.identificador} aparece mais de uma vez "
                    f"({requisito.arquivo}, linha {requisito.linha}); a primeira ocorrência foi mantida."
                )
                continue
            requisitos[requisito.canonico] = requisito

    return list(requisitos.values()), avisos
