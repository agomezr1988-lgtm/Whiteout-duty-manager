import json
import os
from typing import Dict, Any


def _data_file(guild_id: int) -> str:
    return f"data/guilds/{guild_id}/events.json"


def ensure_data_file(guild_id: int):
    # Creates the server's file if it doesn't exist
    os.makedirs(f"data/guilds/{guild_id}", exist_ok=True)

    path = _data_file(guild_id)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)


def load_events(guild_id: int) -> Dict[str, Any]:
    # Loads events from the given server's JSON file
    ensure_data_file(guild_id)

    with open(_data_file(guild_id), "r", encoding="utf-8") as f:
        return json.load(f)


def save_events(guild_id: int, events: Dict[str, Any]):
    # Saves events to the given server's JSON file
    ensure_data_file(guild_id)

    with open(_data_file(guild_id), "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)
