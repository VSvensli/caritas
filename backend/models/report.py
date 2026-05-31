import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid7())
    )
    client_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True
    )
    village_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("villages.id"), index=True
    )
    reporter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    yield_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    self_consumption_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    sold_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_idr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fertilizer_produced_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    fertilizer_used_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    pesticide_produced_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    pesticide_used_l: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    village: Mapped["Village"] = relationship(back_populates="reports")
    reporter: Mapped["User"] = relationship()
