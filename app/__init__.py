import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config

from .extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Atrás de um proxy HTTPS (ex.: Render): confia nos cabeçalhos X-Forwarded-* e
    # só envia o cookie de sessão por HTTPS. Ative com TRUST_PROXY=1.
    if os.environ.get("TRUST_PROXY") == "1":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Entre na sua conta para acessar esta página."
    login_manager.login_message_category = "erro"

    from . import models  # noqa: F401  (registra os modelos no SQLAlchemy)
    from .cli import registrar_comandos
    from .controllers.auth_controller import bp as auth_bp
    from .controllers.main_controller import bp as main_bp
    from .controllers.conquista_controller import bp as conquistas_bp
    from .controllers.estatistica_controller import bp as estatisticas_bp
    from .controllers.materia_controller import bp as materias_bp
    from .controllers.meta_controller import bp as metas_bp
    from .controllers.sessao_controller import bp as sessoes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(sessoes_bp)
    app.register_blueprint(materias_bp)
    app.register_blueprint(metas_bp)
    app.register_blueprint(conquistas_bp)
    app.register_blueprint(estatisticas_bp)
    registrar_comandos(app)

    return app
