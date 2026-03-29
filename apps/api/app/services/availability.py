"""
Disponibilités hébergements – heuristique basée sur :
  - Nombre réel de logements référencés (DATAtourisme, refresh 24h)
  - Saison
  - Week-end
  - Vacances scolaires françaises toutes zones (A, B, C)
  - Jours fériés français (Pâques, ponts, etc.)

Sources : data.education.gouv.fr + api.datatourisme.fr
"""

from datetime import date, timedelta
from functools import lru_cache

import httpx

from app.services.datatourisme import fetch_accommodation_count
from app.core.config import settings

_CAPACITY_REFERENCE = 200
HOLIDAYS_URL = (
    "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets"
    "/fr-en-calendrier-scolaire/records"
)


def _easter(year: int) -> date:
    """Calcule la date de Pâques (algorithme de Meeus)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(114 + h + l - 7 * m, 31)
    return date(year, month, day + 1)


def _french_public_holidays(year: int) -> set[date]:
    easter = _easter(year)
    return {
        date(year, 1, 1),    # Jour de l'an
        easter + timedelta(days=1),   # Lundi de Pâques
        date(year, 5, 1),    # Fête du travail
        date(year, 5, 8),    # Victoire 1945
        easter + timedelta(days=39),  # Ascension
        easter + timedelta(days=50),  # Lundi de Pentecôte
        date(year, 7, 14),   # Fête nationale
        date(year, 8, 15),   # Assomption
        date(year, 11, 1),   # Toussaint
        date(year, 11, 11),  # Armistice
        date(year, 12, 25),  # Noël
    }


def _is_easter_weekend(target: date) -> bool:
    easter = _easter(target.year)
    # Vendredi saint → lundi de Pâques
    return easter - timedelta(days=2) <= target <= easter + timedelta(days=1)


@lru_cache(maxsize=1)
def _fetch_holidays_all_zones() -> list[tuple[date, date]]:
    """Retourne les vacances scolaires des 3 zones (A, B, C)."""
    periods = []
    for zone in ("Zone A", "Zone B", "Zone C"):
        params = {
            "where": f'zone="{zone}"',
            "select": "start_date,end_date",
            "limit": 100,
        }
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(HOLIDAYS_URL, params=params)
                resp.raise_for_status()
            for r in resp.json().get("results", []):
                if r.get("start_date") and r.get("end_date"):
                    start = date.fromisoformat(r["start_date"][:10])
                    end = date.fromisoformat(r["end_date"][:10])
                    periods.append((start, end))
        except Exception:
            continue
    return periods


def _zones_on_holiday(target: date) -> int:
    """Retourne le nombre de zones scolaires en vacances ce jour-là (0-3)."""
    count = 0
    seen: set[tuple[date, date]] = set()
    for start, end in _fetch_holidays_all_zones():
        if (start, end) not in seen and start <= target <= end:
            seen.add((start, end))
            count += 1
    return min(count, 3)


def compute_availability_score(target: date) -> float:
    """Score d'occupation estimé (0-100). Plus c'est haut, plus c'est fréquenté."""
    score = 30.0

    # Calibrage via DATAtourisme
    if settings.datatourisme_key:
        count = fetch_accommodation_count(settings.datatourisme_key)
        if count >= _CAPACITY_REFERENCE:
            score += 5
        elif 0 < count < 50:
            score -= 5

    # Saison
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

    # Vacances scolaires : +8 par zone en vacances (max +24 si les 3 zones)
    zones = _zones_on_holiday(target)
    score += zones * 8

    holidays = _french_public_holidays(target.year)

    # Pâques : weekend exceptionnel pour Saintes-Maries
    if _is_easter_weekend(target):
        score += 25

    # Jour férié
    elif target in holidays:
        score += 18

    # Pont : veille ou lendemain d'un férié en semaine
    # (ex: férié mardi → lundi est un pont, férié jeudi → vendredi est un pont)
    else:
        tomorrow = target + timedelta(days=1)
        yesterday = target - timedelta(days=1)
        is_pont = (
            (target.weekday() == 0 and tomorrow in holidays)  # lundi avant férié mardi
            or (target.weekday() == 4 and yesterday in holidays)  # vendredi après férié jeudi
        )
        if is_pont:
            score += 12

    return min(100.0, round(score, 1))
