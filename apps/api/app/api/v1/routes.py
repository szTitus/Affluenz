from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.booking import fetch_booking_data
from app.db.session import get_db
from app.models.affluence import AffluenceScore, Event
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


@router.get("/debug/booking")
def debug_booking():
    """Test Booking.com API — affiche les champs d'un hôtel pour debug."""
    from datetime import date, timedelta
    import httpx
    today = date.today()
    if not settings.rapidapi_key:
        return {"error": "no key"}
    params = {
        "dest_id": "-1437348", "dest_type": "city",
        "checkin_date": today.isoformat(),
        "checkout_date": (today + timedelta(days=1)).isoformat(),
        "adults_number": 2, "room_number": 1, "units": "metric",
        "order_by": "price", "locale": "fr", "currency": "EUR",
        "filter_by_currency": "EUR", "page_number": 0,
    }
    headers = {
        "X-RapidAPI-Key": settings.rapidapi_key,
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com",
    }
    with httpx.Client(timeout=20) as client:
        resp = client.get("https://booking-com.p.rapidapi.com/v1/hotels/search",
                          params=params, headers=headers)
    data = resp.json()
    results = data.get("result", [])
    if not results:
        return {"hotels": 0}
    # Retourne les clés du premier hôtel + un extrait des 3 premiers
    first = results[0]
    sample = [
        {k: h.get(k) for k in ("hotel_name", "available_rooms", "rooms_left",
                                 "number_of_rooms", "room_count", "min_total_price",
                                 "unit_configuration_label")}
        for h in results[:3]
    ]
    return {
        "total_hotels": len(results),
        "first_hotel_keys": sorted(first.keys()),
        "sample": sample,
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
