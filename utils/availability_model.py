from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Availability:
    # Represents a user's availability for an event.

    # If 'date' is None, the availability is RECURRING: it applies
    # every week on the event's weekday, until the user removes it.
    # Only applies to events with a fixed weekday.

    # If 'date' has a value ('YYYY-MM-DD'), the availability is for
    # THAT specific date only (mandatory for variable-date events).

    # 'task' is the specific task within the event (e.g. "Battle
    # coordination"), or None if the event has no tasks defined or
    # the user is signing up generally.

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
