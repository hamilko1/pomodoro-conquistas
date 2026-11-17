from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ..models import Conquista

bp = Blueprint("conquistas", __name__, url_prefix="/conquistas")


@bp.get("/")
@login_required
def listar():
    # Concede o que já tiver sido atingido (ex.: sessões feitas antes do catálogo existir)
    Conquista.avaliar(current_user)
    itens = Conquista.vitrine(current_user)
    return render_template(
        "conquistas.html",
        itens=itens,
        obtidas=sum(1 for i in itens if i["data"]),
    )
