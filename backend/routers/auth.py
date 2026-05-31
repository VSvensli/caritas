from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth import (
    _decode_token,
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_pin,
)
from backend.database import get_db
from backend.models.user import User
from backend.schemas.auth import LoginRequest, PinLoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    user = db.execute(
        select(User).where(User.email == body.email)
    ).scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.post("/pin-login", response_model=TokenResponse)
def pin_login(body: PinLoginRequest, db: Annotated[Session, Depends(get_db)]):
    user = db.execute(
        select(User).where(User.phone_number == body.phone_number)
    ).scalar_one_or_none()

    if user is None or user.hashed_pin is None or not verify_pin(body.pin, user.hashed_pin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or PIN",
        )

    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    refresh_token: Annotated[str, Body(embed=True)],
    db: Annotated[Session, Depends(get_db)],
):
    payload = _decode_token(refresh_token, "refresh")
    user = db.get(User, payload["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return TokenResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )
