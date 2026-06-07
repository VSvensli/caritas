from datetime import datetime

from pydantic import BaseModel


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageRead(BaseModel):
    id: str
    thread_id: str
    sender_id: str
    sender_name: str
    content: str
    created_at: datetime


class ChatThreadRead(BaseModel):
    id: str
    reporter_id: str
    reporter_name: str
    village_id: str | None
    updated_at: datetime
    unread_count: int
    last_message: ChatMessageRead | None


class ChatThreadDetail(BaseModel):
    id: str
    reporter_id: str
    reporter_name: str
    messages: list[ChatMessageRead]
    created_at: datetime
    updated_at: datetime
