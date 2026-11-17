from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from ..extensions import db
from .base import agora, para_local
from .meta import Meta
from .sessao import SessaoPomodoro

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

    # ---------- avaliação das regras ----------
    @classmethod
    def calcular_metricas(cls, usuario):
        """Números do usuário usados pelas regras (calculados a partir das sessões)."""
        linhas = db.session.execute(
            db.select(SessaoPomodoro.inicio, SessaoPomodoro.duracao_min).where(
                SessaoPomodoro.usuario_id == usuario.id,
                SessaoPomodoro.tipo == "foco",
                SessaoPomodoro.concluida.is_(True),
            )
        ).all()

        por_dia = {}
        horas_fim = []
        for inicio, duracao in linhas:
            dia = para_local(inicio).date()
            por_dia[dia] = por_dia.get(dia, 0) + 1
            horas_fim.append(para_local(inicio + timedelta(minutes=duracao)).hour)

        melhor_sequencia = atual = 0
        anterior = None
        for dia in sorted(por_dia):
            atual = atual + 1 if anterior is not None and dia - anterior == timedelta(days=1) else 1
            melhor_sequencia = max(melhor_sequencia, atual)
            anterior = dia

        return {
            "total_sessoes": len(linhas),
            "sequencia_dias": melhor_sequencia,
            "sessoes_no_dia": max(por_dia.values(), default=0),
            "metas_concluidas": db.session.scalar(
                db.select(db.func.count()).select_from(Meta).where(
                    Meta.usuario_id == usuario.id, Meta.concluida.is_(True)
                )
            ),
            # Maior e menor hora (0-23) em que um foco terminou
            "hora_max": max(horas_fim, default=-1),
            "hora_min": min(horas_fim, default=99),
        }

    def atingida(self, metricas):
        if self.criterio_tipo == "hora_apos":
            return metricas["hora_max"] >= self.criterio_valor
        if self.criterio_tipo == "hora_antes":
            return metricas["hora_min"] < self.criterio_valor
        return metricas[self.criterio_tipo] >= self.criterio_valor

    def progresso(self, metricas):
        """(atual, alvo) para regras de contagem; None nas regras de horário."""
        if self.criterio_tipo in ("hora_apos", "hora_antes"):
            return None
        return min(metricas[self.criterio_tipo], self.criterio_valor), self.criterio_valor

    @classmethod
    def avaliar(cls, usuario):
        """Concede as conquistas cujo critério foi atingido. Retorna as novas."""
        ja_tem = set(
            db.session.scalars(
                db.select(UsuarioConquista.conquista_id).where(UsuarioConquista.usuario_id == usuario.id)
            )
        )
        pendentes = [c for c in db.session.scalars(db.select(cls).order_by(cls.id)) if c.id not in ja_tem]
        if not pendentes:
            return []

        metricas = cls.calcular_metricas(usuario)
        novas = [c for c in pendentes if c.atingida(metricas)]
        if not novas:
            return []

        momento = agora()
        for conquista in novas:
            db.session.add(
                UsuarioConquista(usuario_id=usuario.id, conquista_id=conquista.id, data_obtencao=momento)
            )
        try:
            db.session.commit()
        except IntegrityError:  # duas requisições concederam ao mesmo tempo
            db.session.rollback()
            return []
        return novas

    @classmethod
    def vitrine(cls, usuario):
        """Todas as conquistas do catálogo com o estado do usuário (para a tela)."""
        obtidas = {
            uc.conquista_id: uc.data_obtencao
            for uc in db.session.scalars(
                db.select(UsuarioConquista).where(UsuarioConquista.usuario_id == usuario.id)
            )
        }
        metricas = cls.calcular_metricas(usuario)
        itens = []
        for c in db.session.scalars(db.select(cls).order_by(cls.id)):
            itens.append({
                "conquista": c,
                "data": para_local(obtidas[c.id]) if c.id in obtidas else None,
                "progresso": None if c.id in obtidas else c.progresso(metricas),
            })
        # Conquistadas primeiro (mais recentes antes), depois as que faltam
        itens.sort(key=lambda i: (i["data"] is None, -(i["data"].timestamp() if i["data"] else 0), i["conquista"].id))
        return itens


class UsuarioConquista(db.Model):
    __tablename__ = "usuarios_conquistas"

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    conquista_id = db.Column(db.Integer, db.ForeignKey("conquistas.id", ondelete="CASCADE"), primary_key=True)
    data_obtencao = db.Column(db.DateTime, nullable=False, default=agora)

    usuario = db.relationship("Usuario", back_populates="conquistas")
    conquista = db.relationship("Conquista")
