from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ErroValidacao(ValueError):
    """Dados inválidos informados pelo usuário (mensagem pronta para exibir)."""


try:
    FUSO_LOCAL = ZoneInfo("America/Sao_Paulo")
except ZoneInfoNotFoundError:  # Windows sem o pacote tzdata
    FUSO_LOCAL = timezone(timedelta(hours=-3))  # Brasil não tem horário de verão desde 2019


def agora():
    """Data/hora atual em UTC, sem fuso (como o banco armazena)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def inicio_do_dia_local():
    """Meia-noite de hoje no fuso de Brasília, convertida para UTC (sem fuso)."""
    meia_noite = datetime.now(FUSO_LOCAL).replace(hour=0, minute=0, second=0, microsecond=0)
    return meia_noite.astimezone(timezone.utc).replace(tzinfo=None)
