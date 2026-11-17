from sqlalchemy.exc import IntegrityError

from ..extensions import db
from .base import ErroValidacao

NOME_MAX = 80


class Materia(db.Model):
    __tablename__ = "materias"
    __table_args__ = (db.UniqueConstraint("usuario_id", "nome", name="uq_materia_usuario"),)

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nome = db.Column(db.String(80), nullable=False)

    usuario = db.relationship("Usuario", back_populates="materias")

    # ---------- validação ----------
    @classmethod
    def _validar_nome(cls, usuario, nome, ignorar_id=None):
        nome = (nome or "").strip()
        if not nome:
            raise ErroValidacao("Informe o nome da matéria.")
        if len(nome) > NOME_MAX:
            raise ErroValidacao(f"O nome pode ter no máximo {NOME_MAX} caracteres.")
        consulta = db.select(cls.id).where(
            cls.usuario_id == usuario.id, db.func.lower(cls.nome) == nome.lower()
        )
        if ignorar_id is not None:
            consulta = consulta.where(cls.id != ignorar_id)
        if db.session.scalar(consulta) is not None:
            raise ErroValidacao("Você já tem uma matéria com esse nome.")
        return nome

    # ---------- consultas ----------
    @classmethod
    def listar(cls, usuario):
        return list(
            db.session.scalars(
                db.select(cls).where(cls.usuario_id == usuario.id).order_by(db.func.lower(cls.nome))
            )
        )

    @classmethod
    def buscar(cls, usuario, materia_id):
        """Matéria do usuário, ou None (nunca devolve a de outra pessoa)."""
        materia = db.session.get(cls, materia_id)
        if materia is None or materia.usuario_id != usuario.id:
            return None
        return materia

    def focos_concluidos(self):
        from .sessao import SessaoPomodoro

        return db.session.scalar(
            db.select(db.func.count()).select_from(SessaoPomodoro).where(
                SessaoPomodoro.materia_id == self.id,
                SessaoPomodoro.tipo == "foco",
                SessaoPomodoro.concluida.is_(True),
            )
        )

    # ---------- comandos ----------
    @classmethod
    def criar(cls, usuario, nome):
        nome = cls._validar_nome(usuario, nome)
        materia = cls(usuario_id=usuario.id, nome=nome)
        db.session.add(materia)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ErroValidacao("Você já tem uma matéria com esse nome.")
        return materia

    def renomear(self, nome):
        self.nome = self._validar_nome(self.usuario, nome, ignorar_id=self.id)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ErroValidacao("Você já tem uma matéria com esse nome.")

    def excluir(self):
        """Exclui a matéria preservando o histórico.

        - Sessões continuam existindo, apenas ficam "sem matéria".
        - Metas ainda abertas dessa matéria perdem o sentido e são removidas.
        - Metas já concluídas são mantidas (ficam "sem matéria").
        """
        from .meta import Meta
        from .sessao import SessaoPomodoro

        db.session.execute(
            db.delete(Meta).where(Meta.materia_id == self.id, Meta.concluida.is_(False))
        )
        db.session.execute(
            db.update(Meta).where(Meta.materia_id == self.id).values(materia_id=None)
        )
        db.session.execute(
            db.update(SessaoPomodoro)
            .where(SessaoPomodoro.materia_id == self.id)
            .values(materia_id=None)
        )
        db.session.delete(self)
        db.session.commit()
