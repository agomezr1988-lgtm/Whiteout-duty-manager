import json
import os
from typing import List, Optional

from .availability_model import (
    Availability,
    availability_to_dict,
    availability_from_dict,
)

DATA_FILE = "data/availability.json"


def _ensure_file():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)


def _load() -> List[dict]:
    _ensure_file()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: List[dict]):
    _ensure_file()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class AvailabilityManager:
    def __init__(self):
        self.entries: List[Availability] = []
        self.load()

    # -------------------------
    # CARGA / GUARDADO
    # -------------------------
    def load(self):
        self.entries = [availability_from_dict(d) for d in _load()]

    def save(self):
        _save([availability_to_dict(a) for a in self.entries])

    # -------------------------
    # ESCRITURA
    # -------------------------
    def set_available(
        self,
        event_id: str,
        user_id: str,
        user_name: str,
        role: str = "",
        date: Optional[str] = None,
    ):
        """Apunta a un usuario. Si ya estaba apuntado (mismo evento,
        usuario y tipo de fecha), actualiza la entrada existente."""

        self.entries = [
            a for a in self.entries
            if not (
                a.event_id == event_id
                and a.user_id == user_id
                and a.date == date
            )
        ]

        self.entries.append(
            Availability(
                event_id=event_id,
                user_id=user_id,
                user_name=user_name,
                role=role,
                date=date,
            )
        )

        self.save()

    def remove_available(
        self,
        event_id: str,
        user_id: str,
        date: Optional[str] = None,
    ) -> bool:
        """Quita a un usuario. Devuelve True si habÃ­a algo que quitar."""

        before = len(self.entries)

        self.entries = [
            a for a in self.entries
            if not (
                a.event_id == event_id
                and a.user_id == user_id
                and a.date == date
            )
        ]

        changed = len(self.entries) != before

        if changed:
            self.save()

        return changed

    # -------------------------
    # CONSULTAS
    # -------------------------
    def get_for_event(
        self,
        event_id: str,
        date: Optional[str] = None,
    ) -> List[Availability]:
        """Devuelve la disponibilidad recurrente de un evento, mÃ¡s la
        de una fecha concreta si se indica."""

        result = [
            a for a in self.entries
            if a.event_id == event_id and a.date is None
        ]

        if date:
            result += [
                a for a in self.entries
                if a.event_id == event_id and a.date == date
            ]

        return result

    def clear_event(self, event_id: str):
        self.entries = [a for a in self.entries if a.event_id != event_id]
        self.save()
