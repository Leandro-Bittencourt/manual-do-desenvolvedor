"""Filtros e textos usados nos templates."""

from datetime import timezone

from .analysis.confianca import faixa

ROTULOS_TIPO = {
    "requisito": "Requisito",
    "teste": "Teste",
    "funcao": "Função",
    "classe": "Classe",
    "metodo": "Método",
    "interface": "Interface",
}

ROTULOS_LINGUAGEM = {"python": "Python", "java": "Java", "javascript": "JavaScript", "html": "HTML"}

ROTULOS_STATUS = {
    "sugerido": "Sugerido",
    "confirmado": "Confirmado",
    "rejeitado": "Rejeitado",
    "a_revisar": "A revisar",
}

ROTULOS_FAIXA = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}

ROTULOS_ESTRATEGIA = {
    "E1": "E1 · Marcação explícita",
    "E2": "E2 · Análise de chamadas",
    "E3": "E3 · Inferência transitiva",
    "E4": "E4 · Similaridade textual",
    "REV": "Revisão do desenvolvedor",
}


def init_app(app) -> None:
    faixas = app.config["ANALISE_FAIXAS"]

    @app.template_filter("faixa")
    def _faixa(confianca: float) -> str:
        return faixa(confianca, faixas)

    @app.template_filter("percentual")
    def _percentual(valor: float) -> str:
        return f"{valor * 100:.0f}%"

    @app.template_filter("decimal")
    def _decimal(valor: float) -> str:
        return f"{valor:.2f}".replace(".", ",")

    @app.template_filter("data")
    def _data(valor) -> str:
        if not valor:
            return ""
        if valor.tzinfo is None:  # o SQLite devolve datas sem fuso; elas são gravadas em UTC
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone().strftime("%d/%m/%Y %H:%M")

    app.jinja_env.globals.update(
        ROTULOS_TIPO=ROTULOS_TIPO,
        ROTULOS_STATUS=ROTULOS_STATUS,
        ROTULOS_FAIXA=ROTULOS_FAIXA,
        ROTULOS_ESTRATEGIA=ROTULOS_ESTRATEGIA,
        ROTULOS_LINGUAGEM=ROTULOS_LINGUAGEM,
    )
