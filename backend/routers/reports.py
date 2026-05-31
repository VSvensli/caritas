from fastapi import APIRouter

from backend.auth import AnyAuthenticated, StaffRead
from backend.schemas.report import ReportCreate, ReportRead, ReportSummary

router = APIRouter(tags=["reports"])


@router.post(
    "/villages/{village_id}/reports",
    response_model=ReportRead,
    status_code=201,
)
def submit_report(user: AnyAuthenticated, village_id: str, body: ReportCreate):
    raise NotImplementedError


@router.get(
    "/villages/{village_id}/reports",
    response_model=list[ReportRead],
)
def list_reports(user: AnyAuthenticated, village_id: str):
    raise NotImplementedError


@router.get("/reports/summary", response_model=ReportSummary)
def report_summary(user: StaffRead):
    raise NotImplementedError
