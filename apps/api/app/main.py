from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router
from app.db.session import SessionLocal, init_db
from app.services.scoring import refresh_scores


def _scheduled_refresh():
    """Appelée par le scheduler toutes les heures."""
    db = SessionLocal()
    try:
        refresh_scores(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init DB + premier calcul des scores
    init_db()
    _scheduled_refresh()

    # Scheduler : recalcul toutes les heures
    scheduler = BackgroundScheduler()
    scheduler.add_job(_scheduled_refresh, "interval", hours=1, id="refresh_scores")
    scheduler.start()

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Affluence API",
    version="3.0.0",
    description="API d'estimation de l'affluence – Saintes-Maries-de-la-Mer.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
