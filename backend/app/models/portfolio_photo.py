import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PortfolioPhoto(Base):
    __tablename__ = "portfolio_photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("masters.id", ondelete="CASCADE"),
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500))
    thumbnail_path: Mapped[str] = mapped_column(String(500))
    caption: Mapped[str | None] = mapped_column(String(255))
    service_tag: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # Relationships -- lazy="raise_on_sql" prevents accidental lazy loads in async
    master: Mapped["Master"] = relationship(  # noqa: F821
        back_populates="portfolio_photos", lazy="raise_on_sql"
    )
