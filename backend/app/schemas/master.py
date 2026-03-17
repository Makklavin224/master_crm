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
