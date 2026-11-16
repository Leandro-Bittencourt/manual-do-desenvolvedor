"""Cadastro, entrada e saída de usuários."""

import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .extensions import db, login_manager
from .models import Usuario

bp = Blueprint("auth", __name__)

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SENHA_MINIMA = 8


@login_manager.user_loader
def _carregar_usuario(usuario_id: str):
    return db.session.get(Usuario, int(usuario_id))


@bp.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if current_user.is_authenticated:
        return redirect(url_for("main.painel"))

    erros: list[str] = []
    dados = {"nome": "", "email": ""}
    if request.method == "POST":
        dados["nome"] = request.form.get("nome", "").strip()
        dados["email"] = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmacao = request.form.get("confirmacao", "")

        if not dados["nome"]:
            erros.append("Informe seu nome.")
        if not RE_EMAIL.match(dados["email"]):
            erros.append("Informe um e-mail válido.")
        if len(senha) < SENHA_MINIMA:
            erros.append(f"A senha deve ter pelo menos {SENHA_MINIMA} caracteres.")
        if senha != confirmacao:
            erros.append("A confirmação da senha não confere.")
        if not erros and Usuario.query.filter_by(email=dados["email"]).first():
            erros.append("Já existe uma conta com este e-mail.")

        if not erros:
            usuario = Usuario(nome=dados["nome"], email=dados["email"])
            usuario.definir_senha(senha)
            db.session.add(usuario)
            db.session.commit()
            login_user(usuario)
            flash("Conta criada. Envie seu primeiro projeto para começar.", "sucesso")
            return redirect(url_for("main.painel"))

    return render_template("auth/cadastrar.html", erros=erros, dados=dados)


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    if current_user.is_authenticated:
        return redirect(url_for("main.painel"))

    erro = None
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.verificar_senha(senha):
            login_user(usuario, remember=bool(request.form.get("lembrar")))
            destino = request.args.get("next", "")
            if not destino.startswith("/") or destino.startswith("//"):
                destino = url_for("main.painel")
            return redirect(destino)
        erro = "E-mail ou senha incorretos."

    return render_template("auth/entrar.html", erro=erro, email=email)


@bp.route("/sair", methods=["POST"])
@login_required
def sair():
    logout_user()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("auth.entrar"))
