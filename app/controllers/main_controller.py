from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..models import SessaoPomodoro

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.painel"))
    return redirect(url_for("auth.login"))


@bp.route("/painel")
@login_required
def painel():
    return render_template(
        "painel.html",
        materias=sorted(current_user.materias, key=lambda m: m.nome.lower()),
        focos_hoje=SessaoPomodoro.focos_hoje(current_user),
        total_focos=SessaoPomodoro.total_focos(current_user),
    )
