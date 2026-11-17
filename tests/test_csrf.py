import pytest

from app import create_app
from app.extensions import db
from config import TestConfig


class ConfigComCsrf(TestConfig):
    WTF_CSRF_ENABLED = True


@pytest.fixture
def client_csrf():
    app = create_app(ConfigComCsrf)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_post_sem_token_csrf_e_recusado(client_csrf):
    resp = client_csrf.post("/login", data={"email": "a@b.com", "senha": "x"})
    assert resp.status_code == 400


def test_api_sem_token_csrf_e_recusada(client_csrf):
    resp = client_csrf.post("/api/sessoes/iniciar", json={"tipo": "foco", "duracao_min": 25})
    assert resp.status_code == 400
