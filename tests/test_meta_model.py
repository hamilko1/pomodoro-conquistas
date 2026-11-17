from datetime import timedelta

import pytest

from app.extensions import db
from app.models import ErroValidacao, Materia, Meta, SessaoPomodoro, Usuario, agora
from app.models.base import hoje_local


@pytest.fixture
def materia(usuario):
    return Materia.criar(usuario, "Cálculo")


def _foco(usuario, materia=None, inicio=None, concluida=True, tipo="foco"):
    db.session.add(SessaoPomodoro(
        usuario_id=usuario.id, materia_id=materia.id if materia else None,
        inicio=inicio or agora(), duracao_min=25, tipo=tipo, concluida=concluida,
    ))
    db.session.commit()


def test_criar_meta(usuario, materia):
    amanha = hoje_local() + timedelta(days=1)
    m = Meta.criar(usuario, "  10 de Cálculo ", "10", amanha.isoformat(), str(materia.id))
    assert (m.descricao, m.quantidade_alvo, m.prazo, m.materia_id) == ("10 de Cálculo", 10, amanha, materia.id)
    assert m.data_criacao is not None and m.concluida is False


def test_criar_meta_minima(usuario):
    m = Meta.criar(usuario, "Estudar", 3)
    assert m.prazo is None and m.materia_id is None


@pytest.mark.parametrize("descricao,alvo", [
    ("", 5), ("   ", 5), ("x" * 151, 5),
    ("ok", 0), ("ok", -1), ("ok", "abc"), ("ok", ""), ("ok", None), ("ok", 501), ("ok", 2.5), ("ok", True),
])
def test_criar_meta_invalida(usuario, descricao, alvo):
    with pytest.raises(ErroValidacao):
        Meta.criar(usuario, descricao, alvo)


def test_prazo_no_passado_e_invalido(usuario):
    ontem = hoje_local() - timedelta(days=1)
    with pytest.raises(ErroValidacao, match="passado"):
        Meta.criar(usuario, "Estudar", 3, ontem.isoformat())


def test_prazo_hoje_e_valido_e_texto_invalido_nao(usuario):
    assert Meta.criar(usuario, "Estudar", 3, hoje_local().isoformat()).prazo == hoje_local()
    with pytest.raises(ErroValidacao):
        Meta.criar(usuario, "Estudar", 3, "31/12/2030")


def test_materia_de_outro_usuario_e_recusada(usuario):
    outro = Usuario.cadastrar("Beto", "beto@exemplo.com", "senha-segura-123")
    alheia = Materia.criar(outro, "Química")
    with pytest.raises(ErroValidacao, match="Matéria"):
        Meta.criar(usuario, "Estudar", 3, materia_id=alheia.id)
    with pytest.raises(ErroValidacao):
        Meta.criar(usuario, "Estudar", 3, materia_id="abc")


def test_contagem_ignora_sessoes_anteriores_a_criacao(usuario):
    _foco(usuario, inicio=agora() - timedelta(hours=2))
    m = Meta.criar(usuario, "Estudar", 3)
    assert m.contagem() == 0
    _foco(usuario)
    assert m.contagem() == 1


def test_contagem_so_conta_foco_concluido(usuario):
    m = Meta.criar(usuario, "Estudar", 5)
    m.data_criacao = agora() - timedelta(hours=1)
    _foco(usuario)
    _foco(usuario, concluida=False)
    _foco(usuario, tipo="pausa_curta")
    assert m.contagem() == 1


def test_meta_com_materia_conta_so_aquela_materia(usuario, materia):
    outra = Materia.criar(usuario, "Física")
    m = Meta.criar(usuario, "Cálculo", 5, materia_id=materia.id)
    m.data_criacao = agora() - timedelta(hours=1)
    _foco(usuario, materia)
    _foco(usuario, outra)
    _foco(usuario)
    assert m.contagem() == 1


def test_meta_sem_materia_conta_qualquer_materia(usuario, materia):
    m = Meta.criar(usuario, "Qualquer", 5)
    m.data_criacao = agora() - timedelta(hours=1)
    _foco(usuario, materia)
    _foco(usuario)
    assert m.contagem() == 2


def test_contagem_ignora_sessoes_depois_do_prazo(usuario):
    m = Meta.criar(usuario, "Estudar", 5, hoje_local().isoformat())
    m.data_criacao = agora() - timedelta(days=3)
    _foco(usuario)                                   # hoje: conta
    _foco(usuario, inicio=agora() + timedelta(days=2))  # depois do prazo: não conta
    assert m.contagem() == 1


def test_progresso_e_percentual_limitados_ao_alvo(usuario):
    m = Meta.criar(usuario, "Estudar", 2)
    m.data_criacao = agora() - timedelta(hours=1)
    _foco(usuario)
    assert (m.feitos, m.percentual) == (1, 50)
    _foco(usuario)
    _foco(usuario)
    assert (m.feitos, m.percentual) == (2, 100)


def test_avaliar_conclui_apenas_quando_atinge_o_alvo(usuario):
    m = Meta.criar(usuario, "Estudar", 2)
    m.data_criacao = agora() - timedelta(hours=1)
    _foco(usuario)
    assert Meta.avaliar_concluidas(usuario) == []
    assert m.concluida is False
    _foco(usuario)
    assert Meta.avaliar_concluidas(usuario) == [m]
    assert m.concluida is True and m.data_conclusao is not None
    assert Meta.avaliar_concluidas(usuario) == []  # não repete


def test_situacao(usuario):
    m = Meta.criar(usuario, "Estudar", 2, (hoje_local() + timedelta(days=1)).isoformat())
    assert m.situacao == "andamento"
    m.prazo = hoje_local() - timedelta(days=1)
    assert m.situacao == "vencida"
    m.concluida = True
    assert m.situacao == "concluida"


def test_editar(usuario, materia):
    m = Meta.criar(usuario, "Estudar", 5)
    m.editar("Revisar", "8", "", str(materia.id))
    assert (m.descricao, m.quantidade_alvo, m.prazo, m.materia_id) == ("Revisar", 8, None, materia.id)


def test_editar_meta_vencida_sem_mudar_prazo_e_permitido(usuario):
    m = Meta.criar(usuario, "Estudar", 5)
    m.prazo = hoje_local() - timedelta(days=2)
    db.session.commit()
    m.editar("Novo texto", 5, m.prazo.isoformat())
    assert m.descricao == "Novo texto"


def test_editar_para_prazo_passado_falha(usuario):
    m = Meta.criar(usuario, "Estudar", 5)
    with pytest.raises(ErroValidacao):
        m.editar("Estudar", 5, (hoje_local() - timedelta(days=1)).isoformat())


def test_editar_meta_cumprida_falha(usuario):
    m = Meta.criar(usuario, "Estudar", 5)
    m.concluida = True
    db.session.commit()
    with pytest.raises(ErroValidacao, match="cumprida"):
        m.editar("Outra", 5)


def test_reduzir_alvo_pode_cumprir_a_meta(usuario):
    m = Meta.criar(usuario, "Estudar", 5)
    m.data_criacao = agora() - timedelta(hours=1)
    _foco(usuario)
    _foco(usuario)
    m.editar("Estudar", 2)
    assert m.concluida is True


def test_excluir_e_buscar_isolado_por_usuario(usuario):
    outro = Usuario.cadastrar("Beto", "beto@exemplo.com", "senha-segura-123")
    m = Meta.criar(usuario, "Estudar", 5)
    assert Meta.buscar(outro, m.id) is None
    mid = m.id
    m.excluir()
    assert db.session.get(Meta, mid) is None
