from datetime import datetime

from pydantic import BaseModel


class VillageCreate(BaseModel):
    name: str
    latitude: float
    longitude: float


class VillageUpdate(BaseModel):
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    population: int | None = None


class VillageRead(BaseModel):
    id: str
    name: str
    slug: str
    latitude: float
    longitude: float
    population: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
