"""Add booking exclusion constraint and master settings columns

Revision ID: 003_add_booking_exclusion_and_master_settings
Revises: 002_enable_rls
Create Date: 2026-03-17
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_add_booking_exclusion_and_master_settings"
down_revision: Union[str, None] = "002_enable_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add master settings and tg_user_id columns
    op.add_column(
        "masters",
        sa.Column(
            "tg_user_id",
            sa.String(100),
            unique=True,
            index=True,
            nullable=True,
        ),
    )
    op.add_column(
        "masters",
        sa.Column(
            "buffer_minutes",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "masters",
        sa.Column(
            "cancellation_deadline_hours",
            sa.Integer,
            nullable=False,
            server_default=sa.text("24"),
        ),
    )
    op.add_column(
        "masters",
        sa.Column(
            "slot_interval_minutes",
            sa.Integer,
            nullable=False,
            server_default=sa.text("30"),
        ),
    )

    # 2. Enable btree_gist extension for exclusion constraints
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # 3. Add booking_range generated column (tstzrange from starts_at to ends_at)
    op.execute(
        "ALTER TABLE bookings ADD COLUMN booking_range tstzrange "
        "GENERATED ALWAYS AS (tstzrange(starts_at, ends_at, '[)')) STORED"
    )

    # 4. Add exclusion constraint: prevent overlapping bookings for the same master
    # Note: cancelled bookings are filtered at application level via SELECT FOR UPDATE
    op.execute(
        "ALTER TABLE bookings ADD CONSTRAINT bookings_no_overlap "
        "EXCLUDE USING gist (master_id WITH =, booking_range WITH &&)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS bookings_no_overlap")
    op.execute("ALTER TABLE bookings DROP COLUMN IF EXISTS booking_range")
    op.execute("DROP EXTENSION IF EXISTS btree_gist")

    op.drop_column("masters", "slot_interval_minutes")
    op.drop_column("masters", "cancellation_deadline_hours")
    op.drop_column("masters", "buffer_minutes")
    op.drop_column("masters", "tg_user_id")
