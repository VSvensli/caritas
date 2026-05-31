from datetime import date, datetime

from pydantic import BaseModel


class CalendarEntryCreate(BaseModel):
    crop_name: str
    planting_start: date
    planting_end: date
    harvest_date: date
    season: str
    year: int


class CalendarEntryUpdate(BaseModel):
    crop_name: str | None = None
    planting_start: date | None = None
    planting_end: date | None = None
    harvest_date: date | None = None
    season: str | None = None
    year: int | None = None


class CalendarEntryRead(BaseModel):
    id: str
    village_id: str
    crop_name: str
    planting_start: date
    planting_end: date
    harvest_date: date
    season: str
    year: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
