import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    master_id: uuid.UUID
    service_id: uuid.UUID
    starts_at: datetime
    client_name: str = Field(min_length=1)
    client_phone: str = Field(min_length=10)
    source_platform: str = "telegram"
    platform_user_id: str | None = None  # Platform-specific user ID (TG, MAX, VK)


class ManualBookingCreate(BaseModel):
    service_id: uuid.UUID
    starts_at: datetime
    client_name: str = Field(min_length=1)
    client_phone: str = Field(min_length=10)
    notes: str | None = None


class BookingRead(BaseModel):
    id: uuid.UUID
    master_id: uuid.UUID
    client_id: uuid.UUID
    service_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: str
    source_platform: str | None
    notes: str | None
    created_at: datetime
    service_name: str | None = None
    client_name: str | None = None
    client_phone: str | None = None

    model_config = {"from_attributes": True}


class BookingCancel(BaseModel):
    reason: str | None = None


class BookingReschedule(BaseModel):
    new_starts_at: datetime


class BookingListResponse(BaseModel):
    bookings: list[BookingRead]
    total: int
