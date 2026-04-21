"""
Scoring V3 – données réelles.

Sources :
  - Météo        : Open-Meteo (sans clé)
  - Disponibilités : vacances scolaires Zone B + saison + week-end
  - Événements   : OpenAgenda (clé OPENAGENDA_KEY)
  - Prix         : heuristique saisonnière (pas d'API publique gratuite)
"""

from datetime import date, timedelta
from app.services.availability import _easter, _french_public_holidays, _is_easter_weekend, _zones_on_holiday

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.affluence import AffluenceScore
from app.services.availability import compute_availability_score
from app.services.events_fetcher import compute_event_score, fetch_events
from app.services.booking import compute_booking_scores
from app.services.weather import fetch_weather_scores

def score_to_level(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def compute_global_score(avail: float, price: float, event: float,
                         weather: float, target: date) -> float:
    """
    Calcule le score global à partir des 4 sous-scores.

    Logique :
      1. L'occupation fixe un score de base (signal le plus fort).
      2. La météo, le prix et les événements modulent le score
         à la hausse ou à la baisse autour de cette base.
      3. Le week-end ajoute un bonus (plus de visiteurs à la journée).
    """
    # --- Score de base selon l'occupation ---
    if avail >= 95:
        base = 82
    elif avail >= 85:
        base = 72
    elif avail >= 70:
        base = 58
    elif avail >= 50:
        base = 42
    elif avail >= 30:
        base = 28
    else:
        base = 15

    # --- Modificateurs (chacun entre -10 et +10 environ) ---

    # Météo : beau temps = plus de monde, mauvais = moins
    # Poids renforcé : la météo est LE déclencheur d'une journée plage
    weather_mod = (weather - 50) / 3.3  # 0→-15, 50→0, 100→+15

    # Prix : prix élevés = forte demande
    price_mod = (price - 50) / 10  # 0→-5, 50→0, 100→+5

    # Événements : attirent du monde
    event_mod = event / 10  # 0→0, 30→+3, 100→+10

    # Week-end : plus de monde (visiteurs journée + week-endeurs)
    weekend_mod = 5 if target.weekday() >= 5 else 0

    score = base + weather_mod + price_mod + event_mod + weekend_mod
    return round(min(100.0, max(0.0, score)), 1)


def _compute_price_score(target: date) -> float:
    """Heuristique prix – utilisé en fallback si pas de données Booking."""
    score = 40.0
    # Saison
    if target.month in (7, 8):
        score += 30
    elif target.month == 6:
        score += 18
    elif target.month == 9:
        score += 10
    elif target.month in (4, 5):
        score += 8
    # Week-end
    if target.weekday() >= 5:
        score += 10
    # Pâques = prix au plus haut hors saison
    if _is_easter_weekend(target):
        score += 20
    elif target in _french_public_holidays(target.year):
        score += 12
    # Vacances scolaires : les prix montent avec le nombre de zones en vacances
    zones = _zones_on_holiday(target)
    if zones >= 2:
        score += 15
    elif zones == 1:
        score += 8
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
        events = fetch_events(settings.datatourisme_key, days=7)
    except Exception:
        events = []

    # 3. Calcul + upsert pour chaque jour
    for delta in range(7):
        target = today + timedelta(days=delta)
        date_str = target.isoformat()

        # Booking.com : vraies données si disponibles, sinon heuristique
        booking_avail, booking_price = compute_booking_scores(target)

        avail = booking_avail if booking_avail > 0 else compute_availability_score(target)
        price = booking_price if booking_price > 0 else _compute_price_score(target)
        event = compute_event_score(target, events)
        # Météo : défaut à 60 (plutôt neutre-positif) si pas de données
        weather = weather_map.get(date_str, 60.0)

        global_score = compute_global_score(avail, price, event, weather, target)
        # Confiance plus haute si on a des données Booking réelles
        if booking_avail > 0:
            confidence = 0.95 if delta <= 1 else 0.85 if delta <= 3 else 0.70
        else:
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
