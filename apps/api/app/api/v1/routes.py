from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
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
def trigger_refresh(db: Session = Depends(get_db)):
    """Recalcule les scores à partir des sources externes."""
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
    """Retourne les événements bruts OpenAgenda pour vérifier l'intégration."""
    events = fetch_events(settings.openagenda_key, days=7)
    return {"count": len(events), "events": events[:5]}


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
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                "https://api.datatourisme.fr/v1/catalog",
                params=params,
                headers={"X-API-Key": settings.datatourisme_key},
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
