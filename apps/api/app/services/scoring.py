"""
Scoring V3 – données réelles.

Sources :
  - Météo        : Open-Meteo (sans clé)
  - Disponibilités : vacances scolaires Zone B + saison + week-end
  - Événements   : OpenAgenda (clé OPENAGENDA_KEY)
  - Prix         : heuristique saisonnière (pas d'API publique gratuite)
"""

from datetime import date, timedelta
from app.services.availability import _easter, _french_public_holidays, _is_easter_weekend

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.affluence import AffluenceScore
from app.services.availability import compute_availability_score
from app.services.events_fetcher import compute_event_score, fetch_events
from app.services.weather import fetch_weather_scores

WEIGHTS = {
    "availability": 0.35,
    "price": 0.25,
    "event": 0.20,
    "weather": 0.20,
}


def score_to_level(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _compute_price_score(target: date) -> float:
    """Heuristique prix – sera remplacé par une vraie source en V4."""
    score = 40.0
    if target.month in (7, 8):
        score += 30
    elif target.month == 6:
        score += 18
    elif target.month == 9:
        score += 10
    elif target.month in (4, 5):
        score += 8
    if target.weekday() >= 5:
        score += 10
    # Pâques = prix au plus haut hors saison
    if _is_easter_weekend(target):
        score += 20
    elif target in _french_public_holidays(target.year):
        score += 12
    return min(100.0, round(score, 1))


def refresh_scores(db: Session) -> None:
    """
    Récupère les données externes et met à jour les scores
    pour aujourd'hui + les 6 prochains jours.
    Appelé au démarrage de l'API et via POST /api/v1/refresh.
    """
    today = date.today()

    # 1. Météo (Open-Meteo)
    try:
        weather_map = fetch_weather_scores()
    except Exception:
        weather_map = {}

    # 2. Événements (OpenAgenda)
    try:
        events = fetch_events(settings.openagenda_key, days=7)
    except Exception:
        events = []

    # 3. Calcul + upsert pour chaque jour
    for delta in range(7):
        target = today + timedelta(days=delta)
        date_str = target.isoformat()

        avail = compute_availability_score(target)
        price = _compute_price_score(target)
        event = compute_event_score(target, events)
        weather = weather_map.get(date_str, 50.0)

        global_score = round(
            avail * WEIGHTS["availability"]
            + price * WEIGHTS["price"]
            + event * WEIGHTS["event"]
            + weather * WEIGHTS["weather"],
            1,
        )
        confidence = 0.85 if delta <= 1 else 0.70 if delta <= 3 else 0.55

        existing = (
            db.query(AffluenceScore)
            .filter(AffluenceScore.score_date == target)
            .first()
        )
        if existing:
            existing.global_score = global_score
            existing.level = score_to_level(global_score)
            existing.availability_score = avail
            existing.price_score = price
            existing.event_score = event
            existing.weather_score = weather
            existing.confidence_score = confidence
        else:
            db.add(
                AffluenceScore(
                    score_date=target,
                    zone="saintes-maries-de-la-mer",
                    global_score=global_score,
                    level=score_to_level(global_score),
                    availability_score=avail,
                    price_score=price,
                    event_score=event,
                    weather_score=weather,
                    confidence_score=confidence,
                )
            )

    db.commit()


# Alias conservé pour la compatibilité avec main.py
def seed_scores(db: Session) -> None:
    refresh_scores(db)
