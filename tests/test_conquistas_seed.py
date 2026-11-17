from app.extensions import db
from app.models import Conquista


def test_seed_cadastra_as_dez_conquistas(app):
    assert Conquista.cadastrar_iniciais() == 10
    assert db.session.scalar(db.select(db.func.count()).select_from(Conquista)) == 10


def test_seed_e_idempotente(app):
    Conquista.cadastrar_iniciais()
    assert Conquista.cadastrar_iniciais() == 0
    assert db.session.scalar(db.select(db.func.count()).select_from(Conquista)) == 10
