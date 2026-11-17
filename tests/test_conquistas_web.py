from datetime import timedelta

from app.extensions import db
from app.models import Conquista, Meta, SessaoPomodoro, agora


def _entrar(client, email="ana@exemplo.com", senha="senha-segura-123"):
    client.post("/login", data={"email": email, "senha": senha})


def _foco_pronto_para_concluir(client):
    sid = client.post("/api/sessoes/iniciar", json={"tipo": "foco", "duracao_min": 25}).get_json()["id"]
    sessao = db.session.get(SessaoPomodoro, sid)
    sessao.inicio = agora() - timedelta(minutes=26)
    db.session.commit()
    return sid


def test_pagina_exige_login(client):
    resp = client.get("/conquistas/")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]


def test_pagina_com_catalogo_vazio_orienta_a_rodar_o_seed(client, usuario):
    _entrar(client)
    assert "flask --app run seed" in client.get("/conquistas/").get_data(as_text=True)


def test_pagina_lista_o_catalogo(client, usuario):
    Conquista.cadastrar_iniciais()
    _entrar(client)
    html = client.get("/conquistas/").get_data(as_text=True)
    assert "Primeiro Foco" in html and "Madrugador" in html and "0 de 10 conquistadas" in html


def test_concluir_foco_devolve_conquista_nova(client, usuario):
    Conquista.cadastrar_iniciais()
    _entrar(client)
    sid = _foco_pronto_para_concluir(client)
    dados = client.post(f"/api/sessoes/{sid}/concluir").get_json()
    nomes = [c["nome"] for c in dados["conquistas_novas"]]
    assert "Primeiro Foco" in nomes
    # (não conto o total: Coruja/Madrugador dependem da hora em que o teste roda)
    assert "Conquistada em" in client.get("/conquistas/").get_data(as_text=True)


def test_segundo_foco_nao_repete_a_conquista(client, usuario):
    Conquista.cadastrar_iniciais()
    _entrar(client)
    client.post(f"/api/sessoes/{_foco_pronto_para_concluir(client)}/concluir")
    dados = client.post(f"/api/sessoes/{_foco_pronto_para_concluir(client)}/concluir").get_json()
    assert "conquistas_novas" not in dados


def test_meta_cumprida_e_conquista_na_mesma_resposta(client, usuario):
    Conquista.cadastrar_iniciais()
    _entrar(client)
    meta = Meta.criar(usuario, "Um pomodoro", 1)
    meta.data_criacao = agora() - timedelta(minutes=40)
    db.session.commit()
    dados = client.post(f"/api/sessoes/{_foco_pronto_para_concluir(client)}/concluir").get_json()
    assert dados["metas_cumpridas"] == ["Um pomodoro"]
    assert "Meta Cumprida" in [c["nome"] for c in dados["conquistas_novas"]]


def test_pausa_nao_avalia_conquistas(client, usuario):
    Conquista.cadastrar_iniciais()
    _entrar(client)
    sid = client.post("/api/sessoes/iniciar", json={"tipo": "pausa_curta", "duracao_min": 5}).get_json()["id"]
    sessao = db.session.get(SessaoPomodoro, sid)
    sessao.inicio = agora() - timedelta(minutes=6)
    db.session.commit()
    assert "conquistas_novas" not in client.post(f"/api/sessoes/{sid}/concluir").get_json()
