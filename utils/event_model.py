from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class Event:
    """
    Event model.
    """

    # Identification
    id: str
    name: str
    description: str
    time: str                       # HH:MM (UTC)

    # weekday=None means a VARIABLE-DATE event (not a fixed weekly
    # day, e.g. SvS): people can only sign up for specific dates,
    # not recurringly. EXCEPTION: if daily=True, the event happens
    # every day and DOES support recurring signup.
    weekday: Optional[int] = None   # 0=Monday ... 6=Sunday, or None
    daily: bool = False             # True = repeats every day

    # Internal tasks within the event that people can individually
    # sign up for (e.g. "Battle coordination", "Rally"...)
    tasks: List[str] = field(default_factory=list)

    # Management
    assigned_roles: List[str] = field(default_factory=list)
    duration: Optional[int] = None
    active: bool = True

    # Reminders (minutes before the event)
    reminders: List[int] = field(default_factory=lambda: [60, 30, 15, 5])

    # Prevents sending the same notification multiple times
    last_notified: str = ""

    # Optional info for future versions
    category: str = "General"
    notes: str = ""

    def is_today(self) -> bool:
        if self.daily:
            return True
        if self.weekday is None:
            return False
        return datetime.utcnow().weekday() == self.weekday


def event_to_dict(event: Event) -> dict:
    """Converts an Event into a serializable dict."""
    return asdict(event)


def event_from_dict(data: dict) -> Event:
    """
    Rebuilds an Event from a dict.

    Automatically fills in new fields when loading events created
    with older versions.
    """

    defaults = {
        "daily": False,
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
