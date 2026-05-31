from datetime import datetime

from pydantic import BaseModel


class VillageCreate(BaseModel):
    name: str
    slug: str
    latitude: float
    longitude: float
    population: int = 0
    phone_number: str | None = None


class VillageUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    population: int | None = None
    phone_number: str | None = None


class VillageRead(BaseModel):
    id: str
    name: str
    slug: str
    latitude: float
    longitude: float
    population: int
    phone_number: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
