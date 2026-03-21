import uuid
from datetime import datetime

from pydantic import BaseModel


class MasterRead(BaseModel):
    id: uuid.UUID
    email: str | None
    phone: str | None
    name: str
    business_name: str | None
    timezone: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MasterPublicProfile(BaseModel):
    """Public profile returned on the master's public page."""

    id: uuid.UUID
    name: str
    username: str | None = None
    specialization: str | None = None
    city: str | None = None
    avatar_path: str | None = None
    instagram_url: str | None = None
    avg_rating: float | None = None
    review_count: int = 0

    model_config = {"from_attributes": True}
