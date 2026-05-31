from datetime import datetime

from pydantic import BaseModel


class ReportCreate(BaseModel):
    client_id: str
    reported_at: datetime
    yield_kg: float | None = None
    self_consumption_kg: float | None = None
    sold_kg: float | None = None
    revenue: int | None = None
    fertilizer_produced_kg: float | None = None
    fertilizer_used_kg: float | None = None
    pesticide_produced_l: float | None = None
    pesticide_used_l: float | None = None


class ReportRead(BaseModel):
    id: str
    client_id: str
    village_id: str
    reporter_id: str
    reported_at: datetime
    yield_kg: float | None
    self_consumption_kg: float | None
    sold_kg: float | None
    revenue: int | None
    fertilizer_produced_kg: float | None
    fertilizer_used_kg: float | None
    pesticide_produced_l: float | None
    pesticide_used_l: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportSummary(BaseModel):
    village_count: int
    report_count: int
    total_yield_kg: float
    total_self_consumption_kg: float
    total_sold_kg: float
    total_revenue: int
    total_fertilizer_produced_kg: float
    total_fertilizer_used_kg: float
    total_pesticide_produced_l: float
    total_pesticide_used_l: float
