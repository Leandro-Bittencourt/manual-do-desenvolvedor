"""Proteções da aplicação web: token CSRF e cabeçalhos de segurança."""

import secrets

from flask import abort, request, session


def token_csrf() -> str:
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def init_app(app) -> None:
    app.jinja_env.globals["csrf_token"] = token_csrf

    @app.before_request
    def _verificar_csrf():
        if request.method != "POST" or not app.config.get("CSRF_ATIVO", True):
            return None
        enviado = request.form.get("csrf_token", "")
        esperado = session.get("_csrf", "")
        if not enviado or not esperado or not secrets.compare_digest(enviado, esperado):
            abort(400, description="Formulário expirado ou inválido. Recarregue a página e tente novamente.")
        return None

    @app.after_request
    def _cabecalhos(resposta):
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "same-origin")
        resposta.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; form-action 'self'",
        )
        return resposta
