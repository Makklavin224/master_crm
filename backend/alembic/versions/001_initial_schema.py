"""Initial schema - all domain tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-03-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Masters table
    op.create_table(
        "masters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=True),
        sa.Column("phone", sa.String(20), unique=True, index=True, nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("business_name", sa.String(255), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Europe/Moscow"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Clients table
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone", sa.String(20), unique=True, index=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Client platforms table
    op.create_table(
        "client_platforms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("platform_user_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("client_id", "platform", name="uq_client_platforms_client_platform"),
    )

    # Master-Client join table
    op.create_table(
        "master_clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_visit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_visit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("visit_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("master_id", "client_id", name="uq_master_clients_master_client"),
    )

    # Services table
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=False),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Bookings table
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="confirmed"),
        sa.Column("source_platform", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Payments table
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("payment_method", sa.String(20), nullable=True),
        sa.Column("robokassa_invoice_id", sa.String(255), nullable=True),
        sa.Column("receipt_status", sa.String(20), nullable=False, server_default="not_applicable"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Master schedules table
    op.create_table(
        "master_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("day_of_week", sa.Integer, nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("break_start", sa.Time, nullable=True),
        sa.Column("break_end", sa.Time, nullable=True),
        sa.Column("is_working", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("master_id", "day_of_week", name="uq_master_schedules_master_day"),
    )

    # Schedule exceptions table
    op.create_table(
        "schedule_exceptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("exception_date", sa.Date, nullable=False),
        sa.Column("is_day_off", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("start_time", sa.Time, nullable=True),
        sa.Column("end_time", sa.Time, nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("master_id", "exception_date", name="uq_schedule_exceptions_master_date"),
    )


def downgrade() -> None:
    op.drop_table("schedule_exceptions")
    op.drop_table("master_schedules")
    op.drop_table("payments")
    op.drop_table("bookings")
    op.drop_table("services")
    op.drop_table("master_clients")
    op.drop_table("client_platforms")
    op.drop_table("clients")
    op.drop_table("masters")
