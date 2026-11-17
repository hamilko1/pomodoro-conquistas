from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..models import ErroValidacao, Materia

bp = Blueprint("materias", __name__, url_prefix="/materias")


def _materia_ou_404(materia_id):
    materia = Materia.buscar(current_user, materia_id)
    if materia is None:
        abort(404)
    return materia


@bp.route("/", methods=["GET", "POST"])
@login_required
def listar():
    if request.method == "POST":
        try:
            Materia.criar(current_user, request.form.get("nome"))
        except ErroValidacao as erro:
            flash(str(erro), "erro")
        else:
            flash("Matéria criada.", "sucesso")
            return redirect(url_for("materias.listar"))
    return render_template("materias/lista.html", materias=Materia.listar(current_user), form=request.form)


@bp.route("/<int:materia_id>/editar", methods=["GET", "POST"])
@login_required
def editar(materia_id):
    materia = _materia_ou_404(materia_id)
    if request.method == "POST":
        try:
            materia.renomear(request.form.get("nome"))
        except ErroValidacao as erro:
            flash(str(erro), "erro")
        else:
            flash("Matéria atualizada.", "sucesso")
            return redirect(url_for("materias.listar"))
    return render_template("materias/editar.html", materia=materia, form=request.form)


@bp.post("/<int:materia_id>/excluir")
@login_required
def excluir(materia_id):
    _materia_ou_404(materia_id).excluir()
    flash("Matéria excluída. Seus pomodoros foram mantidos, sem matéria.", "sucesso")
    return redirect(url_for("materias.listar"))
