"""
Connecteur Booking.com via RapidAPI (tipsters).
Récupère les disponibilités et prix moyens pour Saintes-Maries-de-la-Mer.
Cache 24h pour respecter le quota gratuit (~50 req/mois).
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

# Cache 24h
_cache: tuple[dict, float] = ({}, 0.0)
_CACHE_TTL = 86400


def _headers() -> dict:
    return {
        "X-RapidAPI-Key": settings.rapidapi_key,
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com",
    }


def fetch_booking_data(checkin: date, checkout: date) -> dict:
    """
    Recherche les hôtels disponibles pour une nuit donnée.
    Retourne {"available": int, "avg_price": float, "total": int}.
    Cache 24h.
    """
    global _cache
    cached, ts = _cache
    cache_key = checkin.isoformat()
    if cache_key in cached and (time.time() - ts) < _CACHE_TTL:
        return cached[cache_key]

    if not settings.rapidapi_key:
        return {}

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
        soldout_count = 0
        urgent_count = 0  # hôtels avec peu de chambres restantes
        for hotel in results:
            price = hotel.get("min_total_price") or hotel.get("price_breakdown", {}).get("gross_price")
            if price:
                prices.append(float(price))
            if hotel.get("soldout"):
                soldout_count += 1
            if hotel.get("urgency_room_msg"):
                urgent_count += 1

        result = {
            "available_hotels": len(results),
            "soldout": soldout_count,
            "urgent": urgent_count,
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
        }

        cached[cache_key] = result
        _cache = (cached, time.time())
        log.info("Booking: %d hôtels dispo (%d soldout, %d urgent), prix moyen %.0f€",
                 result["available_hotels"], soldout_count, urgent_count, result["avg_price"])
        return result

    except Exception as exc:
        log.warning("Booking fetch failed: %s", exc)
        return cached.get(cache_key, {})


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
    soldout = data.get("soldout", 0)
    urgent = data.get("urgent", 0)
    avg_price = data["avg_price"]

    # Score disponibilité basé sur les hôtels disponibles vs parc estimé.
    # Saintes-Maries a ~35 hébergements sur Booking.
    # On pondère : hôtels "urgent" (presque complets) comptent moins.
    TOTAL_ESTIMATED = 35
    effective_available = available - (urgent * 0.5)  # urgents = à moitié pris
    occupancy_rate = max(0, 1 - (effective_available / TOTAL_ESTIMATED))
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
