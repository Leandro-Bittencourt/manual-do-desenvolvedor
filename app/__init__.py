"""Manual do Desenvolvedor — ferramenta web de rastreabilidade entre
requisitos, casos de teste e código-fonte.

Todo o processamento ocorre localmente: nenhum código ou requisito é
enviado a serviços externos.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Flask, render_template

from .config import Config
from .extensions import db, login_manager


def _chave_secreta(app: Flask) -> str:
    arquivo = Path(app.instance_path) / "secret_key"
    if arquivo.exists():
        return arquivo.read_text(encoding="utf-8").strip()
    chave = secrets.token_hex(32)
    arquivo.write_text(chave, encoding="utf-8")
    return chave


def create_app(config_object: type | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object or Config)
    os.makedirs(app.instance_path, exist_ok=True)

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(app.instance_path, "manual.db")
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = _chave_secreta(app)

    db.init_app(app)
    login_manager.init_app(app)

    from . import filtros, seguranca
    from .auth import bp as auth_bp
    from .views import bp as main_bp

    seguranca.init_app(app)
    filtros.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.errorhandler(400)
    def _erro_400(erro):
        return render_template("erro.html", codigo=400, mensagem=erro.description), 400

    @app.errorhandler(404)
    def _erro_404(_erro):
        return render_template("erro.html", codigo=404, mensagem="Página não encontrada."), 404

    @app.errorhandler(413)
    def _erro_413(_erro):
        limite = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return render_template("erro.html", codigo=413,
                               mensagem=f"O arquivo enviado é maior que o limite de {limite} MB."), 413

    with app.app_context():
        db.create_all()

    return app
