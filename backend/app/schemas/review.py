import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewRead(BaseModel):
    """Public review as shown on the master's page."""

    id: uuid.UUID
    rating: int
    text: str | None = None
    client_name: str
    master_reply: str | None = None
    master_replied_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewAdminRead(BaseModel):
    """Review as shown in master's admin panel (includes all statuses)."""

    id: uuid.UUID
    booking_id: uuid.UUID | None = None
    rating: int
    text: str | None = None
    client_name: str
    client_phone: str
    service_name: str
    master_reply: str | None = None
    master_replied_at: datetime | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewReplyRequest(BaseModel):
    """Master's reply to a review."""

    reply_text: str = Field(min_length=1, max_length=500)


class ReviewsListResponse(BaseModel):
    """Paginated list of reviews for admin panel."""

    reviews: list[ReviewAdminRead]
    total: int
