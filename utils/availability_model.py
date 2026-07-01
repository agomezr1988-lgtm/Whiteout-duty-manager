from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Availability:
    """
    Representa la disponibilidad de un usuario para un evento.

    Si 'date' es None, la disponibilidad es RECURRENTE: se aplica
    todas las semanas al día de la semana del evento, hasta que el
    usuario se quite.

    Si 'date' tiene un valor ('YYYY-MM-DD'), la disponibilidad es
    para ESA fecha concreta únicamente.
    """

    event_id: str
    user_id: str
    user_name: str
    role: str = ""
    date: Optional[str] = None


def availability_to_dict(a: Availability) -> dict:
    return asdict(a)


def availability_from_dict(data: dict) -> Availability:
    return Availability(**data)
