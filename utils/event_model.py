from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Event:
    """
    Representa un evento dentro del sistema semanal.
    """

    id: str
    name: str
    description: str

    # Día de la semana (0=Lunes ... 6=Domingo)
    weekday: int

    # Hora en formato 24h (ej: "20:00")
    time: str

    # Roles responsables (R4 / R5 / otros)
    assigned_roles: List[str] = field(default_factory=list)

    # Opcional: duración en minutos
    duration: Optional[int] = None

    # Estado del evento
    active: bool = True

    def is_today(self) -> bool:
        """Comprueba si el evento es hoy (lógica base)."""
        return datetime.utcnow().weekday() == self.weekday

Utils/event_manager.py

from typing import List, Dict
from .event_model import Event


class EventManager:
    """
    Maneja todos los eventos del sistema Whiteout Survival Bot 2.
    """

    def __init__(self):
        self.events: Dict[str, Event] = {}

    def add_event(self, event: Event):
        """Añadir evento nuevo"""
        self.events[event.id] = event

    def remove_event(self, event_id: str):
        """Eliminar evento"""
        if event_id in self.events:
            del self.events[event_id]

    def get_event(self, event_id: str):
        """Obtener evento específico"""
        return self.events.get(event_id)

    def get_all_events(self):
        """Lista todos los eventos"""
        return list(self.events.values())

    def get_today_events(self, weekday: int):
        """Eventos activos del día"""
        return [
            e for e in self.events.values()
            if e.weekday == weekday and e.active
        ]
