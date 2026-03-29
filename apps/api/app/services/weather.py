"""
Connecteur météo – Open-Meteo (gratuit, sans clé API).
Coordonnées : Saintes-Maries-de-la-Mer.
"""

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
LAT = 43.4527
LON = 4.4282

# WMO weather code → score de base (0-100)
_WMO_SCORE: dict[int, float] = {
    0: 100,               # ciel dégagé
    1: 92, 2: 80, 3: 65,  # peu nuageux → couvert
    45: 50, 48: 45,       # brouillard
    51: 40, 53: 35, 55: 30, 56: 25, 57: 20,  # bruine
    61: 30, 63: 22, 65: 15, 66: 15, 67: 10,  # pluie
    71: 15, 73: 10, 75: 5, 77: 5,            # neige
    80: 35, 81: 25, 82: 15,                  # averses
    85: 10, 86: 5,                            # averses de neige
    95: 10, 96: 5, 99: 5,                    # orages
}


def fetch_weather_scores() -> dict[str, float]:
    """
    Retourne {date_iso: score} pour les 7 prochains jours.
    En cas d'erreur, retourne un dict vide (le scoring utilisera 50 par défaut).
    """
    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": "weathercode,temperature_2m_max",
        "timezone": "Europe/Paris",
        "forecast_days": 7,
    }
    with httpx.Client(timeout=10) as client:
        resp = client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()

    data = resp.json()
    result: dict[str, float] = {}

    for date_str, wcode, tmax in zip(
        data["daily"]["time"],
        data["daily"]["weathercode"],
        data["daily"]["temperature_2m_max"],
    ):
        score = _WMO_SCORE.get(int(wcode), 50.0)
        # Bonus température : Saintes-Maries vit du soleil et de la chaleur
        if tmax is not None:
            if tmax >= 28:
                score = min(100.0, score + 10)
            elif tmax >= 22:
                score = min(100.0, score + 5)
            elif tmax < 10:
                score = max(0.0, score - 15)
        result[date_str] = round(score, 1)

    return result
