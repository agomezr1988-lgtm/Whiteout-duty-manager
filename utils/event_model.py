from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class Event:
    """
    Modelo de un evento semanal.
    """

    # Identificación
    id: str
    name: str
    description: str

    # Programación
    weekday: int              # 0=Lunes ... 6=Domingo
    time: str                 # HH:MM (UTC)

    # Gestión
    assigned_roles: List[str] = field(default_factory=list)
    duration: Optional[int] = None
    active: bool = True

    # Recordatorios (minutos antes del evento)
    reminders: List[int] = field(default_factory=lambda: [60, 30, 15, 5])

    # Evita enviar el mismo aviso varias veces
    last_notified: str = ""

    # Información opcional para futuras versiones
    category: str = "General"
    notes: str = ""

    def is_today(self) -> bool:
        return datetime.utcnow().weekday() == self.weekday


def event_to_dict(event: Event) -> dict:
    """Convierte un Event en un diccionario serializable."""
    return asdict(event)


def event_from_dict(data: dict) -> Event:
    """
    Reconstruye un Event desde un diccionario.

    Añade automáticamente los nuevos campos cuando
    se cargan eventos creados con versiones antiguas.
    """

    defaults = {
        "assigned_roles": [],
        "duration": None,
        "active": True,
        "reminders": [60, 30, 15, 5],
        "last_notified": "",
        "category": "General",
        "notes": "",
    }

    for key, value in defaults.items():
        data.setdefault(key, value)

    return Event(**data)
