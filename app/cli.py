import click

from .extensions import db
from .models import Conquista


def registrar_comandos(app):
    @app.cli.command("init-db")
    def init_db():
        """Cria as tabelas (use o docs/schema.sql em produção)."""
        db.create_all()
        click.echo("Tabelas criadas.")

    @app.cli.command("seed")
    def seed():
        """Cadastra o catálogo inicial de conquistas (não duplica)."""
        novas = Conquista.cadastrar_iniciais()
        click.echo(f"{novas} conquista(s) cadastrada(s).")
