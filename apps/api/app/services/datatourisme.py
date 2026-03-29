"""
Connecteur DATAtourisme (gratuit, clé API requise).
Récupère le nombre total de logements référencés autour de Saintes-Maries-de-la-Mer.
Cache 24h pour éviter des appels répétés.
"""

import time
import httpx

DATATOURISME_URL = "https://api.datatourisme.fr/v1/catalog"
LAT = 43.4527
LON = 4.4282

# Cache simple : (valeur, timestamp)
_cache: tuple[int, float] = (0, 0.0)
_CACHE_TTL = 86400  # 24h en secondes


def fetch_accommodation_count(api_key: str) -> int:
    """
    Retourne le nombre total de logements touristiques dans un rayon de 20 km.
    Résultat mis en cache 24h. Retourne 0 en cas d'erreur.
    """
    global _cache
    count, ts = _cache
    if count > 0 and (time.time() - ts) < _CACHE_TTL:
        return count

    params = {
        "api_key": api_key,
        "geo_distance": f"{LAT},{LON},20km",
        "filters": "@type=in=(schema:Accommodation,schema:Hotel,schema:Hostel,"
                   "schema:BedAndBreakfast,schema:LodgingBusiness)",
        "page_size": 1,
    }
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(DATATOURISME_URL, params=params)
            resp.raise_for_status()
        total = resp.json().get("total", 0)
        if total > 0:
            _cache = (total, time.time())
        return total
    except Exception:
        return count  # retourne la dernière valeur connue
