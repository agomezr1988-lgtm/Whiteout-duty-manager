from typing import Dict, List, Optional

from .event_model import Event, event_to_dict, event_from_dict
from .storage import load_events, save_events


class EventManager:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.events: Dict[str, Event] = {}
        self.load()

    # -------------------------
    # LOAD
    # -------------------------
    def load(self):
        """Loads all events for this server from storage."""
        data = load_events(self.guild_id)

        self.events = {
            event_id: event_from_dict(event_data)
            for event_id, event_data in data.items()
        }

    def save(self):
        """Saves all events for this server."""
        save_events(self.guild_id, {
            event_id: event_to_dict(event)
            for event_id, event in self.events.items()
        })

    # -------------------------
    # CRUD
    # -------------------------
    def add_event(self, event: Event):
        self.events[event.id] = event
        self.save()

    def update_event(self, event: Event):
        self.events[event.id] = event
        self.save()

    def remove_event(self, event_id: str) -> bool:
        if event_id not in self.events:
            return False

        del self.events[event_id]
        self.save()
        return True

    # -------------------------
    # QUERIES
    # -------------------------
    def get_event(self, event_id: str) -> Optional[Event]:
        return self.events.get(event_id)

    def get_all_events(self) -> List[Event]:
        def sort_key(e):
            if e.daily:
                category = 0
            elif e.weekday is not None:
                category = 1
            else:
                category = 2
            return (category, e.weekday if e.weekday is not None else 0, e.time)

        return sorted(self.events.values(), key=sort_key)

    def get_today_events(self, weekday: int) -> List[Event]:
        return [
            event
            for event in self.events.values()
            if event.active and event.weekday == weekday
        ]

    def get_events_by_day(self, weekday: int) -> List[Event]:
        return sorted(
            [
                event
                for event in self.events.values()
                if event.weekday == weekday
            ],
            key=lambda e: e.time
        )

    def event_exists(self, event_id: str) -> bool:
        return event_id in self.events

    def clear(self):
        self.events.clear()
        self.save()
