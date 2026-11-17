from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import Materia, SessaoPomodoro, Usuario
from app.models.base import FUSO_LOCAL, hoje_local
from app.models.sessao import formatar_minutos


def _local(dia, hora=12):
    return (
        datetime(dia.year, dia.month, dia.day, hora, tzinfo=FUSO_LOCAL)
        .astimezone(timezone.utc)
        .replace(tzinfo=None)
    )


def _foco(usuario, dia, hora=12, materia=None, duracao=25, concluida=True, tipo="foco"):
    db.session.add(SessaoPomodoro(
        usuario_id=usuario.id, materia_id=materia.id if materia else None,
        inicio=_local(dia, hora), duracao_min=duracao, tipo=tipo, concluida=concluida,
    ))
    db.session.commit()


def _entrar(client):
    client.post("/login", data={"email": "ana@exemplo.com", "senha": "senha-segura-123"})


def test_formatar_minutos():
    assert formatar_minutos(0) == "0min"
    assert formatar_minutos(25) == "25min"
    assert formatar_minutos(60) == "1h"
    assert formatar_minutos(90) == "1h30min"
    assert formatar_minutos(125) == "2h05min"


def test_estatisticas_sem_sessoes(usuario):
    est = SessaoPomodoro.estatisticas(usuario)
    assert (est["total"], est["hoje"], est["semana"], est["tempo_total"]) == (0, 0, 0, "0min")
    assert len(est["serie"]) == 14 and all(d["altura"] == 0 for d in est["serie"])
    assert est["materias"] == []


def test_totais_hoje_semana_e_tempo(usuario):
    hoje = hoje_local()
    _foco(usuario, hoje)
    _foco(usuario, hoje, hora=14)
    _foco(usuario, hoje - timedelta(days=3))
    _foco(usuario, hoje - timedelta(days=10))  # fora da semana, mas dentro dos 14 dias
    est = SessaoPomodoro.estatisticas(usuario)
    assert (est["total"], est["hoje"], est["semana"]) == (4, 2, 3)
    assert est["tempo_total"] == "1h40min"


def test_ignora_pausas_e_sessoes_nao_concluidas(usuario):
    hoje = hoje_local()
    _foco(usuario, hoje, tipo="pausa_curta", duracao=5)
    _foco(usuario, hoje, concluida=False)
    assert SessaoPomodoro.estatisticas(usuario)["total"] == 0


def test_serie_termina_hoje_e_escala_pela_maior_coluna(usuario):
    hoje = hoje_local()
    for h in (9, 10, 11, 12):
        _foco(usuario, hoje, hora=h)
    _foco(usuario, hoje - timedelta(days=1))
    serie = SessaoPomodoro.estatisticas(usuario)["serie"]
    assert serie[-1]["dia"] == hoje and serie[-1]["focos"] == 4 and serie[-1]["altura"] == 100
    assert serie[-2]["focos"] == 1 and serie[-2]["altura"] == 25


def test_por_materia_ordenado_e_com_sem_materia(usuario):
    hoje = hoje_local()
    calc = Materia.criar(usuario, "Cálculo")
    fis = Materia.criar(usuario, "Física")
    _foco(usuario, hoje, materia=fis)
    _foco(usuario, hoje, materia=calc)
    _foco(usuario, hoje, materia=calc, duracao=50)
    _foco(usuario, hoje)
    materias = SessaoPomodoro.estatisticas(usuario)["materias"]
    assert [(m["nome"], m["focos"], m["tempo"]) for m in materias] == [
        ("Cálculo", 2, "1h15min"), ("Física", 1, "25min"), ("Sem matéria", 1, "25min"),
    ]


def test_nao_mistura_dados_de_outro_usuario(usuario):
    outro = Usuario.cadastrar("Beto", "beto@exemplo.com", "senha-segura-123")
    _foco(outro, hoje_local())
    assert SessaoPomodoro.estatisticas(usuario)["total"] == 0


def test_pagina_exige_login(client):
    resp = client.get("/estatisticas/")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]


def test_pagina_vazia_e_com_dados(client, usuario):
    _entrar(client)
    html = client.get("/estatisticas/").get_data(as_text=True)
    assert "Nenhum pomodoro concluído ainda" in html

    calc = Materia.criar(usuario, "Cálculo")
    _foco(usuario, hoje_local(), materia=calc)
    html = client.get("/estatisticas/").get_data(as_text=True)
    assert "Pomodoros por dia" in html and "Cálculo" in html and "25min" in html
