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


def hoje_local():
    """Data de hoje no fuso de Brasília."""
    return datetime.now(FUSO_LOCAL).date()


def fim_do_dia_local(dia):
    """Instante em que o dia `dia` (date) termina em Brasília, em UTC sem fuso."""
    meia_noite = datetime(dia.year, dia.month, dia.day, tzinfo=FUSO_LOCAL) + timedelta(days=1)
    return meia_noite.astimezone(timezone.utc).replace(tzinfo=None)
