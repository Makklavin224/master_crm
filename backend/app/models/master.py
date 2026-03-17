import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Master(Base):
    __tablename__ = "masters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, index=True
    )
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    business_name: Mapped[str | None] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(
        String(50), default="Europe/Moscow"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=datetime.now,
    )

    # Relationships
    services: Mapped[list["Service"]] = relationship(  # noqa: F821
        back_populates="master", lazy="selectin"
    )
    bookings: Mapped[list["Booking"]] = relationship(  # noqa: F821
        back_populates="master", lazy="selectin"
    )
    schedules: Mapped[list["MasterSchedule"]] = relationship(  # noqa: F821
        back_populates="master", lazy="selectin"
    )
    master_clients: Mapped[list["MasterClient"]] = relationship(  # noqa: F821
        back_populates="master", lazy="selectin"
    )
