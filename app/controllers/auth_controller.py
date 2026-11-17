from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..models import ErroValidacao, Usuario

bp = Blueprint("auth", __name__)


def _destino_seguro(alvo):
    """Aceita apenas caminhos internos (evita redirecionar para sites externos)."""
    if alvo and alvo.startswith("/") and not alvo.startswith("//"):
        return alvo
    return None


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for("main.painel"))

    if request.method == "POST":
        senha = request.form.get("senha", "")
        if senha != request.form.get("confirmacao", ""):
            flash("As senhas não coincidem.", "erro")
        else:
            try:
                usuario = Usuario.cadastrar(
                    request.form.get("nome"), request.form.get("email"), senha
                )
            except ErroValidacao as erro:
                flash(str(erro), "erro")
            else:
                login_user(usuario)
                flash("Conta criada. Bons estudos!", "sucesso")
                return redirect(url_for("main.painel"))

    return render_template("auth/cadastro.html", form=request.form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.painel"))

    if request.method == "POST":
        usuario = Usuario.autenticar(request.form.get("email"), request.form.get("senha"))
        if usuario:
            login_user(usuario)
            destino = _destino_seguro(request.args.get("next"))
            return redirect(destino or url_for("main.painel"))
        flash("E-mail ou senha incorretos.", "erro")

    return render_template("auth/login.html", form=request.form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("auth.login"))
