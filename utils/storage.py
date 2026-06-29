import json
import os
from typing import Dict, Any

DATA_FILE = "data/events.json"


def ensure_data_file():
    """Crea el archivo si no existe"""
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)


def load_events() -> Dict[str, Any]:
    """Carga eventos desde JSON"""
    ensure_data_file()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_events(events: Dict[str, Any]):
    """Guarda eventos en JSON"""
    ensure_data_file()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)
