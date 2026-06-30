from datetime import datetime, timezone


def now_utc() -> datetime:
    """Devuelve la fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


def parse_time_utc(time_str: str) -> tuple[int, int]:
    """
    Convierte una cadena HH:MM en (hora, minuto).
    """

    try:
        hour, minute = map(int, time_str.strip().split(":"))

        if not (0 <= hour <= 23):
            raise ValueError

        if not (0 <= minute <= 59):
            raise ValueError

        return hour, minute

    except Exception:
        raise ValueError(
            f"Formato de hora inválido: '{time_str}'. Debe ser HH:MM."
        )
