from typing import List, Dict
from .event_model import Event, event_to_dict, event_from_dict
from .storage import load_events, save_events


class EventManager:
    def __init__(self):
        self.events: Dict[str, Event] = {}
        self.load()

    # -------------------------
    # CARGA INICIAL
    # -------------------------
    def load(self):
        data = load_events()

        self.events = {
            eid: event_from_dict(edata)
            for eid, edata in data.items()
        }

    # -------------------------
    # GUARDAR TODO
    # -------------------------
    def _save(self):
        data = {
            eid: event_to_dict(event)
            for eid, event in self.events.items()
        }

        save_events(data)

    # -------------------------
    # OPERACIONES
    # -------------------------
    def add_event(self, event: Event):
        self.events[event.id] = event
        self._save()

    def remove_event(self, event_id: str):
        if event_id in self.events:
            del self.events[event_id]
            self._save()

    def get_event(self, event_id: str):
        return self.events.get(event_id)

    def get_all_events(self):
        return list(self.events.values())

    def get_today_events(self, weekday: int):
        return [
            e for e in self.events.values()
            if e.weekday == weekday and e.active
        ]
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Event:
    id: str
    name: str
    description: str
    weekday: int
    time: str

    assigned_roles: List[str] = field(default_factory=list)

    duration: Optional[int] = None
    active: bool = True

    # 🆕 NUEVO: recordatorios en minutos antes del evento
    reminders: List[int] = field(default_factory=lambda: [60, 10])

    # 🆕 NUEVO: evita spam de notificaciones
    last_notified: Optional[str] = None
