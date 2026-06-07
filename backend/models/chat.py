import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.user import User


class ChatThread(Base):
    __tablename__ = "chat_threads"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid7())
    )
    reporter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    reporter: Mapped["User"] = relationship()
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    read_receipts: Mapped[list["ChatReadReceipt"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid7())
    )
    thread_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_threads.id"), index=True
    )
    sender_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    thread: Mapped["ChatThread"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship()


class ChatReadReceipt(Base):
    __tablename__ = "chat_read_receipts"
    __table_args__ = (UniqueConstraint("thread_id", "user_id"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid7())
    )
    thread_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_threads.id"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )
    last_read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    thread: Mapped["ChatThread"] = relationship(back_populates="read_receipts")
    user: Mapped["User"] = relationship()
