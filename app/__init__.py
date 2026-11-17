from flask import Flask

from config import Config

from .extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

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

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    registrar_comandos(app)

    return app
