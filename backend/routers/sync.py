from fastapi import APIRouter

from backend.auth import AnyAuthenticated
from backend.schemas.sync import SyncStatus

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status", response_model=SyncStatus)
def sync_status(user: AnyAuthenticated):
    raise NotImplementedError
