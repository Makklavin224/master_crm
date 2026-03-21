"""Add OTP columns to client_sessions for cabinet auth

Revision ID: 014_add_otp_columns_to_client_sessions
Revises: 013_add_payment_fns_receipt
Create Date: 2026-03-21
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "014_add_otp_columns_to_client_sessions"
down_revision: Union[str, None] = "013_add_payment_fns_receipt"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "client_sessions",
        sa.Column("otp_hash", sa.String(64), nullable=True),
    )
    op.add_column(
        "client_sessions",
        sa.Column(
            "otp_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "client_sessions",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("client_sessions", "is_verified")
    op.drop_column("client_sessions", "otp_attempts")
    op.drop_column("client_sessions", "otp_hash")
