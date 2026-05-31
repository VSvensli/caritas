from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.auth import AnyAuthenticated, StaffWrite
from backend.database import get_db
from backend.models.calendar import SubTask, Task
from backend.models.user import Role
from backend.models.village import Village
from backend.schemas.calendar import (
    TaskCreate,
    TaskRead,
    TaskUpdate,
)

router = APIRouter(prefix="/villages/{village_id}/calendar", tags=["calendar"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    user: AnyAuthenticated,
    village_id: str,
    db: Annotated[Session, Depends(get_db)],
    updated_since: datetime | None = Query(None),
):
    if user.role == Role.reporter and user.village_id != village_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    query = (
        select(Task)
        .options(selectinload(Task.subtasks))
        .where(Task.village_id == village_id)
    )
    if updated_since is not None:
        query = query.where(Task.updated_at >= updated_since)
    query = query.order_by(Task.due_date)

    return db.execute(query).scalars().all()


@router.post("", response_model=TaskRead, status_code=201)
def create_task(
    _user: StaffWrite,
    village_id: str,
    body: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
):
    if db.get(Village, village_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Village not found"
        )

    task = Task(**body.model_dump(exclude={"subtasks"}), village_id=village_id)
    for st in body.subtasks:
        task.subtasks.append(SubTask(**st.model_dump()))
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    _user: StaffWrite,
    village_id: str,
    task_id: str,
    body: TaskUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    task = db.execute(
        select(Task)
        .options(selectinload(Task.subtasks))
        .where(Task.id == task_id, Task.village_id == village_id)
    ).scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    updates = body.model_dump(exclude_unset=True)
    subtasks_data = updates.pop("subtasks", None)

    for field, value in updates.items():
        setattr(task, field, value)

    if subtasks_data is not None:
        task.subtasks.clear()
        for st in subtasks_data:
            task.subtasks.append(SubTask(**st))

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    _user: StaffWrite,
    village_id: str,
    task_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    task = db.execute(
        select(Task).where(Task.id == task_id, Task.village_id == village_id)
    ).scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    db.delete(task)
    db.commit()
