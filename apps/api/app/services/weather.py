"""
Connecteur météo – OpenWeatherMap (clé API requise).
Utilise l'API One Call 3.0 ou la Forecast 5-day/3h.
Coordonnées : Saintes-Maries-de-la-Mer.
"""

import httpx
from datetime import date, timedelta

from app.core.config import settings

OWM_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
LAT = 43.4527
LON = 4.4282

# OpenWeatherMap condition ID → score de base (0-100)
# Ref: https://openweathermap.org/weather-conditions
_OWM_SCORE: dict[int, float] = {
    800: 100,  # ciel dégagé
    801: 90,   # peu nuageux
    802: 78,   # nuages épars
    803: 60,   # nuages fragmentés
    804: 50,   # couvert
}


def _condition_score(condition_id: int) -> float:
    """Retourne un score basé sur l'ID de condition OWM."""
    if condition_id in _OWM_SCORE:
        return _OWM_SCORE[condition_id]
    group = condition_id // 100
    if group == 2:   # orage
        return 10.0
    if group == 3:   # bruine
        return 35.0
    if group == 5:   # pluie
        if condition_id <= 501:
            return 30.0
        return 15.0
    if group == 6:   # neige
        return 10.0
    if group == 7:   # brouillard, brume
        return 45.0
    return 50.0


def fetch_weather_scores() -> dict[str, float]:
    """
    Retourne {date_iso: score} pour les 5 prochains jours.
    Agrège les prévisions 3h en un score journalier.
    """
    api_key = settings.openweathermap_key
    if not api_key:
        return {}

    params = {
        "lat": LAT,
        "lon": LON,
        "appid": api_key,
        "units": "metric",
    }

    with httpx.Client(timeout=10) as client:
        resp = client.get(OWM_FORECAST_URL, params=params)
        resp.raise_for_status()

    data = resp.json()

    # Agrégation par jour : temp max, vent max, pire condition
    days: dict[str, dict] = {}

    for entry in data.get("list", []):
        dt_txt = entry["dt_txt"][:10]  # "2026-03-30"
        if dt_txt not in days:
            days[dt_txt] = {"tmax": -99, "wind_max": 0, "conditions": []}

        temp = entry["main"]["temp_max"]
        wind = entry["wind"]["speed"] * 3.6  # m/s → km/h
        cond_id = entry["weather"][0]["id"]

        day = days[dt_txt]
        day["tmax"] = max(day["tmax"], temp)
        day["wind_max"] = max(day["wind_max"], wind)
        day["conditions"].append(cond_id)

    result: dict[str, float] = {}

    for date_str, day in days.items():
        # Score = pire condition météo de la journée
        worst_score = min(_condition_score(c) for c in day["conditions"])
        score = worst_score

        # Bonus température
        tmax = day["tmax"]
        if tmax >= 28:
            score = min(100.0, score + 10)
        elif tmax >= 22:
            score = min(100.0, score + 5)
        elif tmax < 10:
            score = max(0.0, score - 15)

        # Pénalité vent (mistral)
        wind = day["wind_max"]
        if wind >= 80:
            score = max(0.0, score - 40)
        elif wind >= 60:
            score = max(0.0, score - 25)
        elif wind >= 40:
            score = max(0.0, score - 12)

        result[date_str] = round(score, 1)

    return result
