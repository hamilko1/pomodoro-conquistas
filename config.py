import os

from dotenv import load_dotenv

load_dotenv()


def _normalizar_url(url):
    # Força o driver psycopg2 (instalado no requirements.txt).
    # Também corrige "postgres://", que alguns provedores de hospedagem entregam.
    if url:
        for prefixo in ("postgres://", "postgresql://"):
            if url.startswith(prefixo):
                return "postgresql+psycopg2://" + url[len(prefixo):]
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "chave-de-desenvolvimento-troque-em-producao")
    SQLALCHEMY_DATABASE_URI = _normalizar_url(
        os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pomodoro")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "chave-de-teste"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
