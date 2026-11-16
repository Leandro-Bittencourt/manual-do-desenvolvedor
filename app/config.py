"""Configurações da aplicação.

Os pesos e limiares da análise ficam aqui para facilitar a calibração na
primeira etapa de avaliação (projetos controlados).
"""

import os


class Config:
    SECRET_KEY = os.environ.get("MANUAL_SECRET_KEY")  # se vazio, é gerada em instance/secret_key
    SQLALCHEMY_DATABASE_URI = os.environ.get("MANUAL_DATABASE_URL")  # se vazio, usa instance/manual.db
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # tamanho máximo do ZIP enviado: 50 MB
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_ATIVO = True

    # --- Análise (Capítulo 3) -------------------------------------------
    ANALISE_PADRAO_IDS = None  # None = RF, RNF, REQ, RN, UC, US, HU
    ANALISE_PESOS = {"E1": 0.95, "E2": 0.85, "E3": 0.60, "E4": 0.70, "REV": 1.0}
    ANALISE_FAIXAS = {"alta": 0.80, "media": 0.50}
    ANALISE_LIMIAR_E4 = 0.30  # calibrado no projeto de exemplo; recalibrar na 1ª etapa
    ANALISE_TOP_K_E4 = 5
    ANALISE_LIMIAR_E3 = 0.10


class ConfigTeste(Config):
    TESTING = True
    SECRET_KEY = "chave-de-teste"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    CSRF_ATIVO = False
