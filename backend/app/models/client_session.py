import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ClientSession(Base):
    __tablename__ = "client_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
    )
    phone: Mapped[str] = mapped_column(String(20))
    token: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    otp_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    otp_attempts: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # Relationships -- lazy="raise_on_sql" prevents accidental lazy loads in async
    client: Mapped["Client"] = relationship(  # noqa: F821
        lazy="raise_on_sql"
    )
