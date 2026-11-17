from ..extensions import db


class Meta(db.Model):
    __tablename__ = "metas"
    __table_args__ = (db.CheckConstraint("quantidade_alvo > 0", name="ck_meta_alvo"),)

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey("materias.id", ondelete="SET NULL"))
    descricao = db.Column(db.String(150), nullable=False)
    quantidade_alvo = db.Column(db.SmallInteger, nullable=False)
    prazo = db.Column(db.Date)
    concluida = db.Column(db.Boolean, nullable=False, default=False)
    data_conclusao = db.Column(db.DateTime)

    usuario = db.relationship("Usuario", back_populates="metas")
    materia = db.relationship("Materia")
