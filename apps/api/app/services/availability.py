"""
Disponibilités hébergements – heuristique basée sur :
  - Saison
  - Week-end
  - Vacances scolaires françaises Zone B (Académie d'Aix-Marseille)

Source vacances : data.education.gouv.fr (open data, sans clé API).
"""

from datetime import date
from functools import lru_cache

import httpx

HOLIDAYS_URL = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets"
    "/fr-en-calendrier-scolaire/records"
)

# Saintes-Maries-de-la-Mer → Bouches-du-Rhône → Académie d'Aix-Marseille → Zone B
ZONE = "Zone B"


@lru_cache(maxsize=1)
def _fetch_holidays() -> list[tuple[date, date]]:
    """Retourne la liste de (start, end) des vacances scolaires Zone B."""
    params = {
        "where": f'zone="{ZONE}"',
        "select": "start_date,end_date",
        "limit": 100,
    }
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(HOLIDAYS_URL, params=params)
            resp.raise_for_status()
        records = resp.json().get("results", [])
        periods = []
        for r in records:
            if r.get("start_date") and r.get("end_date"):
                start = date.fromisoformat(r["start_date"][:10])
                end = date.fromisoformat(r["end_date"][:10])
                periods.append((start, end))
        return periods
    except Exception:
        return []


def _is_school_holiday(target: date) -> bool:
    for start, end in _fetch_holidays():
        if start <= target <= end:
            return True
    return False


def compute_availability_score(target: date) -> float:
    """Score d'occupation estimé (0-100)."""
    score = 30.0

    # Saison – Saintes-Maries est très saisonnière
    if target.month in (7, 8):
        score += 50
    elif target.month == 6:
        score += 30
    elif target.month == 9:
        score += 20
    elif target.month in (4, 5):
        score += 12
    elif target.month in (10, 3):
        score += 5

    # Week-end
    if target.weekday() >= 5:
        score += 12

    # Vacances scolaires
    if _is_school_holiday(target):
        score += 18

    return min(100.0, round(score, 1))
