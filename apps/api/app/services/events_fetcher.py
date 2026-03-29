"""
Connecteur événements – OpenAgenda v2.
Recherche les événements dans un rayon de 30 km autour de Saintes-Maries-de-la-Mer.
"""

import logging
from datetime import date, timedelta

import httpx

log = logging.getLogger(__name__)

OPENAGENDA_URL = "https://api.openagenda.com/v2/events"
LAT = 43.4527
LON = 4.4282


def fetch_events(api_key: str, days: int = 7) -> list[dict]:
    """
    Retourne la liste des événements OpenAgenda pour les `days` prochains jours.
    Retourne [] en cas d'erreur pour ne pas bloquer le scoring.
    """
    if not api_key:
        return []

    today = date.today()
    end = today + timedelta(days=days - 1)

    # OpenAgenda v2 : filtre géographique via relative[lat/lng/distance]
    params = {
        "key": api_key,
        "longdescription": 0,
        "size": 100,
        "relative[lat]": LAT,
        "relative[lng]": LON,
        "relative[d]": 30,          # rayon en km
        "timings[gte]": today.isoformat(),
        "timings[lte]": end.isoformat(),
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(OPENAGENDA_URL, params=params)
            resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])
        log.info("OpenAgenda: %d événements trouvés", len(events))
        return events
    except Exception as exc:
        log.warning("OpenAgenda fetch failed: %s", exc)
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
