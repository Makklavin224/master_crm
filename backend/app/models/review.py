import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
    )
    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("masters.id", ondelete="CASCADE"),
        index=True,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
    )
    rating: Mapped[int] = mapped_column(Integer)
    text: Mapped[str | None] = mapped_column(String(500))
    master_reply: Mapped[str | None] = mapped_column(String(500))
    master_replied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    status: Mapped[str] = mapped_column(
        String(20), default="published", server_default=sa.text("'published'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.text("now()"),
        onupdate=datetime.now,
    )

    # Relationships -- lazy="raise_on_sql" prevents accidental lazy loads in async
    master: Mapped["Master"] = relationship(  # noqa: F821
        back_populates="reviews", lazy="raise_on_sql"
    )
    booking: Mapped["Booking"] = relationship(  # noqa: F821
        lazy="raise_on_sql"
    )
    client: Mapped["Client"] = relationship(  # noqa: F821
        lazy="raise_on_sql"
    )
