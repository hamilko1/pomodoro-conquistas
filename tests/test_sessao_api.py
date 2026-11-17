from datetime import timedelta

from app.extensions import db
from app.models import SessaoPomodoro, Usuario, agora


def _entrar(client, email="ana@exemplo.com", senha="senha-segura-123"):
    client.post("/login", data={"email": email, "senha": senha})


def _iniciar(client, **extra):
    corpo = {"tipo": "foco", "duracao_min": 25, **extra}
    return client.post("/api/sessoes/iniciar", json=corpo)


def _terminar_tempo(sessao_id):
    sessao = db.session.get(SessaoPomodoro, sessao_id)
    sessao.inicio = agora() - timedelta(minutes=sessao.duracao_min + 1)
    db.session.commit()


def test_api_exige_login_e_responde_json(client):
    resp = _iniciar(client)
    assert resp.status_code == 401
    assert "erro" in resp.get_json()
    assert client.post("/api/sessoes/1/concluir").status_code == 401


def test_iniciar_sessao(client, usuario):
    _entrar(client)
    resp = _iniciar(client)
    assert resp.status_code == 201
    dados = resp.get_json()
    assert dados["tipo"] == "foco" and dados["duracao_min"] == 25
    assert db.session.get(SessaoPomodoro, dados["id"]).concluida is False


def test_iniciar_com_dados_invalidos(client, usuario):
    _entrar(client)
    assert _iniciar(client, tipo="descanso").status_code == 400
    assert _iniciar(client, duracao_min=0).status_code == 400
    assert _iniciar(client, duracao_min="25").status_code == 400
    assert _iniciar(client, materia_id=9999).status_code == 400


def test_iniciar_sem_corpo_json(client, usuario):
    _entrar(client)
    resp = client.post("/api/sessoes/iniciar", data="isto não é json")
    assert resp.status_code == 400


def test_concluir_antes_do_tempo_retorna_409(client, usuario):
    _entrar(client)
    sid = _iniciar(client).get_json()["id"]
    resp = client.post(f"/api/sessoes/{sid}/concluir")
    assert resp.status_code == 409
    assert "ainda não terminou" in resp.get_json()["erro"]


def test_concluir_apos_o_tempo_atualiza_placar(client, usuario):
    _entrar(client)
    sid = _iniciar(client).get_json()["id"]
    _terminar_tempo(sid)
    resp = client.post(f"/api/sessoes/{sid}/concluir")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True, "focos_hoje": 1, "total_focos": 1}


def test_concluir_pausa_nao_conta_como_foco(client, usuario):
    _entrar(client)
    sid = _iniciar(client, tipo="pausa_curta", duracao_min=5).get_json()["id"]
    _terminar_tempo(sid)
    assert client.post(f"/api/sessoes/{sid}/concluir").get_json()["focos_hoje"] == 0


def test_concluir_duas_vezes_retorna_409(client, usuario):
    _entrar(client)
    sid = _iniciar(client).get_json()["id"]
    _terminar_tempo(sid)
    client.post(f"/api/sessoes/{sid}/concluir")
    assert client.post(f"/api/sessoes/{sid}/concluir").status_code == 409


def test_concluir_sessao_inexistente(client, usuario):
    _entrar(client)
    assert client.post("/api/sessoes/9999/concluir").status_code == 404


def test_nao_conclui_sessao_de_outro_usuario(client, usuario):
    _entrar(client)
    sid = _iniciar(client).get_json()["id"]
    _terminar_tempo(sid)
    client.post("/logout")

    Usuario.cadastrar("Beto", "beto@exemplo.com", "senha-segura-123")
    _entrar(client, email="beto@exemplo.com")
    assert client.post(f"/api/sessoes/{sid}/concluir").status_code == 404
    assert db.session.get(SessaoPomodoro, sid).concluida is False


def test_painel_mostra_timer_e_placar(client, usuario):
    _entrar(client)
    html = client.get("/painel").get_data(as_text=True)
    assert 'id="timer"' in html
    assert 'id="focos-hoje"' in html
    assert 'name="csrf-token"' in html
