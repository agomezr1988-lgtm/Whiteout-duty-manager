import json
import os
from typing import List, Optional

from .availability_model import (
    Availability,
    availability_to_dict,
    availability_from_dict,
)


def _data_file(guild_id: int) -> str:
    return f"data/guilds/{guild_id}/availability.json"


def _ensure_file(guild_id: int):
    os.makedirs(f"data/guilds/{guild_id}", exist_ok=True)

    path = _data_file(guild_id)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)


def _load(guild_id: int) -> List[dict]:
    _ensure_file(guild_id)

    with open(_data_file(guild_id), "r", encoding="utf-8") as f:
        return json.load(f)


def _save(guild_id: int, data: List[dict]):
    _ensure_file(guild_id)

    with open(_data_file(guild_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class AvailabilityManager:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.entries: List[Availability] = []
        self.load()

    # -------------------------
    # LOAD / SAVE
    # -------------------------
    def load(self):
        self.entries = [availability_from_dict(d) for d in _load(self.guild_id)]

    def save(self):
        _save(self.guild_id, [availability_to_dict(a) for a in self.entries])

    # -------------------------
    # WRITES
    # -------------------------
    def set_available(
        self,
        event_id: str,
        user_id: str,
        user_name: str,
        rank: str = "",
        date: Optional[str] = None,
        task: Optional[str] = None,
    ):
        """Signs a user up. If already signed up (same event, user,
        date and task), updates the existing entry."""

        self.entries = [
            a for a in self.entries
            if not (
                a.event_id == event_id
                and a.user_id == user_id
                and a.date == date
                and a.task == task
            )
        ]

        self.entries.append(
            Availability(
                event_id=event_id,
                user_id=user_id,
                user_name=user_name,
                rank=rank,
                date=date,
                task=task,
            )
        )

        self.save()

    def remove_available(
        self,
        event_id: str,
        user_id: str,
        date: Optional[str] = None,
        task: Optional[str] = None,
    ) -> bool:
        """Removes a user. Returns True if there was something to remove."""

        before = len(self.entries)

        self.entries = [
            a for a in self.entries
            if not (
                a.event_id == event_id
                and a.user_id == user_id
                and a.date == date
                and a.task == task
            )
        ]

        changed = len(self.entries) != before

        if changed:
            self.save()

        return changed

    # -------------------------
    # QUERIES
    # -------------------------
    def get_for_event(
        self,
        event_id: str,
        date: Optional[str] = None,
    ) -> List[Availability]:
        """Returns the recurring availability of an event, plus that of
        a specific date if given (includes all tasks)."""

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

    def get_dated_for_event(self, event_id: str) -> List[Availability]:
        """Returns ALL signups with a specific date for an event (any
        date, not just one in particular). Used to list variable-date
        events in the calendar."""

        return [
            a for a in self.entries
            if a.event_id == event_id and a.date
        ]

    def has_any_signups(self, event_id: str) -> bool:
        """True if anyone is signed up for this event, regardless of
        date (recurring or specific)."""
        return any(a.event_id == event_id for a in self.entries)

    def count_signups(self, event_id: str) -> int:
        """Total number of signups (people x dates) for an event."""
        return sum(1 for a in self.entries if a.event_id == event_id)
