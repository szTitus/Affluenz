import hashlib
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func as sqlfunc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.booking import fetch_booking_data
from app.services.weather import cache_info as weather_cache_info
from app.services.weather import fetch_weather_raw, fetch_weather_scores
from app.db.session import get_db
from app.models.affluence import AffluenceScore, Event, VisitDaily, VisitorHashDaily
from app.schemas.affluence import AffluenceOut, EventIn, EventOut
from app.services.events_fetcher import fetch_events
from app.services.scoring import refresh_scores

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/refresh", status_code=200)
def trigger_refresh(
    db: Session = Depends(get_db),
    x_refresh_secret: str = Header(default=""),
):
    """Recalcule les scores. Nécessite le header X-Refresh-Secret."""
    if x_refresh_secret != settings.refresh_secret:
        raise HTTPException(status_code=401, detail="Invalid secret.")
    refresh_scores(db)
    return {"status": "refreshed"}


@router.get("/affluence/today", response_model=AffluenceOut)
def get_today(db: Session = Depends(get_db)):
    row = (
        db.query(AffluenceScore)
        .filter(AffluenceScore.score_date == date.today())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No score available for today.")
    return row


@router.get("/affluence/forecast", response_model=list[AffluenceOut])
def get_forecast(db: Session = Depends(get_db)):
    rows = (
        db.query(AffluenceScore)
        .filter(AffluenceScore.score_date >= date.today())
        .order_by(AffluenceScore.score_date)
        .limit(7)
        .all()
    )
    return rows


@router.get("/debug/events-raw")
def debug_events_raw():
    """Diagnostic complet : teste fetch_events et retourne le résultat."""
    import httpx
    key = settings.datatourisme_key
    # Appel direct sans cache
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                "https://api.datatourisme.fr/v1/catalog",
                params={
                    "api_key": key,
                    "geo_distance": "43.4527,4.4282,30km",
                    "filters": 'type=="EntertainmentAndEvent" OR type=="Festival" OR type=="SocialEvent"',
                    "page_size": 1,
                },
            )
        data = resp.json()
        total = data.get("meta", {}).get("total", "N/A")
        return {
            "key_preview": key[:8] + "..." if key else "EMPTY",
            "status": resp.status_code,
            "total_events": total,
            "fetch_events_result_len": len(fetch_events(key, days=7)),
        }
    except Exception as exc:
        return {"error": str(exc), "key_preview": key[:8] + "..." if key else "EMPTY"}


@router.get("/debug/weather")
def debug_weather(force: bool = False):
    """Données brutes Open-Meteo + scores météo calculés par jour.

    Query param ?force=1 pour ignorer le cache 24h.
    """
    try:
        raw = fetch_weather_raw(force_refresh=force)
        scores = fetch_weather_scores()
        daily = raw.get("daily", {})
        dates = daily.get("time", [])
        per_day = []
        for i, d in enumerate(dates):
            per_day.append({
                "date": d,
                "weathercode": daily.get("weathercode", [None])[i] if i < len(daily.get("weathercode", [])) else None,
                "tmax": daily.get("temperature_2m_max", [None])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
                "tmin": daily.get("temperature_2m_min", [None])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
                "wind_max_kmh": daily.get("windspeed_10m_max", [None])[i] if i < len(daily.get("windspeed_10m_max", [])) else None,
                "precipitation_mm": daily.get("precipitation_sum", [None])[i] if i < len(daily.get("precipitation_sum", [])) else None,
                "computed_score": scores.get(d),
            })
        return {
            "source": "open-meteo",
            "cache": weather_cache_info(),
            "days": per_day,
        }
    except Exception as exc:
        return {"error": str(exc)}


@router.get("/debug/booking")
def debug_booking():
    """Test Booking.com API."""
    from datetime import date, timedelta
    today = date.today()
    data = fetch_booking_data(today, today + timedelta(days=1))
    return {
        "key_preview": settings.rapidapi_key[:8] + "..." if settings.rapidapi_key else "EMPTY",
        "checkin": today.isoformat(),
        "result": data,
    }


@router.get("/debug/events-nofilter")
def debug_events_nofilter():
    """Test DATAtourisme events sans filtre date pour vérifier la clé API."""
    import httpx
    params = {
        "api_key": settings.datatourisme_key,
        "geo_distance": "43.4527,4.4282,30km",
        "filters": "@type=in=(schema:Event,schema:Festival,schema:EntertainmentAndEvent)",
        "page_size": 5,
    }
    key = settings.datatourisme_key
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                "https://api.datatourisme.fr/v1/catalog",
                params={
                    "api_key": key,
                    "page_size": 5,
                    "geo_distance": "43.4527,4.4282,30km",
                    "filters": 'type=="EntertainmentAndEvent" OR type=="Festival" OR type=="SocialEvent"',
                },
            )
        return {"status": resp.status_code, "body": resp.json()}
    except Exception as exc:
        return {"error": str(exc)}


@router.get("/events", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).order_by(Event.starts_at).all()


@router.post("/events", response_model=EventOut, status_code=201)
def create_event(payload: EventIn, db: Session = Depends(get_db)):
    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# ── Analytics ────────────────────────────────────────────────────────────
def _client_ip(request: Request) -> str:
    """Récupère la vraie IP client derrière un reverse proxy (Railway, Fastly)."""
    fwd = request.headers.get("x-forwarded-for") or ""
    if fwd:
        return fwd.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _visitor_hash(ip: str, user_agent: str, day: date) -> str:
    """Hash sha256 avec sel journalier → impossible de tracer un visiteur entre jours,
    et impossible de retrouver une IP en clair depuis le hash.
    """
    raw = f"{ip}|{user_agent}|{day.isoformat()}|{settings.refresh_secret}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.post("/track", status_code=204)
def track_visit(request: Request, db: Session = Depends(get_db)):
    """Enregistre une vue + dédupe le visiteur sur la journée.
    Pas de cookie, pas de PII stockée en clair. RGPD-friendly.
    """
    try:
        today = date.today()
        ip = _client_ip(request)
        ua = request.headers.get("user-agent", "")
        visitor = _visitor_hash(ip, ua, today)

        # Visiteur déjà vu aujourd'hui ?
        existing = (
            db.query(VisitorHashDaily)
            .filter(
                VisitorHashDaily.visit_date == today,
                VisitorHashDaily.visitor_hash == visitor,
            )
            .first()
        )
        is_new = existing is None

        # Upsert ligne quotidienne
        row = db.query(VisitDaily).filter(VisitDaily.visit_date == today).first()
        if not row:
            row = VisitDaily(visit_date=today, total_views=0, unique_visitors=0)
            db.add(row)

        row.total_views = (row.total_views or 0) + 1
        if is_new:
            row.unique_visitors = (row.unique_visitors or 0) + 1
            db.add(VisitorHashDaily(visit_date=today, visitor_hash=visitor))

        db.commit()
    except IntegrityError:
        # Course concurrente (2 requêtes simultanées même visiteur) → best-effort
        db.rollback()
    except Exception:
        # Un bug tracking ne doit JAMAIS casser le site
        db.rollback()
    return


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    x_stats_secret: str = Header(default=""),
    days: int = 30,
):
    """Stats agrégées. Nécessite le header X-Stats-Secret (= refresh_secret)."""
    if x_stats_secret != settings.refresh_secret:
        raise HTTPException(status_code=401, detail="Invalid secret.")

    days = max(1, min(days, 365))
    since = date.today() - timedelta(days=days - 1)

    rows = (
        db.query(VisitDaily)
        .filter(VisitDaily.visit_date >= since)
        .order_by(VisitDaily.visit_date)
        .all()
    )
    total_views = sum(r.total_views for r in rows)
    total_unique = sum(r.unique_visitors for r in rows)

    # Totaux "all time"
    all_time = db.query(
        sqlfunc.coalesce(sqlfunc.sum(VisitDaily.total_views), 0),
        sqlfunc.coalesce(sqlfunc.sum(VisitDaily.unique_visitors), 0),
    ).one()

    return {
        "range_days": days,
        "since": since.isoformat(),
        "total_views": total_views,
        "total_unique_visitors": total_unique,
        "all_time_views": int(all_time[0]),
        "all_time_unique_visitors": int(all_time[1]),
        "days": [
            {
                "date": r.visit_date.isoformat(),
                "views": r.total_views,
                "unique": r.unique_visitors,
            }
            for r in rows
        ],
    }


@router.post("/stats/cleanup", status_code=200)
def cleanup_old_hashes(
    db: Session = Depends(get_db),
    x_stats_secret: str = Header(default=""),
):
    """Purge les hashes > 48h. Les agrégats VisitDaily sont préservés."""
    if x_stats_secret != settings.refresh_secret:
        raise HTTPException(status_code=401, detail="Invalid secret.")

    cutoff = date.today() - timedelta(days=2)
    deleted = (
        db.query(VisitorHashDaily)
        .filter(VisitorHashDaily.visit_date < cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted": deleted, "cutoff": cutoff.isoformat()}
