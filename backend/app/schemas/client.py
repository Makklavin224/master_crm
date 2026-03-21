import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.booking import BookingRead


class ClientRead(BaseModel):
    id: uuid.UUID
    phone: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MasterClientRead(BaseModel):
    client: ClientRead
    first_visit_at: datetime | None
    last_visit_at: datetime | None
    visit_count: int

    model_config = {"from_attributes": True}


class ClientDetailRead(BaseModel):
    client: ClientRead
    bookings: list[BookingRead]
    visit_count: int


# --- Client Cabinet OTP Auth Schemas ---


class OTPRequest(BaseModel):
    phone: str


class OTPVerify(BaseModel):
    phone: str
    code: str


class OTPResponse(BaseModel):
    success: bool
    message: str
    cooldown_seconds: int | None = None


class SessionResponse(BaseModel):
    token: str


# --- Client Cabinet Bookings & Reviews Schemas ---


class ClientBookingRead(BaseModel):
    id: uuid.UUID
    master_id: uuid.UUID
    master_name: str
    service_id: uuid.UUID
    service_name: str
    starts_at: datetime
    ends_at: datetime
    status: str
    source_platform: str | None = None
    master_username: str | None = None

    model_config = {"from_attributes": True}


class ClientBookingsResponse(BaseModel):
    upcoming: list[ClientBookingRead]
    past: list[ClientBookingRead]


class ReviewCreate(BaseModel):
    booking_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=500)


class ReviewCreateResponse(BaseModel):
    id: uuid.UUID
    rating: int
    text: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
