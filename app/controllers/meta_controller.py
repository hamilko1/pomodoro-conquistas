from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..models import ErroValidacao, Materia, Meta

bp = Blueprint("metas", __name__, url_prefix="/metas")


def _meta_ou_404(meta_id):
    meta = Meta.buscar(current_user, meta_id)
    if meta is None:
        abort(404)
    return meta


def _dados_do_formulario():
    return (
        request.form.get("descricao"),
        request.form.get("quantidade_alvo"),
        request.form.get("prazo"),
        request.form.get("materia_id"),
    )


@bp.route("/", methods=["GET", "POST"])
@login_required
def listar():
    if request.method == "POST":
        try:
            Meta.criar(current_user, *_dados_do_formulario())
        except ErroValidacao as erro:
            flash(str(erro), "erro")
        else:
            flash("Meta criada.", "sucesso")
            return redirect(url_for("metas.listar"))
    # Cobre metas que foram cumpridas sem passar pelo timer (ex.: alvo reduzido)
    Meta.avaliar_concluidas(current_user)
    return render_template(
        "metas/lista.html",
        metas=Meta.listar(current_user),
        materias=Materia.listar(current_user),
        form=request.form,
    )


@bp.route("/<int:meta_id>/editar", methods=["GET", "POST"])
@login_required
def editar(meta_id):
    meta = _meta_ou_404(meta_id)
    if meta.concluida:
        flash("Uma meta cumprida não pode ser editada.", "erro")
        return redirect(url_for("metas.listar"))
    if request.method == "POST":
        try:
            meta.editar(*_dados_do_formulario())
        except ErroValidacao as erro:
            flash(str(erro), "erro")
        else:
            flash("Meta atualizada.", "sucesso")
            return redirect(url_for("metas.listar"))
    return render_template(
        "metas/editar.html", meta=meta, materias=Materia.listar(current_user), form=request.form
    )


@bp.post("/<int:meta_id>/excluir")
@login_required
def excluir(meta_id):
    _meta_ou_404(meta_id).excluir()
    flash("Meta excluída.", "sucesso")
    return redirect(url_for("metas.listar"))
