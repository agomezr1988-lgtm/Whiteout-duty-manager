from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Availability:
    """
    Representa la disponibilidad de un usuario para un evento.

    Si 'date' es None, la disponibilidad es RECURRENTE: se aplica
    todas las semanas al día de la semana del evento, hasta que el
    usuario se quite. Solo aplica a eventos con día fijo.

    Si 'date' tiene un valor ('YYYY-MM-DD'), la disponibilidad es
    para ESA fecha concreta únicamente (obligatorio en eventos de
    fecha variable).

    'task' es la tarea concreta dentro del evento (ej. "Battle
    coordination"), o None si el evento no tiene tareas definidas
    o el usuario se apunta de forma general.
    """

    event_id: str
    user_id: str
    user_name: str
    rank: str = ""                 # R4 / R5
    date: Optional[str] = None
    task: Optional[str] = None


def availability_to_dict(a: Availability) -> dict:
    return asdict(a)


def availability_from_dict(data: dict) -> Availability:
    data.setdefault("task", None)
    data.setdefault("rank", data.pop("role", ""))
    return Availability(**data)
