"""Add notification settings columns and scheduled_reminders table

Revision ID: 005_add_notification_columns_and_reminders
Revises: 004_add_payment_and_settings_columns
Create Date: 2026-03-18
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_add_notification_columns_and_reminders"
down_revision: Union[str, None] = "004_add_payment_and_settings_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Master notification settings columns
    op.add_column(
        "masters",
        sa.Column(
            "reminders_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "masters",
        sa.Column(
            "reminder_1_hours",
            sa.Integer,
            nullable=False,
            server_default=sa.text("24"),
        ),
    )
    op.add_column(
        "masters",
        sa.Column(
            "reminder_2_hours",
            sa.Integer,
            nullable=True,
            server_default=sa.text("2"),
        ),
    )
    op.add_column(
        "masters",
        sa.Column("address_note", sa.Text, nullable=True),
    )

    # 2. Create scheduled_reminders table
    op.create_table(
        "scheduled_reminders",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "booking_id",
            sa.UUID(),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "master_id",
            sa.UUID(),
            sa.ForeignKey("masters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reminder_type", sa.String(20), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "booking_id",
            "reminder_type",
            name="uq_scheduled_reminders_booking_type",
        ),
    )

    # 3. Indexes
    op.create_index(
        "ix_scheduled_reminders_booking_id",
        "scheduled_reminders",
        ["booking_id"],
    )
    op.create_index(
        "ix_scheduled_reminders_master_id",
        "scheduled_reminders",
        ["master_id"],
    )

    # 4. RLS on scheduled_reminders
    op.execute(
        "ALTER TABLE scheduled_reminders ENABLE ROW LEVEL SECURITY"
    )
    op.execute(
        "ALTER TABLE scheduled_reminders FORCE ROW LEVEL SECURITY"
    )
    op.execute(
        "CREATE POLICY scheduled_reminders_master_isolation "
        "ON scheduled_reminders "
        "USING (master_id = current_setting("
        "'app.current_master_id', true)::uuid)"
    )

    # 5. Grant permissions to app_user
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE "
        "ON scheduled_reminders TO app_user"
    )


def downgrade() -> None:
    op.drop_table("scheduled_reminders")

    op.drop_column("masters", "address_note")
    op.drop_column("masters", "reminder_2_hours")
    op.drop_column("masters", "reminder_1_hours")
    op.drop_column("masters", "reminders_enabled")
