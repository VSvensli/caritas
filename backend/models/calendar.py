import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class CalendarEntry(Base):
    __tablename__ = "calendar_entries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    village_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("villages.id"), index=True
    )
    crop_name: Mapped[str] = mapped_column(String(255))
    planting_start: Mapped[date] = mapped_column(Date)
    planting_end: Mapped[date] = mapped_column(Date)
    harvest_date: Mapped[date] = mapped_column(Date)
    season: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    village: Mapped["Village"] = relationship(back_populates="calendar_entries")
