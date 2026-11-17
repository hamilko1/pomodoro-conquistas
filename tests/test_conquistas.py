from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models import Conquista, Materia, Meta, SessaoPomodoro, Usuario, UsuarioConquista, agora
from app.models.base import FUSO_LOCAL


def _local(ano, mes, dia, hora=12, minuto=0):
    """Horário de Brasília -> UTC sem fuso, como o banco guarda."""
    return datetime(ano, mes, dia, hora, minuto, tzinfo=FUSO_LOCAL).astimezone(timezone.utc).replace(tzinfo=None)


def _foco(usuario, inicio, duracao=25, concluida=True, tipo="foco"):
    db.session.add(SessaoPomodoro(
        usuario_id=usuario.id, inicio=inicio, duracao_min=duracao, tipo=tipo, concluida=concluida,
    ))
    db.session.commit()


def _codigos(conquistas):
    return {c.codigo for c in conquistas}


@pytest.fixture
def catalogo(app):
    Conquista.cadastrar_iniciais()


def test_sem_catalogo_nao_concede_nada(usuario):
    _foco(usuario, _local(2026, 3, 2))
    assert Conquista.avaliar(usuario) == []


def test_primeiro_foco_e_concedido_uma_unica_vez(usuario, catalogo):
    assert Conquista.avaliar(usuario) == []
    _foco(usuario, _local(2026, 3, 2))
    assert _codigos(Conquista.avaliar(usuario)) == {"primeiro_foco"}
    assert Conquista.avaliar(usuario) == []
    assert db.session.scalar(db.select(db.func.count()).select_from(UsuarioConquista)) == 1


def test_pausa_e_sessao_nao_concluida_nao_contam(usuario, catalogo):
    _foco(usuario, _local(2026, 3, 2), tipo="pausa_curta", duracao=5)
    _foco(usuario, _local(2026, 3, 2), concluida=False)
    assert Conquista.avaliar(usuario) == []


def test_dez_focos(usuario, catalogo):
    for i in range(9):
        _foco(usuario, _local(2026, 3, 2 + i))
    assert "dez_focos" not in _codigos(Conquista.avaliar(usuario))
    _foco(usuario, _local(2026, 3, 20))
    assert "dez_focos" in _codigos(Conquista.avaliar(usuario))


def test_maratonista_exige_quatro_no_mesmo_dia(usuario, catalogo):
    for h in (9, 10, 11):
        _foco(usuario, _local(2026, 3, 2, h))
    assert "maratonista" not in _codigos(Conquista.avaliar(usuario))
    _foco(usuario, _local(2026, 3, 3, 9))  # outro dia não ajuda
    assert "maratonista" not in _codigos(Conquista.avaliar(usuario))
    _foco(usuario, _local(2026, 3, 2, 14))
    assert "maratonista" in _codigos(Conquista.avaliar(usuario))


def test_sequencia_de_dias_seguidos(usuario, catalogo):
    for dia in (2, 3, 5):  # falta o dia 4
        _foco(usuario, _local(2026, 3, dia))
    assert "sequencia_3" not in _codigos(Conquista.avaliar(usuario))
    _foco(usuario, _local(2026, 3, 4))
    assert "sequencia_3" in _codigos(Conquista.avaliar(usuario))


def test_dia_e_contado_no_horario_de_brasilia(usuario, catalogo):
    # 23:30 e 00:30 locais são 2 dias diferentes, mesmo estando a 1h de distância em UTC
    _foco(usuario, _local(2026, 3, 2, 23, 30))
    _foco(usuario, _local(2026, 3, 3, 0, 30))
    _foco(usuario, _local(2026, 3, 4, 12))
    assert "sequencia_3" in _codigos(Conquista.avaliar(usuario))


def test_coruja_depois_das_22h(usuario, catalogo):
    _foco(usuario, _local(2026, 3, 2, 21, 20))  # termina 21:45
    assert "coruja" not in _codigos(Conquista.avaliar(usuario))
    _foco(usuario, _local(2026, 3, 3, 21, 50))  # termina 22:15
    assert "coruja" in _codigos(Conquista.avaliar(usuario))


def test_madrugador_antes_das_7h(usuario, catalogo):
    _foco(usuario, _local(2026, 3, 2, 6, 35))  # termina 07:00 -> não conta
    assert "madrugador" not in _codigos(Conquista.avaliar(usuario))
    _foco(usuario, _local(2026, 3, 3, 6, 0))  # termina 06:25
    assert "madrugador" in _codigos(Conquista.avaliar(usuario))


def test_meta_cumprida(usuario, catalogo):
    meta = Meta.criar(usuario, "Estudar", 1)
    assert "meta_cumprida" not in _codigos(Conquista.avaliar(usuario))
    meta.concluida = True
    db.session.commit()
    assert "meta_cumprida" in _codigos(Conquista.avaliar(usuario))


def test_sessoes_de_outro_usuario_nao_contam(usuario, catalogo):
    outro = Usuario.cadastrar("Beto", "beto@exemplo.com", "senha-segura-123")
    _foco(outro, _local(2026, 3, 2))
    assert Conquista.avaliar(usuario) == []
    assert _codigos(Conquista.avaliar(outro)) == {"primeiro_foco"}


def test_concede_retroativamente_varias_de_uma_vez(usuario, catalogo):
    for h in (9, 10, 11, 14):
        _foco(usuario, _local(2026, 3, 2, h))
    assert _codigos(Conquista.avaliar(usuario)) == {"primeiro_foco", "maratonista"}


def test_vitrine_mostra_data_e_progresso(usuario, catalogo):
    for dia in (2, 3):
        _foco(usuario, _local(2026, 3, dia))
    Conquista.avaliar(usuario)
    itens = {i["conquista"].codigo: i for i in Conquista.vitrine(usuario)}
    assert len(itens) == 10
    assert itens["primeiro_foco"]["data"] is not None and itens["primeiro_foco"]["progresso"] is None
    assert itens["dez_focos"]["data"] is None and itens["dez_focos"]["progresso"] == (2, 10)
    assert itens["sequencia_3"]["progresso"] == (2, 3)
    assert itens["coruja"]["progresso"] is None  # regra de horário não tem barra
    # conquistadas vêm primeiro
    ordem = [i["data"] is not None for i in Conquista.vitrine(usuario)]
    assert ordem == sorted(ordem, reverse=True)
