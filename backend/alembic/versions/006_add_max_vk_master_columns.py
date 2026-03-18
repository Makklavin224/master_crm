"""Add max_user_id and vk_user_id to masters

Revision ID: 006_add_max_vk_master_columns
Revises: 005_add_notification_columns_and_reminders
Create Date: 2026-03-18
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_add_max_vk_master_columns"
down_revision: Union[str, None] = "005_add_notification_columns_and_reminders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add MAX user ID column
    op.add_column(
        "masters",
        sa.Column("max_user_id", sa.String(100), nullable=True),
    )
    op.create_index(
        "ix_masters_max_user_id", "masters", ["max_user_id"], unique=True
    )

    # Add VK user ID column
    op.add_column(
        "masters",
        sa.Column("vk_user_id", sa.String(100), nullable=True),
    )
    op.create_index(
        "ix_masters_vk_user_id", "masters", ["vk_user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_masters_vk_user_id", table_name="masters")
    op.drop_column("masters", "vk_user_id")
    op.drop_index("ix_masters_max_user_id", table_name="masters")
    op.drop_column("masters", "max_user_id")
