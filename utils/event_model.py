from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class Event:
    """
    Modelo de un evento semanal.
    """

    id: str
    name: str
    description: str
    weekday: int              # 0=Lunes ... 6=Domingo
    time: str                 # "20:00"
    assigned_roles: List[str] = field(default_factory=list)
    duration: Optional[int] = None
    active: bool = True

    def is_today(self) -> bool:
        return datetime.utcnow().weekday() == self.weekday


def event_to_dict(event: Event) -> dict:
    """
    Convierte un Event en un diccionario serializable.
    """
    return asdict(event)


def event_from_dict(data: dict) -> Event:
    """
    Reconstruye un Event desde un diccionario.
    """
    return Event(**data)
