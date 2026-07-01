from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class Event:
    """
    Modelo de un evento.
    """

    # Identificación
    id: str
    name: str
    description: str
    time: str                       # HH:MM (UTC)

    # weekday=None significa evento de FECHA VARIABLE (no semanal fijo,
    # ej. SvS): solo se puede apuntar gente a fechas concretas, no de
    # forma recurrente.
    weekday: Optional[int] = None   # 0=Lunes ... 6=Domingo, o None

    # Tareas internas del evento a las que la gente se apunta
    # individualmente (ej: "Battle coordination", "Rally"...)
    tasks: List[str] = field(default_factory=list)

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
        if self.weekday is None:
            return False
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
        "tasks": [],
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
