from datetime import datetime, timezone


class ErroValidacao(ValueError):
    """Dados inválidos informados pelo usuário (mensagem pronta para exibir)."""


def agora():
    """Data/hora atual em UTC, sem fuso (como o banco armazena)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
