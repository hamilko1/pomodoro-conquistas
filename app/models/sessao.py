from datetime import timedelta

from ..extensions import db
from .base import ErroValidacao, agora, hoje_local, inicio_do_dia_local, para_local
from .materia import Materia

def formatar_minutos(minutos):
    """90 -> '1h30min'; 25 -> '25min'."""
    horas, resto = divmod(int(minutos), 60)
    if horas == 0:
        return f"{resto}min"
    return f"{horas}h{resto:02d}min" if resto else f"{horas}h"


TIPOS_SESSAO = ("foco", "pausa_curta", "pausa_longa")
DURACAO_MIN = 1
DURACAO_MAX = 180
# Folga para latência de rede e arredondamento do relógio do navegador
TOLERANCIA_SEGUNDOS = 5


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

    @classmethod
    def iniciar(cls, usuario, tipo, duracao_min, materia_id=None):
        """Registra o começo de um ciclo (ainda não concluído)."""
        if tipo not in TIPOS_SESSAO:
            raise ErroValidacao("Tipo de ciclo inválido.")
        if (
            not isinstance(duracao_min, int)
            or isinstance(duracao_min, bool)
            or not DURACAO_MIN <= duracao_min <= DURACAO_MAX
        ):
            raise ErroValidacao(
                f"A duração deve ser um número inteiro de {DURACAO_MIN} a {DURACAO_MAX} minutos."
            )
        if materia_id is not None:
            materia = db.session.get(Materia, materia_id) if isinstance(materia_id, int) else None
            if materia is None or materia.usuario_id != usuario.id:
                raise ErroValidacao("Matéria não encontrada.")

        sessao = cls(
            usuario_id=usuario.id,
            materia_id=materia_id,
            inicio=agora(),
            duracao_min=duracao_min,
            tipo=tipo,
        )
        db.session.add(sessao)
        db.session.commit()
        return sessao

    def concluir(self):
        """Marca como concluída, conferindo no servidor se o tempo realmente passou."""
        if self.concluida:
            raise ErroValidacao("Esta sessão já foi concluída.")
        decorrido = (agora() - self.inicio).total_seconds()
        if decorrido < self.duracao_min * 60 - TOLERANCIA_SEGUNDOS:
            raise ErroValidacao("O tempo desta sessão ainda não terminou.")
        self.concluida = True
        db.session.commit()

    @classmethod
    def _focos_concluidos(cls, usuario):
        return db.select(db.func.count()).select_from(cls).where(
            cls.usuario_id == usuario.id, cls.tipo == "foco", cls.concluida.is_(True)
        )

    @classmethod
    def total_focos(cls, usuario):
        return db.session.scalar(cls._focos_concluidos(usuario))

    @classmethod
    def focos_hoje(cls, usuario):
        return db.session.scalar(
            cls._focos_concluidos(usuario).where(cls.inicio >= inicio_do_dia_local())
        )

    @classmethod
    def estatisticas(cls, usuario, dias=14):
        """Resumo dos pomodoros de foco concluídos (dias no horário de Brasília)."""
        linhas = db.session.execute(
            db.select(cls.inicio, cls.duracao_min, cls.materia_id).where(
                cls.usuario_id == usuario.id, cls.tipo == "foco", cls.concluida.is_(True)
            )
        ).all()
        nomes = {m.id: m.nome for m in Materia.listar(usuario)}

        por_dia, por_materia, minutos_total = {}, {}, 0
        for inicio, duracao, materia_id in linhas:
            dia = para_local(inicio).date()
            por_dia[dia] = por_dia.get(dia, 0) + 1
            item = por_materia.setdefault(materia_id, [0, 0])
            item[0] += 1
            item[1] += duracao
            minutos_total += duracao

        hoje = hoje_local()
        serie = [
            (hoje - timedelta(days=i), por_dia.get(hoje - timedelta(days=i), 0))
            for i in range(dias - 1, -1, -1)
        ]
        maximo = max((n for _, n in serie), default=0)
        materias = sorted(
            (
                {
                    "nome": nomes.get(mid, "Sem matéria"),
                    "focos": focos,
                    "tempo": formatar_minutos(minutos),
                }
                for mid, (focos, minutos) in por_materia.items()
            ),
            key=lambda m: (-m["focos"], m["nome"].lower()),
        )
        return {
            "total": len(linhas),
            "hoje": por_dia.get(hoje, 0),
            "semana": sum(por_dia.get(hoje - timedelta(days=i), 0) for i in range(7)),
            "tempo_total": formatar_minutos(minutos_total),
            "serie": [
                {"dia": d, "focos": n, "altura": int(n * 100 / maximo) if maximo else 0}
                for d, n in serie
            ],
            "dias": dias,
            "materias": materias,
        }
