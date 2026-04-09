"""
Connecteur Booking.com via RapidAPI (tipsters).
Récupère les disponibilités et prix moyens pour Saintes-Maries-de-la-Mer.
Cache 24h par date – 7 requêtes/jour (une par jour de prévision).
"""

import logging
import time
from datetime import date, timedelta

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

BOOKING_SEARCH_URL = "https://booking-com.p.rapidapi.com/v1/hotels/search"
DEST_ID = "-1437348"  # Saintes-Maries-de-la-Mer dest_id sur Booking
DEST_TYPE = "city"

# Cache 24h par date : {date_iso: (result_dict, timestamp)}
_cache: dict[str, tuple[dict, float]] = {}
_CACHE_TTL = 86400


def _headers() -> dict:
    return {
        "X-RapidAPI-Key": settings.rapidapi_key,
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com",
    }


def fetch_booking_data(checkin: date, checkout: date) -> dict:
    """
    Recherche les hôtels disponibles pour une nuit donnée.
    Retourne {"available_hotels": int, "avg_price": float}.
    Cache 24h par date.
    """
    cache_key = checkin.isoformat()

    # Vérifier le cache pour cette date spécifique
    if cache_key in _cache:
        cached_result, cached_ts = _cache[cache_key]
        if (time.time() - cached_ts) < _CACHE_TTL:
            return cached_result

    if not settings.rapidapi_key:
        return {}

    # Pause entre les requêtes pour éviter le rate-limit RapidAPI
    time.sleep(1.5)

    params = {
        "dest_id": DEST_ID,
        "dest_type": DEST_TYPE,
        "checkin_date": checkin.isoformat(),
        "checkout_date": checkout.isoformat(),
        "adults_number": 2,
        "room_number": 1,
        "units": "metric",
        "order_by": "price",
        "locale": "fr",
        "currency": "EUR",
        "filter_by_currency": "EUR",
        "page_number": 0,
    }

    try:
        with httpx.Client(timeout=20) as client:
            resp = client.get(BOOKING_SEARCH_URL, params=params, headers=_headers())
            resp.raise_for_status()

        data = resp.json()
        results = data.get("result", [])
        prices = []
        for hotel in results:
            price = hotel.get("min_total_price") or hotel.get("price_breakdown", {}).get("gross_price")
            if price:
                prices.append(float(price))

        result = {
            "available_hotels": len(results),
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
        }

        _cache[cache_key] = (result, time.time())
        log.info("Booking [%s]: %d hôtels dispo, prix moyen %.0f€",
                 cache_key, result["available_hotels"], result["avg_price"])
        return result

    except Exception as exc:
        log.warning("Booking fetch failed [%s]: %s", cache_key, exc)
        # Retourner le cache expiré si disponible
        if cache_key in _cache:
            return _cache[cache_key][0]
        return {}


def compute_booking_scores(target: date) -> tuple[float, float]:
    """
    Retourne (availability_score, price_score) basés sur les données Booking.
    Retourne (0, 0) si pas de données → le scoring utilisera l'heuristique.
    """
    checkout = target + timedelta(days=1)
    data = fetch_booking_data(target, checkout)

    if not data or not data.get("available_hotels"):
        return 0.0, 0.0

    available = data["available_hotels"]
    avg_price = data["avg_price"]

    # Score disponibilité basé sur les hôtels disponibles vs parc réel.
    # Saintes-Maries a 268 hébergements référencés sur Booking.
    # Moins il y en a de dispo, plus c'est fréquenté.
    TOTAL_ESTIMATED = 268
    occupancy_rate = max(0, 1 - (available / TOTAL_ESTIMATED))
    avail_score = round(min(100.0, occupancy_rate * 100), 1)

    # Score prix : échelle 0-100 basée sur le prix moyen
    # <50€ = 20, 50-80€ = 40, 80-120€ = 60, 120-180€ = 80, >180€ = 95
    if avg_price <= 50:
        price_score = 20.0
    elif avg_price <= 80:
        price_score = 40.0
    elif avg_price <= 120:
        price_score = 60.0
    elif avg_price <= 180:
        price_score = 80.0
    else:
        price_score = 95.0

    return avail_score, price_score
