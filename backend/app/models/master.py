import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, text
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

    # Telegram integration
    tg_user_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True
    )

    # Phase 5: Multi-messenger integration
    max_user_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True
    )
    vk_user_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True
    )

    # Booking settings
    buffer_minutes: Mapped[int] = mapped_column(Integer, default=0)
    cancellation_deadline_hours: Mapped[int] = mapped_column(
        Integer, default=24
    )
    slot_interval_minutes: Mapped[int] = mapped_column(Integer, default=30)

    # Phase 3: Payment requisites
    card_number: Mapped[str | None] = mapped_column(
        String(20)
    )  # for manual payment QR
    sbp_phone: Mapped[str | None] = mapped_column(
        String(20)
    )  # SBP phone number
    bank_name: Mapped[str | None] = mapped_column(
        String(100)
    )  # bank name for display

    # Phase 3: Robokassa credentials (encrypted)
    robokassa_merchant_login: Mapped[str | None] = mapped_column(String(255))
    robokassa_password1_encrypted: Mapped[str | None] = mapped_column(
        Text
    )  # Fernet encrypted
    robokassa_password2_encrypted: Mapped[str | None] = mapped_column(
        Text
    )  # Fernet encrypted
    robokassa_is_test: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    robokassa_hash_algorithm: Mapped[str] = mapped_column(
        String(10), default="sha256", server_default=text("'sha256'")
    )

    # Phase 3: Fiscalization settings
    fiscalization_level: Mapped[str] = mapped_column(
        String(20), default="none", server_default=text("'none'")
    )  # none, manual, auto
    has_seen_grey_warning: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    receipt_sno: Mapped[str] = mapped_column(
        String(30), default="patent", server_default=text("'patent'")
    )

    # Phase 4: Notification settings
    reminders_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )
    reminder_1_hours: Mapped[int] = mapped_column(
        Integer, default=24, server_default=text("24")
    )
    reminder_2_hours: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=2, server_default=text("2")
    )
    address_note: Mapped[str | None] = mapped_column(Text, nullable=True)

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
