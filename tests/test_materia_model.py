import pytest

from app.extensions import db
from app.models import ErroValidacao, Materia, Meta, SessaoPomodoro, Usuario, agora


@pytest.fixture
def outro(app):
    return Usuario.cadastrar("Beto Lima", "beto@exemplo.com", "senha-segura-123")


def _sessao(usuario, materia, concluida=True, tipo="foco"):
    s = SessaoPomodoro(
        usuario_id=usuario.id, materia_id=materia.id if materia else None,
        inicio=agora(), duracao_min=25, tipo=tipo, concluida=concluida,
    )
    db.session.add(s)
    db.session.commit()
    return s


def test_criar_materia_remove_espacos(usuario):
    m = Materia.criar(usuario, "  Cálculo I  ")
    assert m.nome == "Cálculo I" and m.usuario_id == usuario.id


@pytest.mark.parametrize("nome", ["", "   ", None, "x" * 81])
def test_criar_nome_invalido(usuario, nome):
    with pytest.raises(ErroValidacao):
        Materia.criar(usuario, nome)


def test_nome_duplicado_ignora_maiusculas(usuario):
    Materia.criar(usuario, "Física")
    with pytest.raises(ErroValidacao, match="já tem"):
        Materia.criar(usuario, "FÍSICA")


def test_mesmo_nome_em_usuarios_diferentes(usuario, outro):
    Materia.criar(usuario, "Física")
    assert Materia.criar(outro, "Física").id is not None


def test_listar_em_ordem_alfabetica_so_do_usuario(usuario, outro):
    Materia.criar(usuario, "banco de dados")
    Materia.criar(usuario, "Álgebra")
    Materia.criar(outro, "Química")
    nomes = [m.nome for m in Materia.listar(usuario)]
    assert sorted(nomes) == sorted(["banco de dados", "Álgebra"])  # só as do usuário
    assert "Química" not in nomes


def test_buscar_nao_devolve_materia_de_outro_usuario(usuario, outro):
    m = Materia.criar(outro, "Química")
    assert Materia.buscar(usuario, m.id) is None
    assert Materia.buscar(outro, m.id) is m


def test_renomear(usuario):
    m = Materia.criar(usuario, "Calculo")
    m.renomear("Cálculo")
    assert db.session.get(Materia, m.id).nome == "Cálculo"


def test_renomear_para_nome_existente_falha(usuario):
    Materia.criar(usuario, "Física")
    m = Materia.criar(usuario, "Química")
    with pytest.raises(ErroValidacao):
        m.renomear("física")


def test_renomear_mudando_so_a_caixa_e_permitido(usuario):
    m = Materia.criar(usuario, "fisica")
    m.renomear("Fisica")
    assert m.nome == "Fisica"


def test_focos_concluidos_conta_so_focos_concluidos(usuario):
    m = Materia.criar(usuario, "Física")
    _sessao(usuario, m)
    _sessao(usuario, m, concluida=False)
    _sessao(usuario, m, tipo="pausa_curta")
    assert m.focos_concluidos() == 1


def test_excluir_mantem_sessoes_sem_materia(usuario):
    m = Materia.criar(usuario, "Física")
    s = _sessao(usuario, m)
    mid = m.id
    m.excluir()
    assert db.session.get(Materia, mid) is None
    assert db.session.get(SessaoPomodoro, s.id).materia_id is None


def test_excluir_apaga_metas_abertas_e_mantem_cumpridas(usuario):
    m = Materia.criar(usuario, "Física")
    aberta = Meta.criar(usuario, "Aberta", 5, materia_id=m.id)
    cumprida = Meta.criar(usuario, "Cumprida", 5, materia_id=m.id)
    cumprida.concluida = True
    db.session.commit()
    aberta_id, cumprida_id = aberta.id, cumprida.id
    m.excluir()
    assert db.session.get(Meta, aberta_id) is None
    assert db.session.get(Meta, cumprida_id).materia_id is None
