import pytest

from app.models import ErroValidacao, Usuario


def test_cadastrar_usuario_valido(app):
    u = Usuario.cadastrar("  Ana Souza ", "ANA@Exemplo.com ", "senha-segura-123")
    assert u.id is not None
    assert u.nome == "Ana Souza"
    assert u.email == "ana@exemplo.com"


def test_senha_nunca_e_guardada_em_texto_puro(app):
    u = Usuario.cadastrar("Ana", "ana@exemplo.com", "senha-segura-123")
    assert u.senha_hash != "senha-segura-123"
    assert "senha-segura-123" not in u.senha_hash


def test_email_duplicado_e_rejeitado(usuario):
    with pytest.raises(ErroValidacao, match="já está cadastrado"):
        Usuario.cadastrar("Outra Ana", "ANA@exemplo.com", "outra-senha-123")


@pytest.mark.parametrize(
    "nome, email, senha, trecho",
    [
        ("", "a@b.com", "senha-segura-123", "nome"),
        ("   ", "a@b.com", "senha-segura-123", "nome"),
        ("Ana", "sem-arroba", "senha-segura-123", "e-mail"),
        ("Ana", "", "senha-segura-123", "e-mail"),
        ("Ana", "a@b.com", "curta", "senha"),
        ("Ana", "a@b.com", None, "senha"),
        ("A" * 101, "a@b.com", "senha-segura-123", "nome"),
    ],
)
def test_dados_invalidos_sao_rejeitados(app, nome, email, senha, trecho):
    with pytest.raises(ErroValidacao, match=trecho):
        Usuario.cadastrar(nome, email, senha)


def test_autenticar_com_credenciais_corretas(usuario):
    assert Usuario.autenticar("ana@exemplo.com", "senha-segura-123") == usuario
    assert Usuario.autenticar("  ANA@exemplo.com", "senha-segura-123") == usuario


def test_autenticar_com_senha_errada(usuario):
    assert Usuario.autenticar("ana@exemplo.com", "senha-errada") is None


def test_autenticar_com_email_inexistente(app):
    assert Usuario.autenticar("ninguem@exemplo.com", "qualquer-coisa") is None
