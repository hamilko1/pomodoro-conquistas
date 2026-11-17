from ..extensions import db
from .base import agora

CRITERIOS = (
    "total_sessoes",
    "sequencia_dias",
    "sessoes_no_dia",
    "metas_concluidas",
    "hora_apos",
    "hora_antes",
)

# (codigo, nome, descricao, icone, criterio_tipo, criterio_valor)
CONQUISTAS_INICIAIS = [
    ("primeiro_foco", "Primeiro Foco", "Conclua seu primeiro pomodoro.", "🥉", "total_sessoes", 1),
    ("dez_focos", "Pegando Ritmo", "Conclua 10 pomodoros.", "🥈", "total_sessoes", 10),
    ("cem_focos", "Mestre do Foco", "Conclua 100 pomodoros.", "🥇", "total_sessoes", 100),
    ("sequencia_3", "Aquecendo", "Estude 3 dias seguidos.", "🔥", "sequencia_dias", 3),
    ("sequencia_7", "Semana Perfeita", "Estude 7 dias seguidos.", "🔥", "sequencia_dias", 7),
    ("sequencia_30", "Hábito Formado", "Estude 30 dias seguidos.", "🏆", "sequencia_dias", 30),
    ("maratonista", "Maratonista", "Conclua 4 pomodoros no mesmo dia.", "📚", "sessoes_no_dia", 4),
    ("meta_cumprida", "Meta Cumprida", "Cumpra sua primeira meta.", "🎯", "metas_concluidas", 1),
    ("coruja", "Coruja", "Conclua um pomodoro depois das 22h.", "🦉", "hora_apos", 22),
    ("madrugador", "Madrugador", "Conclua um pomodoro antes das 7h.", "🌅", "hora_antes", 7),
]


class Conquista(db.Model):
    __tablename__ = "conquistas"
    __table_args__ = (
        db.CheckConstraint("criterio_valor > 0", name="ck_conquista_valor"),
        db.CheckConstraint(
            "criterio_tipo IN ('total_sessoes', 'sequencia_dias', 'sessoes_no_dia', "
            "'metas_concluidas', 'hora_apos', 'hora_antes')",
            name="ck_conquista_tipo",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(40), nullable=False, unique=True)
    nome = db.Column(db.String(60), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    icone = db.Column(db.String(10), nullable=False)
    criterio_tipo = db.Column(db.String(20), nullable=False)
    criterio_valor = db.Column(db.SmallInteger, nullable=False)

    @classmethod
    def cadastrar_iniciais(cls):
        """Insere as conquistas que ainda não existem. Retorna quantas foram criadas."""
        existentes = set(db.session.scalars(db.select(cls.codigo)))
        novas = 0
        for codigo, nome, descricao, icone, tipo, valor in CONQUISTAS_INICIAIS:
            if codigo in existentes:
                continue
            db.session.add(
                cls(codigo=codigo, nome=nome, descricao=descricao, icone=icone,
                    criterio_tipo=tipo, criterio_valor=valor)
            )
            novas += 1
        db.session.commit()
        return novas


class UsuarioConquista(db.Model):
    __tablename__ = "usuarios_conquistas"

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    conquista_id = db.Column(db.Integer, db.ForeignKey("conquistas.id", ondelete="CASCADE"), primary_key=True)
    data_obtencao = db.Column(db.DateTime, nullable=False, default=agora)

    usuario = db.relationship("Usuario", back_populates="conquistas")
    conquista = db.relationship("Conquista")
