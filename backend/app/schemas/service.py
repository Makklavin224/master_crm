import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    duration_minutes: int = Field(ge=5, le=480)
    price: int = Field(ge=0)
    category: str | None = None
    description: str | None = None


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    duration_minutes: int | None = Field(default=None, ge=5, le=480)
    price: int | None = Field(default=None, ge=0)
    category: str | None = None
    description: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class ServiceRead(BaseModel):
    id: uuid.UUID
    master_id: uuid.UUID
    name: str
    description: str | None
    duration_minutes: int
    price: int
    category: str | None
    is_active: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
