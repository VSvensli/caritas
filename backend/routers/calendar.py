from datetime import datetime

from fastapi import APIRouter, Query

from backend.auth import AnyAuthenticated, StaffWrite
from backend.schemas.calendar import (
    CalendarEntryCreate,
    CalendarEntryRead,
    CalendarEntryUpdate,
)

router = APIRouter(prefix="/villages/{village_id}/calendar", tags=["calendar"])


@router.get("", response_model=list[CalendarEntryRead])
def list_calendar(
    user: AnyAuthenticated,
    village_id: str,
    updated_since: datetime | None = Query(None),
):
    raise NotImplementedError


@router.post("", response_model=CalendarEntryRead, status_code=201)
def create_calendar_entry(user: StaffWrite, village_id: str, body: CalendarEntryCreate):
    raise NotImplementedError


@router.put("/{entry_id}", response_model=CalendarEntryRead)
def update_calendar_entry(
    user: StaffWrite, village_id: str, entry_id: str, body: CalendarEntryUpdate
):
    raise NotImplementedError


@router.delete("/{entry_id}", status_code=204)
def delete_calendar_entry(user: StaffWrite, village_id: str, entry_id: str):
    raise NotImplementedError
