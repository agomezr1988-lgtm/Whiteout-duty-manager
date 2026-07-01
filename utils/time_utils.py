from datetime import datetime, timezone, date, timedelta


def now_utc() -> datetime:
    """Devuelve la fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


def get_week_dates(reference: date = None) -> dict:
    """
    Devuelve un diccionario {weekday(0-6): date} con las fechas
    de la semana actual (Lunes-Domingo), en base a 'reference'
    (o a hoy en UTC si no se indica).
    """
    if reference is None:
        reference = now_utc().date()

    monday = reference - timedelta(days=reference.weekday())

    return {i: monday + timedelta(days=i) for i in range(7)}


def parse_date_ddmmyyyy(text: str) -> str:
    """
    Convierte 'DD/MM' o 'DD/MM/AAAA' a formato ISO 'YYYY-MM-DD'.

    Si no se indica año, se asume el año actual; si esa fecha ya
    pasó esta semana/año, se asume el año siguiente.
    """

    parts = text.strip().split("/")

    if len(parts) not in (2, 3):
        raise ValueError(
            "Formato de fecha inválido. Usa DD/MM o DD/MM/AAAA."
        )

    try:
        day = int(parts[0])
        month = int(parts[1])
    except ValueError:
        raise ValueError(
            "Formato de fecha inválido. Usa DD/MM o DD/MM/AAAA."
        )

    today = now_utc().date()
    year = int(parts[2]) if len(parts) == 3 else today.year

    try:
        parsed = date(year, month, day)
    except ValueError:
        raise ValueError(f"La fecha '{text}' no es válida.")

    if len(parts) == 2 and parsed < today:
        parsed = date(year + 1, month, day)

    return parsed.isoformat()


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
