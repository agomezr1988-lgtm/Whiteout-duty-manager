from datetime import datetime, timezone, date, timedelta


def now_utc() -> datetime:
    """Returns the current date and time in UTC."""
    return datetime.now(timezone.utc)


def parse_time_utc(time_str: str) -> tuple[int, int]:
    """
    Converts an HH:MM string into (hour, minute).
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
            f"Invalid time format: '{time_str}'. Must be HH:MM."
        )


def get_week_dates(reference: date = None) -> dict:
    """
    Returns a dict {weekday(0-6): date} for the current week
    (Monday-Sunday), based on 'reference' (or today in UTC if
    not given).
    """
    if reference is None:
        reference = now_utc().date()

    monday = reference - timedelta(days=reference.weekday())

    return {i: monday + timedelta(days=i) for i in range(7)}


def parse_date_ddmmyyyy(text: str) -> str:
    """
    Converts 'DD/MM' or 'DD/MM/YYYY' to ISO format 'YYYY-MM-DD'.

    If no year is given, the current year is assumed; if that date
    has already passed this year, next year is assumed instead
    (so '05/01' in December points to next January, not the past).
    """

    parts = text.strip().split("/")

    if len(parts) not in (2, 3):
        raise ValueError(
            "Invalid date format. Use DD/MM or DD/MM/YYYY."
        )

    try:
        day = int(parts[0])
        month = int(parts[1])
    except ValueError:
        raise ValueError(
            "Invalid date format. Use DD/MM or DD/MM/YYYY."
        )

    today = now_utc().date()
    year = int(parts[2]) if len(parts) == 3 else today.year

    try:
        parsed = date(year, month, day)
    except ValueError:
        raise ValueError(f"'{text}' is not a valid date.")

    if len(parts) == 2 and parsed < today:
        parsed = date(year + 1, month, day)

    return parsed.isoformat()
