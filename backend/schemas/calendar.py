from datetime import date, datetime

from pydantic import BaseModel


class SubTask(BaseModel):
    id: str
    task_id: str
    title: str
    description: str | None
    due_date: date | None
    duration_minutes: int | None
    is_done: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    task_type: str
    due_date: date | None = None
    season: str
    year: int
    subtasks: list[SubTask] = []


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    task_type: str | None = None
    due_date: date | None = None
    season: str | None = None
    year: int | None = None
    subtasks: list[SubTask] | None = None


class TaskRead(BaseModel):
    id: str
    village_id: str
    title: str
    description: str | None
    task_type: str
    due_date: date | None
    season: str
    year: int
    subtasks: list[SubTask]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
