"""Pré-processamento de texto para a estratégia E4 (similaridade textual).

Passos aplicados a requisitos e a elementos de código:

1. separação de identificadores compostos
   (``validarLoginUsuario`` / ``validar_login_usuario`` -> ``validar login usuario``);
2. conversão para minúsculas e remoção de acentos;
3. remoção de palavras vazias (português, inglês e termos comuns de código);
4. expansão por um glossário português -> inglês, para reduzir a diferença
   de vocabulário entre requisitos em português e código em inglês;
5. redução das palavras ao radical (Snowball, da biblioteca NLTK, que
   funciona sem downloads adicionais).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from functools import lru_cache

from nltk.stem.snowball import SnowballStemmer

STOPWORDS_PT = frozenset(
    """
    a ao aos as ate com como da das de dela dele deles do dos e ela elas ele eles em
    entre era essa esse esta este eu foi for ha isso isto ja la mais mas me mesmo meu
    minha na nas nem no nos nossa nosso num numa o os ou para pela pelas pelo pelos por
    qual quando que quem se sem ser seu sua suas seus so sob sobre tambem te tem ter um
    uma umas uns deve devem dever pode podem sera serao sistema caso cada todo toda
    todos todas onde apos antes depois forma devera permitir permite
    """.split()
)

STOPWORDS_EN = frozenset(
    """
    a an and are as at be by for from has have in is it its of on or that the this to
    was were will with not no if else then should must can may
    """.split()
)

STOPWORDS_CODIGO = frozenset(
    """
    self cls def return none true false assert test tests teste testes init main args
    kwargs str int float bool list dict set tuple print len range import class pass
    raise try except finally lambda yield async await py pytest unittest mock fixture
    setup teardown obj tmp aux resultado result res
    """.split()
)

PALAVRAS_VAZIAS = STOPWORDS_PT | STOPWORDS_EN | STOPWORDS_CODIGO

GLOSSARIO_PADRAO: dict[str, list[str]] = {
    "usuario": ["user"], "usuarios": ["users", "user"], "senha": ["password"],
    "senhas": ["passwords", "password"], "cadastro": ["register", "signup"],
    "cadastrar": ["register", "create"], "entrar": ["login", "signin"],
    "autenticar": ["authenticate", "login"], "autenticacao": ["authentication", "auth", "login"],
    "sair": ["logout"], "buscar": ["search", "find"], "pesquisar": ["search"],
    "excluir": ["delete", "remove"], "remover": ["remove", "delete"], "editar": ["edit", "update"],
    "atualizar": ["update"], "criar": ["create"], "salvar": ["save"], "listar": ["list"],
    "adicionar": ["add"], "incluir": ["add", "insert"],
    "calcular": ["calculate", "compute"], "valor": ["value", "amount"], "preco": ["price"],
    "produto": ["product", "item"], "produtos": ["products"], "pedido": ["order"],
    "carrinho": ["cart"], "pagamento": ["payment"], "pagar": ["pay"],
    "cliente": ["customer", "client"], "relatorio": ["report"], "arquivo": ["file"],
    "enviar": ["send", "upload"], "validar": ["validate"], "validacao": ["validation"],
    "desconto": ["discount"], "cupom": ["coupon"], "estoque": ["stock", "inventory"],
    "quantidade": ["quantity"], "nome": ["name"], "cartao": ["card"], "data": ["date"],
    "erro": ["error"], "mensagem": ["message"], "permissao": ["permission"],
    "perfil": ["profile"], "conta": ["account"], "endereco": ["address"],
}

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_PALAVRA = re.compile(r"[A-Za-zÀ-ÿ0-9_]+")


def remover_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def dividir_identificador(identificador: str) -> list[str]:
    partes: list[str] = []
    for bloco in re.split(r"[_\d]+", identificador):
        if bloco:
            partes.extend(p for p in _CAMEL.split(bloco) if p)
    return partes


_E_MAIL = re.compile(r"\be-mails?\b", re.IGNORECASE)


def palavras(texto: str) -> Iterable[str]:
    texto = _E_MAIL.sub("email", texto or "")
    for bruto in _PALAVRA.findall(texto):
        for parte in dividir_identificador(bruto):
            yield remover_acentos(parte).lower()


@lru_cache(maxsize=1)
def _radicalizador() -> SnowballStemmer:
    return SnowballStemmer("portuguese")


@lru_cache(maxsize=50_000)
def radical(palavra: str) -> str:
    return _radicalizador().stem(palavra)


def preparar(texto: str, glossario: dict[str, list[str]] | None = None,
             exemplos: dict[str, str] | None = None) -> list[str]:
    """Transforma um texto na lista de termos usada pelo TF-IDF.

    Se ``exemplos`` for informado, registra uma palavra legível para cada
    radical (usado para explicar a evidência ao desenvolvedor).
    """
    glossario = GLOSSARIO_PADRAO if glossario is None else glossario
    termos: list[str] = []
    for palavra in palavras(texto):
        if len(palavra) < 2 or palavra in PALAVRAS_VAZIAS:
            continue
        for forma in (palavra, *glossario.get(palavra, [])):
            r = radical(forma)
            termos.append(r)
            if exemplos is not None:
                exemplos.setdefault(r, forma)
    return termos
