import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("masters.id", ondelete="CASCADE"),
        index=True,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE")
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE")
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(20), default="confirmed"
    )  # confirmed, completed, cancelled_by_client, cancelled_by_master, no_show
    source_platform: Mapped[str | None] = mapped_column(
        String(20)
    )  # telegram, max, vk, web
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=datetime.now,
    )

    # Relationships
    master: Mapped["Master"] = relationship(  # noqa: F821
        back_populates="bookings"
    )
    client: Mapped["Client"] = relationship(  # noqa: F821
        back_populates="bookings"
    )
    service: Mapped["Service"] = relationship()  # noqa: F821
    payment: Mapped["Payment | None"] = relationship(  # noqa: F821
        back_populates="booking", uselist=False
    )
