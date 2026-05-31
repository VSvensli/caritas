from datetime import datetime

from pydantic import BaseModel, field_validator

from backend.models.user import Gender, Role


class DashboardUserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: Role = Role.viewer
    gender: Gender | None = None
    image_url: str | None = None

    @field_validator("role")
    @classmethod
    def role_must_not_be_reporter(cls, v: Role) -> Role:
        if v == Role.reporter:
            raise ValueError("Use the village user endpoint to create reporters")
        return v


class VillageUserCreate(BaseModel):
    phone_number: str
    full_name: str
    pin: str
    village_id: str
    gender: Gender | None = None
    image_url: str | None = None

    @field_validator("pin")
    @classmethod
    def pin_must_be_four_digits(cls, v: str) -> str:
        if not (len(v) == 4 and v.isdigit()):
            raise ValueError("PIN must be exactly 4 digits")
        return v


class UserRead(BaseModel):
    id: str
    email: str | None
    phone_number: str | None
    full_name: str
    role: Role
    gender: Gender | None
    image_url: str | None
    village_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
