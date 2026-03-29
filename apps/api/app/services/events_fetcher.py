"""
Connecteur événements – DATAtourisme (gratuit, même clé que l'hébergement).
Recherche les fêtes et manifestations dans un rayon de 30 km autour de
Saintes-Maries-de-la-Mer.
"""

import logging
from datetime import date, timedelta

import httpx

log = logging.getLogger(__name__)

DATATOURISME_URL = "https://api.datatourisme.fr/v1/catalog"
LAT = 43.4527
LON = 4.4282


def fetch_events(api_key: str, days: int = 7) -> list[dict]:
    """
    Retourne les événements DATAtourisme pour les `days` prochains jours.
    Retourne [] en cas d'erreur.
    """
    if not api_key:
        return []

    today = date.today()
    end = today + timedelta(days=days - 1)

    params = {
        "api_key": api_key,
        "geo_distance": f"{LAT},{LON},30km",
        "filters": "@type=in=(schema:Event,schema:Festival,schema:SportsEvent,"
                   "schema:EntertainmentAndEvent,schema:MusicEvent,"
                   "schema:VisualArtsEvent,schema:TheaterEvent)",
        "dateBegin": today.isoformat(),
        "dateEnd": end.isoformat(),
        "page_size": 100,
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(DATATOURISME_URL, params=params)
            resp.raise_for_status()
        data = resp.json()
        events = data.get("data", data.get("results", []))
        log.info("DATAtourisme events: %d trouvés", len(events))
        return events
    except Exception as exc:
        log.warning("DATAtourisme events fetch failed: %s", exc)
        return []


def compute_event_score(target: date, events: list[dict]) -> float:
    """
    Compte les événements actifs le jour `target` et retourne un score 0-100.
    Barème : 0 → 10, 1 → 30, 2 → 50, 3 → 65, 4 → 78, 5+ → 90.
    """
    target_str = target.isoformat()
    count = 0

    for event in events:
        # Format DATAtourisme : dateBegin / dateEnd au niveau racine
        start = (event.get("dateBegin") or event.get("startDate") or "")[:10]
        end = (event.get("dateEnd") or event.get("endDate") or "")[:10]
        if start and end and start <= target_str <= end:
            count += 1
        elif start and start == target_str:
            count += 1

    scores = [10.0, 30.0, 50.0, 65.0, 78.0, 90.0]
    return scores[min(count, len(scores) - 1)]
