import json
import os
from datetime import date, timedelta
from typing import Optional

DATA_FILE = "data/cycle.json"


def _ensure_file():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"svs_battle_date": None}, f, indent=4)


def set_svs_battle_date(d: date):
    _ensure_file()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"svs_battle_date": d.isoformat()}, f, indent=4)


def get_svs_battle_date() -> Optional[date]:
    _ensure_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data.get("svs_battle_date"):
        return None

    return date.fromisoformat(data["svs_battle_date"])


def compute_cycle(anchor: date) -> dict:
    """
    Calcula todas las fechas del ciclo mensual a partir de la fecha
    de SvS Battle (que debe caer en Sábado).

    Devuelve un diccionario {nombre_evento: [fechas...]}.
    """

    monday_w0 = anchor - timedelta(days=anchor.weekday())  # Lunes de la semana de SvS Battle
    monday_w1 = monday_w0 + timedelta(days=7)              # Semana siguiente
    monday_w2 = monday_w0 + timedelta(days=14)              # Dos semanas después

    return {
        "SvS Preparation Phase": [monday_w0 + timedelta(days=i) for i in range(6)],   # Lun-Sáb
        "SvS Battle": [anchor],
        "Alliance Mobilization": [monday_w1 + timedelta(days=i) for i in range(6)],   # Lun-Sáb
        "King of Icefield (KoI)": [monday_w2 + timedelta(days=i) for i in range(6)],  # Lun-Sáb
        "Sunfire Castle (Normal)": [monday_w2 + timedelta(days=5)],                   # Sábado semana+2
        "Crazy Joe": [monday_w2 + timedelta(days=1), monday_w2 + timedelta(days=3)],  # Martes y Jueves
        "BIA": [monday_w2 + timedelta(days=4), monday_w2 + timedelta(days=5)],        # Viernes y Sábado
    }
