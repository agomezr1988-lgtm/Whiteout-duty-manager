import json
import os
from typing import Any, Dict

import config


def _data_file(guild_id: int) -> str:
    return f"data/guilds/{guild_id}/config.json"


def _ensure_file(guild_id: int):
    os.makedirs(f"data/guilds/{guild_id}", exist_ok=True)

    path = _data_file(guild_id)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)


def _load(guild_id: int) -> Dict[str, Any]:
    _ensure_file(guild_id)
    with open(_data_file(guild_id), "r", encoding="utf-8") as f:
        return json.load(f)


def _save(guild_id: int, data: Dict[str, Any]):
    _ensure_file(guild_id)
    with open(_data_file(guild_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# Default values (from .env), used until a server customizes
# them via /management.
DEFAULTS = {
    "role_r4_name": lambda: config.ROLE_R4_NAME,
    "role_r5_name": lambda: config.ROLE_R5_NAME,
    "announcement_channel_id": lambda: config.ANNOUNCEMENT_CHANNEL_ID,
    "calendar_channel_id": lambda: config.CALENDAR_CHANNEL_ID,
}


def get(guild_id: int, key: str):
    data = _load(guild_id)
    if key in data and data[key] not in (None, ""):
        return data[key]
    return DEFAULTS[key]()


def set_value(guild_id: int, key: str, value):
    data = _load(guild_id)
    data[key] = value
    _save(guild_id, data)


def get_role_r4(guild_id: int) -> str:
    return get(guild_id, "role_r4_name")


def get_role_r5(guild_id: int) -> str:
    return get(guild_id, "role_r5_name")


def get_announcement_channel(guild_id: int) -> int:
    return get(guild_id, "announcement_channel_id")


def get_calendar_channel(guild_id: int) -> int:
    return get(guild_id, "calendar_channel_id")


def set_role_r4(guild_id: int, role_name: str):
    set_value(guild_id, "role_r4_name", role_name)


def set_role_r5(guild_id: int, role_name: str):
    set_value(guild_id, "role_r5_name", role_name)


def set_announcement_channel(guild_id: int, channel_id: int):
    set_value(guild_id, "announcement_channel_id", channel_id)


def set_calendar_channel(guild_id: int, channel_id: int):
    set_value(guild_id, "calendar_channel_id", channel_id)
