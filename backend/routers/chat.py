from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.auth import AnyAuthenticated, StaffRead
from backend.database import get_db
from backend.models.chat import ChatMessage, ChatReadReceipt, ChatThread
from backend.models.user import Role, User
from backend.schemas.chat import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatThreadDetail,
    ChatThreadRead,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _is_staff(user: User) -> bool:
    return user.role in (Role.admin, Role.editor, Role.viewer)


def _message_read(message: ChatMessage) -> ChatMessageRead:
    return ChatMessageRead(
        id=message.id,
        thread_id=message.thread_id,
        sender_id=message.sender_id,
        sender_name=message.sender.full_name,
        content=message.content,
        created_at=message.created_at,
    )


def _check_access(thread: ChatThread, user: User) -> None:
    if not _is_staff(user) and thread.reporter_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


def _unread_count(db: Session, thread: ChatThread, user: User) -> int:
    receipt = db.execute(
        select(ChatReadReceipt).where(
            ChatReadReceipt.thread_id == thread.id,
            ChatReadReceipt.user_id == user.id,
        )
    ).scalar_one_or_none()

    query = select(func.count(ChatMessage.id)).where(
        ChatMessage.thread_id == thread.id
    )
    if receipt is not None:
        query = query.where(ChatMessage.created_at > receipt.last_read_at)

    return db.execute(query).scalar_one()


def _upsert_receipt(db: Session, thread_id: str, user_id: str) -> None:
    receipt = db.execute(
        select(ChatReadReceipt).where(
            ChatReadReceipt.thread_id == thread_id,
            ChatReadReceipt.user_id == user_id,
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if receipt is None:
        db.add(
            ChatReadReceipt(
                thread_id=thread_id, user_id=user_id, last_read_at=now
            )
        )
    else:
        receipt.last_read_at = now


def _thread_detail(thread: ChatThread) -> ChatThreadDetail:
    return ChatThreadDetail(
        id=thread.id,
        reporter_id=thread.reporter_id,
        reporter_name=thread.reporter.full_name,
        messages=[_message_read(m) for m in thread.messages],
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


def _load_thread(db: Session, thread_id: str) -> ChatThread:
    thread = db.execute(
        select(ChatThread)
        .options(
            selectinload(ChatThread.messages).selectinload(ChatMessage.sender),
            selectinload(ChatThread.reporter),
        )
        .where(ChatThread.id == thread_id)
    ).scalar_one_or_none()
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )
    return thread


@router.get("/threads", response_model=list[ChatThreadRead])
def list_threads(
    user: StaffRead,
    db: Annotated[Session, Depends(get_db)],
):
    threads = (
        db.execute(
            select(ChatThread)
            .options(
                selectinload(ChatThread.messages).selectinload(
                    ChatMessage.sender
                ),
                selectinload(ChatThread.reporter),
            )
            .order_by(ChatThread.updated_at.desc())
        )
        .scalars()
        .all()
    )

    result = []
    for thread in threads:
        last = thread.messages[-1] if thread.messages else None
        result.append(
            ChatThreadRead(
                id=thread.id,
                reporter_id=thread.reporter_id,
                reporter_name=thread.reporter.full_name,
                village_id=thread.reporter.village_id,
                updated_at=thread.updated_at,
                unread_count=_unread_count(db, thread, user),
                last_message=_message_read(last) if last else None,
            )
        )
    return result


@router.get("/threads/mine", response_model=ChatThreadDetail)
def my_thread(
    user: AnyAuthenticated,
    db: Annotated[Session, Depends(get_db)],
):
    if _is_staff(user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff do not have a personal thread",
        )

    thread = db.execute(
        select(ChatThread)
        .options(
            selectinload(ChatThread.messages).selectinload(ChatMessage.sender),
            selectinload(ChatThread.reporter),
        )
        .where(ChatThread.reporter_id == user.id)
    ).scalar_one_or_none()

    if thread is None:
        thread = ChatThread(reporter_id=user.id)
        db.add(thread)
        db.commit()
        db.refresh(thread)

    return _thread_detail(thread)


@router.get("/threads/by-reporter/{reporter_id}", response_model=ChatThreadDetail)
def thread_by_reporter(
    _user: StaffRead,
    reporter_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    reporter = db.get(User, reporter_id)
    if reporter is None or reporter.role != Role.reporter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reporter not found"
        )

    thread = db.execute(
        select(ChatThread)
        .options(
            selectinload(ChatThread.messages).selectinload(ChatMessage.sender),
            selectinload(ChatThread.reporter),
        )
        .where(ChatThread.reporter_id == reporter_id)
    ).scalar_one_or_none()

    if thread is None:
        thread = ChatThread(reporter_id=reporter_id)
        db.add(thread)
        db.flush()

    _upsert_receipt(db, thread.id, _user.id)
    db.commit()
    db.refresh(thread)

    return _thread_detail(thread)


@router.get("/threads/{thread_id}", response_model=ChatThreadDetail)
def get_thread(
    user: AnyAuthenticated,
    thread_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    thread = _load_thread(db, thread_id)
    _check_access(thread, user)

    _upsert_receipt(db, thread.id, user.id)
    db.commit()

    return _thread_detail(thread)


@router.post(
    "/threads/{thread_id}/messages",
    response_model=ChatMessageRead,
    status_code=201,
)
def send_message(
    user: AnyAuthenticated,
    thread_id: str,
    body: ChatMessageCreate,
    db: Annotated[Session, Depends(get_db)],
):
    thread = db.get(ChatThread, thread_id)
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )
    _check_access(thread, user)

    message = ChatMessage(
        thread_id=thread.id, sender_id=user.id, content=body.content
    )
    db.add(message)
    # Bump thread.updated_at so pollers detect the new message.
    thread.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(message)

    return _message_read(message)


@router.post("/threads/{thread_id}/read", status_code=204)
def mark_read(
    user: AnyAuthenticated,
    thread_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    thread = db.get(ChatThread, thread_id)
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )
    _check_access(thread, user)

    _upsert_receipt(db, thread.id, user.id)
    db.commit()
