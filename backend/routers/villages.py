from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth import AnyAuthenticated, StaffWrite
from backend.database import get_db
from backend.models.user import Role, User
from backend.models.village import Village
from backend.schemas.user import UserRead
from backend.schemas.village import VillageCreate, VillageRead, VillageUpdate

router = APIRouter(prefix="/villages", tags=["villages"])


@router.get("", response_model=list[VillageRead])
def list_villages(_user: AnyAuthenticated, db: Annotated[Session, Depends(get_db)]):
    return db.execute(select(Village).order_by(Village.name)).scalars().all()


@router.post("", response_model=VillageRead, status_code=201)
def create_village(
    _user: StaffWrite, body: VillageCreate, db: Annotated[Session, Depends(get_db)]
):
    existing = db.execute(
        select(Village).where(Village.slug == body.slug)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Village slug already exists",
        )

    village = Village(**body.model_dump())
    db.add(village)
    db.commit()
    db.refresh(village)
    return village


@router.get("/{village_id}", response_model=VillageRead)
def get_village(
    user: AnyAuthenticated, village_id: str, db: Annotated[Session, Depends(get_db)]
):
    if user.role == Role.reporter and user.village_id != village_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    village = db.get(Village, village_id)
    if village is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Village not found")
    return village


@router.put("/{village_id}", response_model=VillageRead)
def update_village(
    _user: StaffWrite,
    village_id: str,
    body: VillageUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    village = db.get(Village, village_id)
    if village is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Village not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(village, field, value)

    db.commit()
    db.refresh(village)
    return village


@router.delete("/{village_id}", status_code=204)
def delete_village(
    _user: StaffWrite, village_id: str, db: Annotated[Session, Depends(get_db)]
):
    village = db.get(Village, village_id)
    if village is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Village not found")
    db.delete(village)
    db.commit()


@router.get("/{village_id}/reporters", response_model=list[UserRead])
def list_village_reporters(
    _user: StaffWrite, village_id: str, db: Annotated[Session, Depends(get_db)]
):
    village = db.get(Village, village_id)
    if village is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Village not found")

    reporters = db.execute(
        select(User).where(User.village_id == village_id, User.role == Role.reporter)
    ).scalars().all()
    return reporters
