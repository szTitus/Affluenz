from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AffluenceScore(Base):
    __tablename__ = "affluence_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    score_date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    zone: Mapped[str] = mapped_column(String(100), default="village-centre")
    global_score: Mapped[float] = mapped_column(Float, nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # low | medium | high

    # Composants
    availability_score: Mapped[float] = mapped_column(Float, default=0.0)
    price_score: Mapped[float] = mapped_column(Float, default=0.0)
    event_score: Mapped[float] = mapped_column(Float, default=0.0)
    weather_score: Mapped[float] = mapped_column(Float, default=0.0)

    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expected_impact: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 – 1.0


class VisitDaily(Base):
    """Agrégat quotidien des visites. Pas de PII : on stocke uniquement des compteurs."""
    __tablename__ = "visits_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    visit_date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    total_views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_visitors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class VisitorHashDaily(Base):
    """Hash éphémère (IP+UA+sel journalier) — sert uniquement à déduper les vues dans la journée.
    Les lignes peuvent être purgées après 48h sans perte d'info (les totaux sont dans VisitDaily).
    """
    __tablename__ = "visitor_hashes_daily"
    __table_args__ = (
        UniqueConstraint("visit_date", "visitor_hash", name="uq_visit_day_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    visit_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    visitor_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # sha256 hex
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
