import uuid
from datetime import datetime

from pydantic import BaseModel

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
