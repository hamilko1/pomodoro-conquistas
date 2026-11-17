from datetime import timedelta

from app.extensions import db
from app.models import Materia, Meta, SessaoPomodoro, Usuario, agora
from app.models.base import hoje_local


def _entrar(client, email="ana@exemplo.com", senha="senha-segura-123"):
    client.post("/login", data={"email": email, "senha": senha})


def test_paginas_exigem_login(client):
    for url in ("/materias/", "/metas/", "/materias/1/editar", "/metas/1/editar"):
        resp = client.get(url)
        assert resp.status_code == 302 and "/login" in resp.headers["Location"]
    assert client.post("/materias/1/excluir").status_code == 302
    assert client.post("/metas/1/excluir").status_code == 302


def test_criar_listar_renomear_e_excluir_materia(client, usuario):
    _entrar(client)
    resp = client.post("/materias/", data={"nome": "Cálculo I"}, follow_redirects=True)
    assert "Matéria criada." in resp.get_data(as_text=True)
    assert "Cálculo I" in client.get("/materias/").get_data(as_text=True)

    materia = Materia.listar(usuario)[0]
    resp = client.post(f"/materias/{materia.id}/editar", data={"nome": "Cálculo II"}, follow_redirects=True)
    assert "Cálculo II" in resp.get_data(as_text=True)

    resp = client.post(f"/materias/{materia.id}/excluir", follow_redirects=True)
    assert "Matéria excluída" in resp.get_data(as_text=True)
    assert Materia.listar(usuario) == []


def test_materia_invalida_mostra_erro(client, usuario):
    _entrar(client)
    resp = client.post("/materias/", data={"nome": "  "})
    assert resp.status_code == 200 and "Informe o nome" in resp.get_data(as_text=True)


def test_materia_aparece_no_seletor_do_timer(client, usuario):
    _entrar(client)
    client.post("/materias/", data={"nome": "Estruturas de Dados"})
    assert "Estruturas de Dados" in client.get("/painel").get_data(as_text=True)


def test_nao_acessa_materia_de_outro_usuario(client, usuario):
    outro = Usuario.cadastrar("Beto", "beto@exemplo.com", "senha-segura-123")
    alheia = Materia.criar(outro, "Química")
    _entrar(client)
    assert client.get(f"/materias/{alheia.id}/editar").status_code == 404
    assert client.post(f"/materias/{alheia.id}/editar", data={"nome": "X"}).status_code == 404
    assert client.post(f"/materias/{alheia.id}/excluir").status_code == 404
    assert db.session.get(Materia, alheia.id).nome == "Química"


def test_nao_acessa_meta_de_outro_usuario(client, usuario):
    outro = Usuario.cadastrar("Beto", "beto@exemplo.com", "senha-segura-123")
    alheia = Meta.criar(outro, "Estudar", 5)
    _entrar(client)
    assert client.get(f"/metas/{alheia.id}/editar").status_code == 404
    assert client.post(f"/metas/{alheia.id}/editar", data={"descricao": "X", "quantidade_alvo": 1}).status_code == 404
    assert client.post(f"/metas/{alheia.id}/excluir").status_code == 404
    assert db.session.get(Meta, alheia.id) is not None


def test_criar_editar_e_excluir_meta(client, usuario):
    _entrar(client)
    materia = Materia.criar(usuario, "Cálculo")
    prazo = (hoje_local() + timedelta(days=3)).isoformat()
    resp = client.post(
        "/metas/",
        data={"descricao": "10 de Cálculo", "quantidade_alvo": "10", "prazo": prazo, "materia_id": materia.id},
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert "Meta criada." in html and "10 de Cálculo" in html and "0 de 10 pomodoros" in html

    meta = Meta.listar(usuario)[0]
    resp = client.post(
        f"/metas/{meta.id}/editar",
        data={"descricao": "12 de Cálculo", "quantidade_alvo": "12", "prazo": "", "materia_id": ""},
        follow_redirects=True,
    )
    assert "12 de Cálculo" in resp.get_data(as_text=True)

    client.post(f"/metas/{meta.id}/excluir")
    assert Meta.listar(usuario) == []


def test_meta_invalida_mostra_erro_e_nao_grava(client, usuario):
    _entrar(client)
    resp = client.post("/metas/", data={"descricao": "Estudar", "quantidade_alvo": "0"})
    assert resp.status_code == 200 and "número inteiro" in resp.get_data(as_text=True)
    assert Meta.listar(usuario) == []


def test_meta_cumprida_nao_abre_edicao(client, usuario):
    meta = Meta.criar(usuario, "Estudar", 1)
    meta.concluida = True
    db.session.commit()
    _entrar(client)
    resp = client.get(f"/metas/{meta.id}/editar", follow_redirects=True)
    assert "não pode ser editada" in resp.get_data(as_text=True)


def test_concluir_foco_cumpre_a_meta(client, usuario):
    _entrar(client)
    meta = Meta.criar(usuario, "Um pomodoro", 1)
    sid = client.post("/api/sessoes/iniciar", json={"tipo": "foco", "duracao_min": 25}).get_json()["id"]
    sessao = db.session.get(SessaoPomodoro, sid)
    sessao.inicio = agora() - timedelta(minutes=26)
    meta.data_criacao = agora() - timedelta(minutes=30)
    db.session.commit()

    dados = client.post(f"/api/sessoes/{sid}/concluir").get_json()
    assert dados["metas_cumpridas"] == ["Um pomodoro"]
    assert db.session.get(Meta, meta.id).concluida is True
    assert "Cumprida" in client.get("/metas/").get_data(as_text=True)


def test_pausa_nao_avalia_metas(client, usuario):
    _entrar(client)
    sid = client.post("/api/sessoes/iniciar", json={"tipo": "pausa_curta", "duracao_min": 5}).get_json()["id"]
    sessao = db.session.get(SessaoPomodoro, sid)
    sessao.inicio = agora() - timedelta(minutes=6)
    db.session.commit()
    assert "metas_cumpridas" not in client.post(f"/api/sessoes/{sid}/concluir").get_json()
