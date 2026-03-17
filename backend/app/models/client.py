import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=datetime.now,
    )

    # Relationships
    platforms: Mapped[list["ClientPlatform"]] = relationship(
        back_populates="client", lazy="selectin"
    )
    bookings: Mapped[list["Booking"]] = relationship(  # noqa: F821
        back_populates="client", lazy="selectin"
    )


class ClientPlatform(Base):
    __tablename__ = "client_platforms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE")
    )
    platform: Mapped[str] = mapped_column(String(20))  # telegram, max, vk
    platform_user_id: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        UniqueConstraint("client_id", "platform", name="uq_client_platforms_client_platform"),
    )

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="platforms")


class MasterClient(Base):
    __tablename__ = "master_clients"

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
    first_visit_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    last_visit_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    visit_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        UniqueConstraint("master_id", "client_id", name="uq_master_clients_master_client"),
    )

    # Relationships
    master: Mapped["Master"] = relationship(  # noqa: F821
        back_populates="master_clients"
    )
    client: Mapped["Client"] = relationship()
