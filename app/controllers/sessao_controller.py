from functools import wraps

from flask import Blueprint, jsonify, request
from flask_login import current_user

from ..extensions import db
from ..models import ErroValidacao, SessaoPomodoro

bp = Blueprint("sessoes", __name__, url_prefix="/api/sessoes")


def api_login_required(view):
    """Como @login_required, mas responde JSON em vez de redirecionar."""
    @wraps(view)
    def envolvido(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify(erro="Sua sessão expirou. Entre novamente."), 401
        return view(*args, **kwargs)
    return envolvido


@bp.post("/iniciar")
@api_login_required
def iniciar():
    dados = request.get_json(silent=True) or {}
    try:
        sessao = SessaoPomodoro.iniciar(
            current_user, dados.get("tipo"), dados.get("duracao_min"), dados.get("materia_id")
        )
    except ErroValidacao as erro:
        return jsonify(erro=str(erro)), 400
    return jsonify(id=sessao.id, tipo=sessao.tipo, duracao_min=sessao.duracao_min), 201


@bp.post("/<int:sessao_id>/concluir")
@api_login_required
def concluir(sessao_id):
    sessao = db.session.get(SessaoPomodoro, sessao_id)
    if sessao is None or sessao.usuario_id != current_user.id:
        return jsonify(erro="Sessão não encontrada."), 404
    try:
        sessao.concluir()
    except ErroValidacao as erro:
        return jsonify(erro=str(erro)), 409
    return jsonify(
        ok=True,
        focos_hoje=SessaoPomodoro.focos_hoje(current_user),
        total_focos=SessaoPomodoro.total_focos(current_user),
    )
