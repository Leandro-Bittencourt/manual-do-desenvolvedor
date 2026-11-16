"""Resolve chamadas encontradas no código para os elementos do projeto.

Usado pela estratégia E2 (análise de chamadas dos testes) e para montar o
grafo de dependências entre funções de produção (análise de impacto).
"""

from __future__ import annotations

import builtins
from collections import defaultdict

from .modelos import TIPO_INTERFACE, Artefato, Chamada

# Nomes que nunca devem ser resolvidos apenas pelo nome (funções nativas,
# métodos de coleções e utilitários de teste).
NOMES_IGNORADOS = frozenset(dir(builtins)) | frozenset(
    {
        "append", "extend", "pop", "items", "keys", "values", "get", "update", "copy",
        "join", "split", "strip", "format", "lower", "upper", "replace", "startswith",
        "endswith", "read", "write", "close", "raises", "approx", "fixture", "mark",
        "parametrize", "patch", "assertEqual", "assertNotEqual", "assertTrue",
        "assertFalse", "assertIn", "assertNotIn", "assertIs", "assertIsNone",
        "assertIsNotNone", "assertRaises", "assertAlmostEqual", "assertGreater",
        "assertLess", "assertDictEqual", "assertListEqual",
        # JavaScript: coleções, promessas, JSON, console, DOM e asserções
        "map", "filter", "find", "forEach", "reduce", "some", "every", "includes", "push", "slice",
        "splice", "concat", "indexOf", "then", "catch", "finally", "toString", "parse", "stringify",
        "log", "error", "warn", "equal", "strictEqual", "deepStrictEqual", "deepEqual", "ok", "throws",
        "rejects", "notEqual", "expect", "toBe", "toEqual", "addEventListener", "querySelector",
        "querySelectorAll", "getElementById", "preventDefault", "getItem", "setItem", "removeItem",
        "trim", "toLowerCase", "toUpperCase", "fill", "click", "goto", "locator", "toHaveText",
        # Java: coleções, streams e asserções do JUnit
        "add", "contains", "isEmpty", "size", "stream", "collect", "toList", "of", "equals", "hashCode",
        "length", "assertEquals", "assertNotEquals", "assertThrows", "assertNotNull", "assertNull",
        "assertSame", "orElse", "orElseThrow", "isPresent", "ofNullable", "put", "containsKey",
    }
)


class Resolvedor:
    def __init__(self, artefatos_codigo: list[Artefato]):
        self._completos: list[tuple[str, Artefato]] = []
        self._por_nome: dict[str, list[Artefato]] = defaultdict(list)
        self._por_seletor: dict[str, list[Artefato]] = defaultdict(list)
        for artefato in artefatos_codigo:
            if artefato.tipo == TIPO_INTERFACE:
                # elementos de interface são encontrados pelos seletores (#id)
                for termo in dict.fromkeys(t for t in artefato.termos if t.startswith("#")):
                    self._por_seletor[termo].append(artefato)
                continue
            completo = f"{artefato.modulo}.{artefato.identificador}" if artefato.modulo else artefato.identificador
            self._completos.append((completo, artefato))
            self._por_nome[artefato.nome].append(artefato)

    def _por_caminho(self, alvo: str) -> list[Artefato]:
        return [a for completo, a in self._completos if completo == alvo or completo.endswith("." + alvo)]

    @staticmethod
    def _modulos_importados(importacoes: dict[str, str]) -> set[str]:
        modulos = set()
        for destino in importacoes.values():
            modulos.add(destino)
            if "." in destino:
                modulos.add(destino.rsplit(".", 1)[0])
        return modulos

    def resolver(self, chamada: Chamada, importacoes: dict[str, str]) -> list[tuple[Artefato, float, str]]:
        """Devolve ``(artefato, pontuação, como)`` para cada destino provável."""
        if chamada.alvo.startswith("#"):
            encontrados = self._por_seletor.get(chamada.alvo, [])
            if not encontrados:
                return []
            peso = round(1 / len(encontrados), 3)
            return [(a, peso, f"seletor {chamada.alvo} da interface") for a in encontrados]

        partes = chamada.alvo.replace("()", "").split(".")
        cabeca = partes[0]

        if cabeca in importacoes:
            alvo = ".".join([importacoes[cabeca], *partes[1:]])
            encontrados = self._por_caminho(alvo)
            if len(encontrados) == 1:
                return [(encontrados[0], 1.0, "resolvido pela importação")]
            if encontrados:
                peso = round(1 / len(encontrados), 3)
                return [(a, peso, "importação ambígua") for a in encontrados]

        nome = partes[-1]
        if nome in NOMES_IGNORADOS or (nome.startswith("__") and nome.endswith("__")):
            return []
        candidatos = self._por_nome.get(nome, [])
        if not candidatos:
            return []
        if len(candidatos) == 1:
            return [(candidatos[0], 1.0, "nome único no projeto")]

        modulos = self._modulos_importados(importacoes)
        filtrados = [
            a for a in candidatos
            if any(a.modulo == m or a.modulo.endswith("." + m) for m in modulos)
        ]
        if len(filtrados) == 1:
            return [(filtrados[0], 1.0, "nome + módulo importado")]
        base = filtrados or candidatos
        peso = round(1 / len(base), 3)
        return [(a, peso, "nome ambíguo") for a in base]
