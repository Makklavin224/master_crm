"""Add qr_sessions table for QR code and magic link login flows.

Revision ID: 007
Revises: 006
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "qr_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_type", sa.String(20), nullable=False),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qr_sessions")),
        sa.UniqueConstraint("token", name=op.f("uq_qr_sessions_token")),
    )
    op.create_index(op.f("ix_qr_sessions_token"), "qr_sessions", ["token"])


def downgrade() -> None:
    op.drop_index(op.f("ix_qr_sessions_token"), table_name="qr_sessions")
    op.drop_table("qr_sessions")
