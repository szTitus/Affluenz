from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, func
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
