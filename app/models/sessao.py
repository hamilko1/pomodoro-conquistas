from ..extensions import db

TIPOS_SESSAO = ("foco", "pausa_curta", "pausa_longa")


class SessaoPomodoro(db.Model):
    __tablename__ = "sessoes_pomodoro"
    __table_args__ = (
        db.CheckConstraint("duracao_min > 0", name="ck_sessao_duracao"),
        db.CheckConstraint("tipo IN ('foco', 'pausa_curta', 'pausa_longa')", name="ck_sessao_tipo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey("materias.id", ondelete="SET NULL"))
    inicio = db.Column(db.DateTime, nullable=False)
    duracao_min = db.Column(db.SmallInteger, nullable=False)
    tipo = db.Column(db.String(12), nullable=False, default="foco")
    concluida = db.Column(db.Boolean, nullable=False, default=False)

    usuario = db.relationship("Usuario", back_populates="sessoes")
    materia = db.relationship("Materia")
