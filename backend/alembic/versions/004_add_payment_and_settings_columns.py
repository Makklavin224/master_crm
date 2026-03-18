"""Add payment extensions and master payment settings columns

Revision ID: 004_add_payment_and_settings_columns
Revises: 003_add_booking_exclusion_and_master_settings
Create Date: 2026-03-18
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_payment_and_settings_columns"
down_revision: Union[str, None] = "003_add_booking_exclusion_and_master_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Payment model extensions
    op.add_column(
        "payments",
        sa.Column("robokassa_inv_id", sa.Integer, unique=True, nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("fiscalization_level", sa.String(20), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("receipt_data", sa.Text, nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("receipt_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("payment_url", sa.Text, nullable=True),
    )

    # 2. Master payment requisites
    op.add_column(
        "masters",
        sa.Column("card_number", sa.String(20), nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column("sbp_phone", sa.String(20), nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column("bank_name", sa.String(100), nullable=True),
    )

    # 3. Master Robokassa credentials
    op.add_column(
        "masters",
        sa.Column("robokassa_merchant_login", sa.String(255), nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column("robokassa_password1_encrypted", sa.Text, nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column("robokassa_password2_encrypted", sa.Text, nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column(
            "robokassa_is_test",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "masters",
        sa.Column(
            "robokassa_hash_algorithm",
            sa.String(10),
            nullable=False,
            server_default=sa.text("'sha256'"),
        ),
    )

    # 4. Master fiscalization settings
    op.add_column(
        "masters",
        sa.Column(
            "fiscalization_level",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'none'"),
        ),
    )
    op.add_column(
        "masters",
        sa.Column(
            "has_seen_grey_warning",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "masters",
        sa.Column(
            "receipt_sno",
            sa.String(30),
            nullable=False,
            server_default=sa.text("'patent'"),
        ),
    )

    # 5. Composite index for payment history queries
    op.create_index(
        "ix_payments_master_id_created_at",
        "payments",
        ["master_id", "created_at"],
    )

    # 6. Sequence for Robokassa InvId generation
    op.execute("CREATE SEQUENCE IF NOT EXISTS robokassa_inv_id_seq")


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS robokassa_inv_id_seq")

    op.drop_index("ix_payments_master_id_created_at", table_name="payments")

    # Master fiscalization settings
    op.drop_column("masters", "receipt_sno")
    op.drop_column("masters", "has_seen_grey_warning")
    op.drop_column("masters", "fiscalization_level")

    # Master Robokassa credentials
    op.drop_column("masters", "robokassa_hash_algorithm")
    op.drop_column("masters", "robokassa_is_test")
    op.drop_column("masters", "robokassa_password2_encrypted")
    op.drop_column("masters", "robokassa_password1_encrypted")
    op.drop_column("masters", "robokassa_merchant_login")

    # Master payment requisites
    op.drop_column("masters", "bank_name")
    op.drop_column("masters", "sbp_phone")
    op.drop_column("masters", "card_number")

    # Payment extensions
    op.drop_column("payments", "payment_url")
    op.drop_column("payments", "receipt_id")
    op.drop_column("payments", "receipt_data")
    op.drop_column("payments", "fiscalization_level")
    op.drop_column("payments", "robokassa_inv_id")
