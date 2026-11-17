from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ..models import SessaoPomodoro

bp = Blueprint("estatisticas", __name__, url_prefix="/estatisticas")


@bp.get("/")
@login_required
def painel():
    return render_template("estatisticas.html", est=SessaoPomodoro.estatisticas(current_user))
