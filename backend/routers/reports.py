from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.auth import AnyAuthenticated, StaffRead
from backend.database import get_db
from backend.models.report import Report
from backend.models.user import Role
from backend.models.village import Village
from backend.schemas.report import ReportCreate, ReportRead, ReportSummary

router = APIRouter(tags=["reports"])


@router.post(
    "/villages/{village_id}/reports",
    response_model=ReportRead,
    status_code=201,
)
def submit_report(
    user: AnyAuthenticated,
    village_id: str,
    body: ReportCreate,
    db: Annotated[Session, Depends(get_db)],
):
    if user.role == Role.reporter and user.village_id != village_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    if db.get(Village, village_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Village not found"
        )

    existing = db.execute(
        select(Report).where(Report.client_id == body.client_id)
    ).scalar_one_or_none()
    if existing:
        return existing

    report = Report(**body.model_dump(), village_id=village_id, reporter_id=user.id)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get(
    "/villages/{village_id}/reports",
    response_model=list[ReportRead],
)
def list_reports(
    user: AnyAuthenticated,
    village_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    if user.role == Role.reporter and user.village_id != village_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return (
        db.execute(
            select(Report)
            .where(Report.village_id == village_id)
            .order_by(Report.reported_at.desc())
        )
        .scalars()
        .all()
    )


@router.get("/reports/summary", response_model=ReportSummary)
def report_summary(
    _user: StaffRead,
    db: Annotated[Session, Depends(get_db)],
):
    row = db.execute(
        select(
            func.count(func.distinct(Report.village_id)).label("village_count"),
            func.count(Report.id).label("report_count"),
            func.coalesce(func.sum(Report.yield_kg), 0).label("total_yield_kg"),
            func.coalesce(func.sum(Report.self_consumption_kg), 0).label(
                "total_self_consumption_kg"
            ),
            func.coalesce(func.sum(Report.sold_kg), 0).label("total_sold_kg"),
            func.coalesce(func.sum(Report.revenue_idr), 0).label("total_revenue_idr"),
            func.coalesce(func.sum(Report.fertilizer_produced_kg), 0).label(
                "total_fertilizer_produced_kg"
            ),
            func.coalesce(func.sum(Report.fertilizer_used_kg), 0).label(
                "total_fertilizer_used_kg"
            ),
            func.coalesce(func.sum(Report.pesticide_produced_l), 0).label(
                "total_pesticide_produced_l"
            ),
            func.coalesce(func.sum(Report.pesticide_used_l), 0).label(
                "total_pesticide_used_l"
            ),
        )
    ).one()

    return ReportSummary(**row._asdict())
