from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.auth import AnyAuthenticated
from backend.database import get_db
from backend.models.calendar import Task
from backend.models.report import Report
from backend.models.user import Role
from backend.models.village import Village
from backend.schemas.sync import SyncStatus

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/villages/{village_id}/status", response_model=SyncStatus)
def sync_status(
    user: AnyAuthenticated,
    village_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    if user.role == Role.reporter and user.village_id != village_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    village = db.get(Village, village_id)
    if village is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Village not found"
        )

    calendar_updated_at = db.execute(
        select(func.max(Task.updated_at)).where(Task.village_id == village_id)
    ).scalar_one_or_none()

    reports_updated_at = db.execute(
        select(func.max(Report.created_at)).where(Report.village_id == village_id)
    ).scalar_one_or_none()

    return SyncStatus(
        village_updated_at=village.updated_at,
        calendar_updated_at=calendar_updated_at,
        reports_updated_at=reports_updated_at,
    )
