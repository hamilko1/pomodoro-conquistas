from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models import ErroValidacao, Materia, SessaoPomodoro, Usuario, agora
from app.models.base import inicio_do_dia_local


def _terminar_tempo(sessao, minutos=None):
    """Simula a passagem do tempo recuando o início da sessão."""
    sessao.inicio = agora() - timedelta(minutes=(minutos or sessao.duracao_min) + 1)
    db.session.commit()


def test_iniciar_cria_sessao_nao_concluida(usuario):
    s = SessaoPomodoro.iniciar(usuario, "foco", 25)
    assert s.id is not None
    assert s.concluida is False
    assert s.tipo == "foco" and s.duracao_min == 25 and s.materia_id is None


def test_iniciar_com_materia_propria(usuario):
    m = Materia(usuario_id=usuario.id, nome="Cálculo")
    db.session.add(m)
    db.session.commit()
    assert SessaoPomodoro.iniciar(usuario, "foco", 25, m.id).materia_id == m.id


def test_iniciar_com_materia_de_outro_usuario_e_rejeitado(usuario):
    outro = Usuario.cadastrar("Beto", "beto@exemplo.com", "senha-segura-123")
    m = Materia(usuario_id=outro.id, nome="Física")
    db.session.add(m)
    db.session.commit()
    with pytest.raises(ErroValidacao, match="Matéria não encontrada"):
        SessaoPomodoro.iniciar(usuario, "foco", 25, m.id)


@pytest.mark.parametrize("materia_id", [9999, "1", 1.5, True])
def test_iniciar_com_materia_invalida(usuario, materia_id):
    with pytest.raises(ErroValidacao):
        SessaoPomodoro.iniciar(usuario, "foco", 25, materia_id)


@pytest.mark.parametrize("tipo", ["", "descanso", None, "FOCO"])
def test_tipo_invalido(usuario, tipo):
    with pytest.raises(ErroValidacao, match="Tipo"):
        SessaoPomodoro.iniciar(usuario, tipo, 25)


@pytest.mark.parametrize("duracao", [0, -5, 181, "25", 25.5, None, True])
def test_duracao_invalida(usuario, duracao):
    with pytest.raises(ErroValidacao, match="duração"):
        SessaoPomodoro.iniciar(usuario, "foco", duracao)


@pytest.mark.parametrize("duracao", [1, 180])
def test_duracao_nos_limites(usuario, duracao):
    assert SessaoPomodoro.iniciar(usuario, "foco", duracao).duracao_min == duracao


def test_concluir_antes_do_tempo_e_recusado(usuario):
    s = SessaoPomodoro.iniciar(usuario, "foco", 25)
    with pytest.raises(ErroValidacao, match="ainda não terminou"):
        s.concluir()
    assert s.concluida is False


def test_concluir_depois_do_tempo(usuario):
    s = SessaoPomodoro.iniciar(usuario, "foco", 25)
    _terminar_tempo(s)
    s.concluir()
    assert s.concluida is True


def test_concluir_aceita_pequena_folga_de_relogio(usuario):
    s = SessaoPomodoro.iniciar(usuario, "foco", 25)
    s.inicio = agora() - timedelta(minutes=25) + timedelta(seconds=3)  # faltam 3 s
    db.session.commit()
    s.concluir()
    assert s.concluida is True


def test_concluir_duas_vezes_e_recusado(usuario):
    s = SessaoPomodoro.iniciar(usuario, "foco", 25)
    _terminar_tempo(s)
    s.concluir()
    with pytest.raises(ErroValidacao, match="já foi concluída"):
        s.concluir()


def test_placar_conta_apenas_focos_concluidos(usuario):
    concluido = SessaoPomodoro.iniciar(usuario, "foco", 25)
    _terminar_tempo(concluido)
    concluido.concluir()

    pausa = SessaoPomodoro.iniciar(usuario, "pausa_curta", 5)
    _terminar_tempo(pausa)
    pausa.concluir()

    SessaoPomodoro.iniciar(usuario, "foco", 25)  # abandonado

    assert SessaoPomodoro.focos_hoje(usuario) == 1
    assert SessaoPomodoro.total_focos(usuario) == 1


def test_focos_de_dias_anteriores_contam_no_total_mas_nao_hoje(usuario):
    s = SessaoPomodoro.iniciar(usuario, "foco", 25)
    _terminar_tempo(s)
    s.concluir()
    s.inicio = agora() - timedelta(days=2)
    db.session.commit()
    assert SessaoPomodoro.focos_hoje(usuario) == 0
    assert SessaoPomodoro.total_focos(usuario) == 1


def test_placar_e_separado_por_usuario(usuario):
    outro = Usuario.cadastrar("Beto", "beto@exemplo.com", "senha-segura-123")
    s = SessaoPomodoro.iniciar(outro, "foco", 25)
    _terminar_tempo(s)
    s.concluir()
    assert SessaoPomodoro.total_focos(usuario) == 0
    assert SessaoPomodoro.total_focos(outro) == 1


def test_inicio_do_dia_local_esta_nas_ultimas_24h():
    diferenca = agora() - inicio_do_dia_local()
    assert timedelta(0) <= diferenca < timedelta(hours=24)
