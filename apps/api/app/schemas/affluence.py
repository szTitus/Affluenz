from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AffluenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    score_date: date
    zone: str
    global_score: float
    level: str
    availability_score: float
    price_score: float
    event_score: float
    weather_score: float
    confidence_score: float
    created_at: datetime


class EventIn(BaseModel):
    title: str
    starts_at: datetime
    ends_at: datetime
    expected_impact: float = 0.0


class EventOut(EventIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
