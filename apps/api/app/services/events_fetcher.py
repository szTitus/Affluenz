"""
Connecteur événements – DATAtourisme + événements annuels connus.

Deux sources combinées :
1. DATAtourisme : compte les événements référencés dans la zone (proxy d'activité)
2. Calendrier annuel hardcodé : grands événements de Saintes-Maries-de-la-Mer
"""

import logging
import time
from datetime import date, timedelta

import httpx

log = logging.getLogger(__name__)

DATATOURISME_URL = "https://api.datatourisme.fr/v1/catalog"
LAT = 43.4527
LON = 4.4282

# Cache simple 1h
_cache: tuple[int, float] = (0, 0.0)
_CACHE_TTL = 3600

# Événements annuels connus à Saintes-Maries-de-la-Mer
# Format : (mois, jour_debut, mois, jour_fin, impact 1-5)
_ANNUAL_EVENTS: list[tuple[int, int, int, int, int]] = [
    (5, 24, 5, 26, 5),   # Pèlerinage des Gitans (24-25 mai) → énorme
    (5, 1,  5, 1,  3),   # Fête du travail / début saison
    (7, 14, 7, 14, 3),   # Fête nationale
    (8, 15, 8, 15, 3),   # Assomption
    (7, 1,  8, 31, 2),   # Saison estivale (boost continu)
    (10, 17, 10, 20, 4), # Pèlerinage d'octobre (3ème dimanche)
]


def _annual_event_count(target: date) -> int:
    """Retourne le nombre d'événements annuels actifs ce jour-là."""
    count = 0
    for m_start, d_start, m_end, d_end, _ in _ANNUAL_EVENTS:
        start = date(target.year, m_start, d_start)
        end = date(target.year, m_end, d_end)
        if start <= target <= end:
            count += 1
    return count


def _annual_event_impact(target: date) -> int:
    """Retourne l'impact max des événements annuels ce jour-là (0-5)."""
    impact = 0
    for m_start, d_start, m_end, d_end, evt_impact in _ANNUAL_EVENTS:
        start = date(target.year, m_start, d_start)
        end = date(target.year, m_end, d_end)
        if start <= target <= end:
            impact = max(impact, evt_impact)
    return impact


def fetch_events(api_key: str, days: int = 7) -> list[dict]:
    """
    Retourne le nombre d'événements DATAtourisme dans la zone (cache 1h).
    On retourne une liste de dicts fictifs de longueur = total pour
    rester compatible avec compute_event_score.
    """
    global _cache
    cached_count, ts = _cache
    if cached_count > 0 and (time.time() - ts) < _CACHE_TTL:
        return [{}] * cached_count

    if not api_key:
        return []

    params = {
        "api_key": api_key,
        "geo_distance": f"{LAT},{LON},30km",
        "filters": 'type=="EntertainmentAndEvent" OR type=="Festival" OR type=="SocialEvent"',
        "page_size": 1,  # on veut juste le total
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(DATATOURISME_URL, params=params)
            resp.raise_for_status()
        total = resp.json().get("meta", {}).get("total", 0)
        log.info("DATAtourisme: %d événements dans la zone", total)
        _cache = (total, time.time())
        return [{}] * total
    except Exception as exc:
        log.warning("DATAtourisme events fetch failed: %s", exc)
        return [{}] * cached_count


def compute_event_score(target: date, events: list[dict]) -> float:
    """
    Score événements 0-100 basé sur :
    - Les événements annuels connus (Pèlerinage, etc.)
    - La densité d'événements DATAtourisme dans la zone
    """
    # 1. Événements annuels connus
    impact = _annual_event_impact(target)
    if impact >= 5:
        return 95.0
    if impact >= 4:
        return 80.0
    if impact >= 3:
        return 65.0
    if impact >= 2:
        return 50.0
    if impact >= 1:
        return 40.0

    # 2. Densité DATAtourisme comme proxy d'activité de fond
    total = len(events)
    if total >= 50:
        return 30.0  # zone très active
    if total >= 10:
        return 20.0
    return 10.0
