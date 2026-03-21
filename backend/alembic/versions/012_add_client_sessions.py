"""Add client_sessions table for client cabinet auth

Revision ID: 012_add_client_sessions
Revises: 011_add_reviews
Create Date: 2026-03-21
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012_add_client_sessions"
down_revision: Union[str, None] = "011_add_reviews"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_sessions",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "client_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # Unique index on token for fast lookups
    op.create_index(
        "ix_client_sessions_token",
        "client_sessions",
        ["token"],
        unique=True,
    )

    # NO RLS on client_sessions -- clients span masters


def downgrade() -> None:
    op.drop_index("ix_client_sessions_token", table_name="client_sessions")
    op.drop_table("client_sessions")
