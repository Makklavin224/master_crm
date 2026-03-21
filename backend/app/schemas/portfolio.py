"""Portfolio photo schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class PortfolioPhotoRead(BaseModel):
    id: uuid.UUID
    file_path: str
    thumbnail_path: str
    caption: str | None = None
    service_tag: str | None = None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PortfolioPhotoUpdate(BaseModel):
    caption: str | None = None
    service_tag: str | None = None


class PortfolioReorderItem(BaseModel):
    id: uuid.UUID
    sort_order: int


class PortfolioReorderRequest(BaseModel):
    items: list[PortfolioReorderItem]
