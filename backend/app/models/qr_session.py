"""QR and Magic Link authentication sessions.

Short-lived sessions for QR code login and magic link login flows.
These are pre-auth sessions (no master_id scoping / RLS needed).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class QrSession(Base):
    __tablename__ = "qr_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_type: Mapped[str] = mapped_column(
        String(20)
    )  # 'qr' or 'magic_link'
    master_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # Set on confirm (QR) or creation (magic link)
    token: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )  # Unique session token
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, confirmed, expired, used
    access_token: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JWT set on confirm
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
