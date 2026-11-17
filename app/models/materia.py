from ..extensions import db


class Materia(db.Model):
    __tablename__ = "materias"
    __table_args__ = (db.UniqueConstraint("usuario_id", "nome", name="uq_materia_usuario"),)

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nome = db.Column(db.String(80), nullable=False)

    usuario = db.relationship("Usuario", back_populates="materias")
