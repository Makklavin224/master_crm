"""Add master profile and FNS fields for v2.0

Revision ID: 009_add_master_profile_fields
Revises: 008_fix_rls_empty_string
Create Date: 2026-03-21
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009_add_master_profile_fields"
down_revision: Union[str, None] = "008_fix_rls_empty_string"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Public profile fields
    op.add_column(
        "masters",
        sa.Column("username", sa.String(30), nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column("specialization", sa.String(255), nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column("city", sa.String(255), nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column("avatar_path", sa.String(500), nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column("instagram_url", sa.String(500), nullable=True),
    )

    # FNS / tax receipt fields
    op.add_column(
        "masters",
        sa.Column("inn", sa.String(12), nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column("fns_token_encrypted", sa.Text, nullable=True),
    )
    op.add_column(
        "masters",
        sa.Column(
            "fns_connected",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # Unique index on username
    op.create_index(
        "ix_masters_username", "masters", ["username"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_masters_username", table_name="masters")

    op.drop_column("masters", "fns_connected")
    op.drop_column("masters", "fns_token_encrypted")
    op.drop_column("masters", "inn")
    op.drop_column("masters", "instagram_url")
    op.drop_column("masters", "avatar_path")
    op.drop_column("masters", "city")
    op.drop_column("masters", "specialization")
    op.drop_column("masters", "username")
