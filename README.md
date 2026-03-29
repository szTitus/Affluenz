# Affluence V2

Webapp locale pour estimer l'affluence dans un village touristique.

## Lancement

```bash
cp .env.example .env
docker compose up --build
```

- Frontend : http://localhost:3000
- API / Swagger : http://localhost:8000/docs

## Architecture

| Service | Image | Port |
|---------|-------|------|
| db | postgres:16-alpine | 5432 |
| api | python:3.12-slim | 8000 |
| web | node:20-alpine | 3000 |

## Score d'affluence (V2 – démo)

Le score est calculé à partir de 4 composants simulés :

| Composant | Description |
|-----------|-------------|
| `availability_score` | Taux d'occupation simulé (hébergements, parkings) |
| `price_score` | Niveau de prix relatif (hôtels, restaurants) |
| `event_score` | Impact des événements programmés |
| `weather_score` | Météo simulée (beau temps = plus de touristes) |

Le `global_score` est une moyenne pondérée. Le niveau (`level`) est déduit :
- `low` : < 40
- `medium` : 40–69
- `high` : ≥ 70

## Ajouter des sources de données (V3+)

- **Disponibilités réelles** : connecter une API Booking/Airbnb dans `services/scoring.py`, fonction `compute_availability_score()`.
- **Météo réelle** : appel OpenWeatherMap dans `compute_weather_score()`.
- **Prix dynamiques** : scraping ou API hôtelière dans `compute_price_score()`.
- **Événements** : alimenter la table `events` via `POST /api/v1/events`.
