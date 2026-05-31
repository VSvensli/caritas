import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.village import Village


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class Role(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    viewer = "viewer"
    reporter = "reporter"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid7())
    )
    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(
        String(20), unique=True, index=True, nullable=True
    )
    hashed_pin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.viewer)
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    village_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("villages.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    village: Mapped["Village"] = relationship(back_populates="reporters")
