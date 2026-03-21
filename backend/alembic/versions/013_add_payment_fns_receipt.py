"""Add FNS receipt tracking columns to payments

Revision ID: 013_add_payment_fns_receipt
Revises: 012_add_client_sessions
Create Date: 2026-03-21
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013_add_payment_fns_receipt"
down_revision: Union[str, None] = "012_add_client_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column("fns_receipt_url", sa.String(500), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column(
            "fns_receipt_attempts",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("payments", "fns_receipt_attempts")
    op.drop_column("payments", "fns_receipt_url")
