import uuid
from datetime import datetime

from pydantic import BaseModel


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
