import json
import os
from datetime import date, timedelta
from typing import Optional


def _data_file(guild_id: int) -> str:
    return f"data/guilds/{guild_id}/cycle.json"


def _ensure_file(guild_id: int):
    os.makedirs(f"data/guilds/{guild_id}", exist_ok=True)

    path = _data_file(guild_id)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"svs_battle_date": None}, f, indent=4)


def set_svs_battle_date(guild_id: int, d: date):
    _ensure_file(guild_id)
    with open(_data_file(guild_id), "w", encoding="utf-8") as f:
        json.dump({"svs_battle_date": d.isoformat()}, f, indent=4)


def get_svs_battle_date(guild_id: int) -> Optional[date]:
    _ensure_file(guild_id)
    with open(_data_file(guild_id), "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data.get("svs_battle_date"):
        return None

    return date.fromisoformat(data["svs_battle_date"])


def compute_cycle(anchor: date) -> dict:
    """
    Calculates all the monthly cycle dates based on the SvS Battle
    date (which must fall on a Saturday).

    Returns a dict {event_name: [dates...]}.
    """

    monday_w0 = anchor - timedelta(days=anchor.weekday())  # Monday of SvS Battle's week
    monday_w1 = monday_w0 + timedelta(days=7)              # Following week
    monday_w2 = monday_w0 + timedelta(days=14)              # Two weeks later

    return {
        "SvS Preparation Phase": [monday_w0 + timedelta(days=i) for i in range(6)],   # Mon-Sat
        "SvS Battle": [anchor],
        "Alliance Mobilization": [monday_w1 + timedelta(days=i) for i in range(6)],   # Mon-Sat
        "King of Icefield (KoI)": [monday_w2 + timedelta(days=i) for i in range(6)],  # Mon-Sat
        "Sunfire Castle (Normal)": [monday_w2 + timedelta(days=5)],                   # Saturday, week+2
        "Crazy Joe": [monday_w2 + timedelta(days=1), monday_w2 + timedelta(days=3)],  # Tuesday and Thursday
        "BIA": [monday_w2 + timedelta(days=4), monday_w2 + timedelta(days=5)],        # Friday and Saturday
    }
