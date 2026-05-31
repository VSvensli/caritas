from datetime import datetime

from pydantic import BaseModel


class SyncStatus(BaseModel):
    villages_updated_at: datetime | None
    calendar_updated_at: datetime | None
    reports_updated_at: datetime | None
