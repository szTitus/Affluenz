"""
Connecteur événements – DATAtourisme (même clé que l'hébergement).
Recherche les fêtes et manifestations dans un rayon de 30 km autour de
Saintes-Maries-de-la-Mer.
"""

import logging
import time
from datetime import date, timedelta

import httpx

log = logging.getLogger(__name__)

DATATOURISME_URL = "https://api.datatourisme.fr/v1/catalog"
LAT = 43.4527
LON = 4.4282
# Rayon réduit à 15km pour rester centré sur Saintes-Maries, exclure Arles
_RADIUS = "15km"

# Cache simple 1h pour éviter des appels répétés
_cache: tuple[list[dict], float] = ([], 0.0)
_CACHE_TTL = 3600


def fetch_events(api_key: str, days: int = 7) -> list[dict]:
    """
    Retourne les événements DATAtourisme pour les `days` prochains jours.
    Retourne [] en cas d'erreur.
    """
    global _cache
    cached_events, ts = _cache
    if cached_events and (time.time() - ts) < _CACHE_TTL:
        return cached_events

    if not api_key:
        return []

    today = date.today()
    end = today + timedelta(days=days - 1)

    params = {
        "api_key": api_key,
        "geo_distance": f"{LAT},{LON},{_RADIUS}",
        "filters": 'type=="EntertainmentAndEvent" OR type=="Festival" OR type=="SocialEvent" OR type=="Concert"',
        "page_size": 100,
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(DATATOURISME_URL, params=params)
            resp.raise_for_status()
        data = resp.json()
        events = data.get("objects", [])
        log.info("DATAtourisme events: %d trouvés dans la zone", len(events))
        _cache = (events, time.time())
        return events
    except Exception as exc:
        log.warning("DATAtourisme events fetch failed: %s", exc)
        return cached_events


def _get_event_dates(event: dict) -> tuple[str, str]:
    """Extrait les dates de début et fin d'un événement DATAtourisme."""
    # Champ direct
    start = (event.get("startDate") or event.get("dateBegin") or "")[:10]
    end = (event.get("endDate") or event.get("dateEnd") or "")[:10]

    # Cherche dans les sous-champs si pas trouvé
    if not start:
        for timing in event.get("hasSchedule", []):
            start = (timing.get("startDate") or timing.get("startTime") or "")[:10]
            end = (timing.get("endDate") or timing.get("endTime") or "")[:10]
            if start:
                break

    # Fallback : lastUpdate comme date de référence
    if not start:
        last = event.get("lastUpdate") or event.get("lastUpdateDatatourisme") or ""
        start = last[:10]
        end = last[:10]

    return start, end


def compute_event_score(target: date, events: list[dict]) -> float:
    """
    Compte les événements actifs le jour `target` et retourne un score 0-100.
    Barème : 0 → 10, 1 → 30, 2 → 50, 3 → 65, 4 → 78, 5+ → 90.
    """
    if not events:
        return 10.0

    target_str = target.isoformat()
    count = 0

    for event in events:
        start, end = _get_event_dates(event)
        if not start:
            continue
        if not end:
            end = start
        if start <= target_str <= end:
            count += 1

    # Bonus si beaucoup d'événements dans la zone (indique une période active)
    total = len(events)
    if count == 0 and total >= 50:
        count = 1  # zone avec beaucoup d'événements permanents → score de base plus haut

    scores = [10.0, 30.0, 50.0, 65.0, 78.0, 90.0]
    return scores[min(count, len(scores) - 1)]
