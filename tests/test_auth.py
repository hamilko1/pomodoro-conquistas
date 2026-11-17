from app.models import Usuario


def _login(client, email="ana@exemplo.com", senha="senha-segura-123", **extra):
    return client.post("/login", data={"email": email, "senha": senha}, **extra)


def test_paginas_publicas_carregam(client):
    assert client.get("/login").status_code == 200
    assert client.get("/cadastro").status_code == 200


def test_raiz_redireciona_visitante_para_login(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_painel_exige_login(client):
    resp = client.get("/painel")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_cadastro_cria_conta_e_entra(client):
    resp = client.post(
        "/cadastro",
        data={"nome": "Bia", "email": "bia@exemplo.com", "senha": "senha-segura-123",
              "confirmacao": "senha-segura-123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Olá, Bia" in resp.get_data(as_text=True)
    assert Usuario.buscar_por_email("bia@exemplo.com") is not None


def test_cadastro_com_senhas_diferentes(client):
    resp = client.post(
        "/cadastro",
        data={"nome": "Bia", "email": "bia@exemplo.com", "senha": "senha-segura-123",
              "confirmacao": "outra-coisa-123"},
    )
    assert resp.status_code == 200
    assert "As senhas não coincidem." in resp.get_data(as_text=True)
    assert Usuario.buscar_por_email("bia@exemplo.com") is None


def test_cadastro_com_email_repetido_mostra_erro(client, usuario):
    resp = client.post(
        "/cadastro",
        data={"nome": "Ana 2", "email": "ana@exemplo.com", "senha": "senha-segura-123",
              "confirmacao": "senha-segura-123"},
    )
    assert "já está cadastrado" in resp.get_data(as_text=True)


def test_login_correto_leva_ao_painel(client, usuario):
    resp = _login(client, follow_redirects=True)
    assert "Olá, Ana Souza" in resp.get_data(as_text=True)


def test_login_com_senha_errada(client, usuario):
    resp = _login(client, senha="errada")
    assert resp.status_code == 200
    assert "E-mail ou senha incorretos." in resp.get_data(as_text=True)


def test_login_nao_revela_se_o_email_existe(client, usuario):
    a = _login(client, email="ninguem@exemplo.com").get_data(as_text=True)
    b = _login(client, senha="errada").get_data(as_text=True)
    assert "E-mail ou senha incorretos." in a and "E-mail ou senha incorretos." in b


def test_login_respeita_next_interno(client, usuario):
    resp = client.post("/login?next=/painel", data={"email": "ana@exemplo.com", "senha": "senha-segura-123"})
    assert resp.headers["Location"].endswith("/painel")


def test_login_bloqueia_redirecionamento_externo(client, usuario):
    for alvo in ("https://site-malicioso.com", "//site-malicioso.com"):
        resp = client.post(f"/login?next={alvo}", data={"email": "ana@exemplo.com", "senha": "senha-segura-123"})
        assert "malicioso" not in resp.headers["Location"]
        client.post("/logout")


def test_logout_encerra_a_sessao(client, usuario):
    _login(client)
    client.post("/logout")
    assert client.get("/painel").status_code == 302


def test_logout_nao_aceita_get(client, usuario):
    _login(client)
    assert client.get("/logout").status_code == 405
