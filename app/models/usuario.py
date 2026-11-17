import re

from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db, login_manager
from .base import ErroValidacao, agora

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SENHA_MIN = 8


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=agora)

    materias = db.relationship("Materia", back_populates="usuario", cascade="all, delete-orphan")
    sessoes = db.relationship("SessaoPomodoro", back_populates="usuario", cascade="all, delete-orphan")
    metas = db.relationship("Meta", back_populates="usuario", cascade="all, delete-orphan")
    conquistas = db.relationship("UsuarioConquista", back_populates="usuario", cascade="all, delete-orphan")

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @classmethod
    def cadastrar(cls, nome, email, senha):
        nome = (nome or "").strip()
        email = (email or "").strip().lower()
        senha = senha or ""

        if not nome:
            raise ErroValidacao("Informe seu nome.")
        if len(nome) > 100:
            raise ErroValidacao("O nome pode ter no máximo 100 caracteres.")
        if len(email) > 150 or not EMAIL_RE.match(email):
            raise ErroValidacao("Informe um e-mail válido.")
        if len(senha) < SENHA_MIN:
            raise ErroValidacao(f"A senha precisa ter pelo menos {SENHA_MIN} caracteres.")
        if cls.buscar_por_email(email):
            raise ErroValidacao("Este e-mail já está cadastrado.")

        usuario = cls(nome=nome, email=email)
        usuario.definir_senha(senha)
        db.session.add(usuario)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ErroValidacao("Este e-mail já está cadastrado.")
        return usuario

    @classmethod
    def buscar_por_email(cls, email):
        email = (email or "").strip().lower()
        return db.session.scalar(db.select(cls).filter_by(email=email))

    @classmethod
    def autenticar(cls, email, senha):
        """Retorna o usuário se e-mail e senha conferem; senão, None."""
        usuario = cls.buscar_por_email(email)
        if usuario and usuario.verificar_senha(senha or ""):
            return usuario
        return None


@login_manager.user_loader
def carregar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))
