import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("masters.id", ondelete="CASCADE"),
        index=True,
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE")
    )
    amount: Mapped[int] = mapped_column(Integer)  # in kopecks
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, paid, cancelled, refunded
    payment_method: Mapped[str | None] = mapped_column(
        String(20)
    )  # cash, card_to_card, sbp_robokassa, sbp, transfer
    robokassa_invoice_id: Mapped[str | None] = mapped_column(String(255))
    receipt_status: Mapped[str] = mapped_column(
        String(20), default="not_applicable"
    )  # not_applicable, pending, issued, failed, cancelled
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Phase 3: Payment extensions
    robokassa_inv_id: Mapped[int | None] = mapped_column(
        Integer, unique=True
    )  # integer InvId for Robokassa
    fiscalization_level: Mapped[str | None] = mapped_column(
        String(20)
    )  # per-payment override: none, manual, auto
    receipt_data: Mapped[str | None] = mapped_column(
        Text
    )  # JSON receipt data for manual mode
    receipt_id: Mapped[str | None] = mapped_column(
        String(255)
    )  # Robokassa receipt ID
    payment_url: Mapped[str | None] = mapped_column(
        Text
    )  # Robokassa payment URL

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=datetime.now,
    )

    # Relationships -- lazy="raise_on_sql" prevents accidental lazy loads in async
    booking: Mapped["Booking"] = relationship(  # noqa: F821
        back_populates="payment", lazy="raise_on_sql"
    )
