"""
Connecteur événements – OpenAgenda v2.
Recherche les événements dans un rayon de ~30 km autour de Saintes-Maries-de-la-Mer.
"""

from datetime import date, timedelta

import httpx

OPENAGENDA_URL = "https://api.openagenda.com/v2/events"

# Bounding box ~30 km autour de Saintes-Maries-de-la-Mer (43.4527, 4.4282)
_BBOX = {
    "geo[northEast][lat]": 43.75,
    "geo[northEast][lng]": 4.73,
    "geo[southWest][lat]": 43.15,
    "geo[southWest][lng]": 4.13,
}


def fetch_events(api_key: str, days: int = 7) -> list[dict]:
    """
    Retourne la liste des événements OpenAgenda pour les `days` prochains jours.
    Retourne [] en cas d'erreur pour ne pas bloquer le scoring.
    """
    if not api_key:
        return []

    today = date.today()
    end = today + timedelta(days=days - 1)

    params = {
        "key": api_key,
        "longdescription": 0,
        "size": 100,
        "timings[gte]": today.isoformat(),
        "timings[lte]": end.isoformat(),
        **_BBOX,
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(OPENAGENDA_URL, params=params)
            resp.raise_for_status()
        return resp.json().get("events", [])
    except Exception:
        return []


def compute_event_score(target: date, events: list[dict]) -> float:
    """
    Compte les événements actifs le jour `target` et retourne un score 0-100.
    Barème : 0 → 10, 1 → 30, 2 → 50, 3 → 65, 4 → 78, 5+ → 90.
    """
    target_str = target.isoformat()
    count = 0

    for event in events:
        for timing in event.get("timings", []):
            start = (timing.get("begin") or "")[:10]
            end = (timing.get("end") or "")[:10]
            if start and end and start <= target_str <= end:
                count += 1
                break  # on compte l'événement une seule fois

    scores = [10.0, 30.0, 50.0, 65.0, 78.0, 90.0]
    return scores[min(count, len(scores) - 1)]
