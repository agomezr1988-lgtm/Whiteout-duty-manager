import logging

logger = logging.getLogger(__name__)


def load_seed_events(event_manager) -> tuple[list, list]:
    """
    Loads the events defined in data/seed_events.py into the given
    event_manager. Only ADDS the ones that don't exist yet (by id);
    never overwrites one that's already created.

    Returns (created, already_existed): lists of IDs.
    """

    try:
        from data.seed_events import SEED_EVENTS
    except ImportError:
        logger.warning("data/seed_events.py not found, skipping automatic loading.")
        return [], []

    from utils.event_model import Event

    created = []
    already_existed = []

    for data in SEED_EVENTS:
        if event_manager.event_exists(data["id"]):
            already_existed.append(data["id"])
            continue

        event = Event(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            weekday=data.get("weekday"),
            daily=data.get("daily", False),
            time=data.get("time", "00:00"),
            tasks=data.get("tasks", []),
            notes=data.get("notes", ""),
        )

        event_manager.add_event(event)
        created.append(data["id"])

    return created, already_existed
