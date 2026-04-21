"""
Connecteur météo – Open-Meteo (gratuit, sans clé API).
Coordonnées : Saintes-Maries-de-la-Mer.

Docs : https://open-meteo.com/en/docs
WMO weather codes : https://open-meteo.com/en/docs#api_form
"""

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
LAT = 43.4527
LON = 4.4282

# WMO weather code → score de base (0-100)
_WMO_SCORE: dict[int, float] = {
    0:  100,  # ciel dégagé
    1:   92,  # principalement clair
    2:   78,  # partiellement nuageux
    3:   60,  # couvert
    45:  45,  # brouillard
    48:  40,  # brouillard givrant
    51:  40,  # bruine légère
    53:  32,  # bruine modérée
    55:  25,  # bruine dense
    56:  25,  # bruine verglaçante légère
    57:  20,  # bruine verglaçante dense
    61:  30,  # pluie légère
    63:  20,  # pluie modérée
    65:  10,  # pluie forte
    66:  15,  # pluie verglaçante légère
    67:  10,  # pluie verglaçante forte
    71:  20,  # neige légère
    73:  12,  # neige modérée
    75:   5,  # neige forte
    77:  15,  # grésil
    80:  28,  # averses légères
    81:  18,  # averses modérées
    82:  10,  # averses violentes
    85:  15,  # averses de neige légères
    86:   8,  # averses de neige fortes
    95:   8,  # orage
    96:   5,  # orage avec grêle légère
    99:   2,  # orage avec grêle forte
}


def _code_score(code: int) -> float:
    return _WMO_SCORE.get(code, 50.0)


def fetch_weather_raw() -> dict:
    """
    Retourne la réponse brute d'Open-Meteo (pour debug).
    """
    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,"
                 "precipitation_sum,windspeed_10m_max",
        "timezone": "Europe/Paris",
        "forecast_days": 7,
    }
    with httpx.Client(timeout=10) as client:
        resp = client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()
    return resp.json()


def fetch_weather_scores() -> dict[str, float]:
    """
    Retourne {date_iso: score} pour les 7 prochains jours via Open-Meteo.
    """
    try:
        data = fetch_weather_raw()
    except Exception:
        return {}

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    codes = daily.get("weathercode", [])
    tmaxs = daily.get("temperature_2m_max", [])
    winds = daily.get("windspeed_10m_max", [])
    precs = daily.get("precipitation_sum", [])

    result: dict[str, float] = {}

    for i, date_str in enumerate(dates):
        code = codes[i] if i < len(codes) else 3
        tmax = tmaxs[i] if i < len(tmaxs) else 20.0
        wind = winds[i] if i < len(winds) else 0.0
        prec = precs[i] if i < len(precs) else 0.0

        score = _code_score(int(code))

        # Bonus température (plus on a chaud, plus les gens viennent)
        if tmax >= 30:
            score = min(100.0, score + 12)
        elif tmax >= 26:
            score = min(100.0, score + 8)
        elif tmax >= 22:
            score = min(100.0, score + 4)
        elif tmax < 10:
            score = max(0.0, score - 15)
        elif tmax < 15:
            score = max(0.0, score - 6)

        # Pénalité vent (mistral – fréquent en Camargue)
        if wind >= 80:
            score = max(0.0, score - 35)
        elif wind >= 60:
            score = max(0.0, score - 20)
        elif wind >= 40:
            score = max(0.0, score - 10)
        elif wind >= 30:
            score = max(0.0, score - 5)

        # Pénalité précipitations cumulées
        if prec >= 10:
            score = max(0.0, score - 15)
        elif prec >= 3:
            score = max(0.0, score - 7)

        result[date_str] = round(score, 1)

    return result
