from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth import AdminOnly, hash_password, hash_pin
from backend.database import get_db
from backend.models.user import Role, User
from backend.schemas.user import DashboardUserCreate, UserRead, VillageUserCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(_user: AdminOnly, db: Annotated[Session, Depends(get_db)]):
    return db.execute(select(User).order_by(User.created_at)).scalars().all()


@router.post("", response_model=UserRead, status_code=201)
def create_dashboard_user(
    _user: AdminOnly, body: DashboardUserCreate, db: Annotated[Session, Depends(get_db)]
):
    existing = db.execute(
        select(User).where(User.email == body.email)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    new_user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=body.role,
        gender=body.gender,
        image_url=body.image_url,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/village", response_model=UserRead, status_code=201)
def create_village_user(
    _user: AdminOnly, body: VillageUserCreate, db: Annotated[Session, Depends(get_db)]
):
    existing = db.execute(
        select(User).where(User.phone_number == body.phone_number)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered",
        )

    new_user = User(
        phone_number=body.phone_number,
        full_name=body.full_name,
        hashed_pin=hash_pin(body.pin),
        role=Role.reporter,
        village_id=body.village_id,
        gender=body.gender,
        image_url=body.image_url,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.delete("/{user_id}", status_code=204)
def delete_user(_user: AdminOnly, user_id: str, db: Annotated[Session, Depends(get_db)]):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    db.delete(target)
    db.commit()
