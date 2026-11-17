from datetime import date

from ..extensions import db
from .base import ErroValidacao, agora, fim_do_dia_local, hoje_local
from .materia import Materia
from .sessao import SessaoPomodoro

DESCRICAO_MAX = 150
ALVO_MIN = 1
ALVO_MAX = 500


class Meta(db.Model):
    __tablename__ = "metas"
    __table_args__ = (db.CheckConstraint("quantidade_alvo > 0", name="ck_meta_alvo"),)

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey("materias.id", ondelete="SET NULL"))
    descricao = db.Column(db.String(150), nullable=False)
    quantidade_alvo = db.Column(db.SmallInteger, nullable=False)
    prazo = db.Column(db.Date)
    # Só contam para a meta os pomodoros feitos depois que ela foi criada
    data_criacao = db.Column(db.DateTime, nullable=False, default=agora)
    concluida = db.Column(db.Boolean, nullable=False, default=False)
    data_conclusao = db.Column(db.DateTime)

    usuario = db.relationship("Usuario", back_populates="metas")
    materia = db.relationship("Materia")

    # ---------- validação ----------
    @staticmethod
    def _ler_dados(usuario, descricao, quantidade_alvo, prazo, materia_id):
        """Valida e converte os dados vindos do formulário."""
        descricao = (descricao or "").strip()
        if not descricao:
            raise ErroValidacao("Descreva a meta.")
        if len(descricao) > DESCRICAO_MAX:
            raise ErroValidacao(f"A descrição pode ter no máximo {DESCRICAO_MAX} caracteres.")

        try:
            if isinstance(quantidade_alvo, bool):
                raise ValueError
            alvo = int(str(quantidade_alvo).strip())
        except (TypeError, ValueError):
            alvo = None
        if alvo is None or not ALVO_MIN <= alvo <= ALVO_MAX:
            raise ErroValidacao(f"A quantidade deve ser um número inteiro de {ALVO_MIN} a {ALVO_MAX}.")

        if isinstance(prazo, str):
            prazo = prazo.strip()
            if not prazo:
                prazo = None
            else:
                try:
                    prazo = date.fromisoformat(prazo)
                except ValueError:
                    raise ErroValidacao("Informe um prazo válido.")

        if materia_id in ("", None):
            materia_id = None
        else:
            try:
                materia_id = int(materia_id)
            except (TypeError, ValueError):
                raise ErroValidacao("Matéria não encontrada.")
            if Materia.buscar(usuario, materia_id) is None:
                raise ErroValidacao("Matéria não encontrada.")

        return descricao, alvo, prazo, materia_id

    # ---------- consultas ----------
    @classmethod
    def listar(cls, usuario):
        """Metas abertas primeiro (prazo mais próximo antes), depois as concluídas."""
        metas = list(db.session.scalars(db.select(cls).where(cls.usuario_id == usuario.id)))
        metas.sort(
            key=lambda m: (
                m.concluida,
                m.prazo is None,
                m.prazo or date.max,
                -m.id,
            )
        )
        return metas

    @classmethod
    def buscar(cls, usuario, meta_id):
        meta = db.session.get(cls, meta_id)
        if meta is None or meta.usuario_id != usuario.id:
            return None
        return meta

    # ---------- progresso ----------
    def contagem(self):
        """Pomodoros de foco concluídos que contam para esta meta."""
        consulta = db.select(db.func.count()).select_from(SessaoPomodoro).where(
            SessaoPomodoro.usuario_id == self.usuario_id,
            SessaoPomodoro.tipo == "foco",
            SessaoPomodoro.concluida.is_(True),
            SessaoPomodoro.inicio >= self.data_criacao,
        )
        if self.materia_id is not None:
            consulta = consulta.where(SessaoPomodoro.materia_id == self.materia_id)
        if self.prazo is not None:
            consulta = consulta.where(SessaoPomodoro.inicio < fim_do_dia_local(self.prazo))
        return db.session.scalar(consulta)

    @property
    def feitos(self):
        return min(self.contagem(), self.quantidade_alvo)

    @property
    def percentual(self):
        return int(self.feitos * 100 / self.quantidade_alvo)

    @property
    def situacao(self):
        if self.concluida:
            return "concluida"
        if self.prazo is not None and self.prazo < hoje_local():
            return "vencida"
        return "andamento"

    @classmethod
    def avaliar_concluidas(cls, usuario):
        """Marca como cumpridas as metas abertas que atingiram o alvo.

        Retorna a lista das metas que acabaram de ser cumpridas.
        """
        abertas = db.session.scalars(
            db.select(cls).where(cls.usuario_id == usuario.id, cls.concluida.is_(False))
        ).all()
        novas = [m for m in abertas if m.contagem() >= m.quantidade_alvo]
        for meta in novas:
            meta.concluida = True
            meta.data_conclusao = agora()
        if novas:
            db.session.commit()
        return novas

    # ---------- comandos ----------
    @classmethod
    def criar(cls, usuario, descricao, quantidade_alvo, prazo=None, materia_id=None):
        descricao, alvo, prazo, materia_id = cls._ler_dados(
            usuario, descricao, quantidade_alvo, prazo, materia_id
        )
        if prazo is not None and prazo < hoje_local():
            raise ErroValidacao("O prazo não pode estar no passado.")
        meta = cls(
            usuario_id=usuario.id,
            descricao=descricao,
            quantidade_alvo=alvo,
            prazo=prazo,
            materia_id=materia_id,
        )
        db.session.add(meta)
        db.session.commit()
        return meta

    def editar(self, descricao, quantidade_alvo, prazo=None, materia_id=None):
        if self.concluida:
            raise ErroValidacao("Uma meta cumprida não pode ser editada.")
        descricao, alvo, prazo, materia_id = self._ler_dados(
            self.usuario, descricao, quantidade_alvo, prazo, materia_id
        )
        if prazo is not None and prazo != self.prazo and prazo < hoje_local():
            raise ErroValidacao("O prazo não pode estar no passado.")
        self.descricao = descricao
        self.quantidade_alvo = alvo
        self.prazo = prazo
        self.materia_id = materia_id
        db.session.commit()
        # Reduzir o alvo pode fazer a meta já estar cumprida
        Meta.avaliar_concluidas(self.usuario)

    def excluir(self):
        db.session.delete(self)
        db.session.commit()
