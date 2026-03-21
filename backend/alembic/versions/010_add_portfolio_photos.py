"""Add portfolio_photos table with RLS

Revision ID: 010_add_portfolio_photos
Revises: 009_add_master_profile_fields
Create Date: 2026-03-21
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010_add_portfolio_photos"
down_revision: Union[str, None] = "009_add_master_profile_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolio_photos",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "master_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("masters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("thumbnail_path", sa.String(500), nullable=False),
        sa.Column("caption", sa.String(255), nullable=True),
        sa.Column("service_tag", sa.String(255), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.create_index(
        "ix_portfolio_photos_master_id",
        "portfolio_photos",
        ["master_id"],
    )

    # Enable RLS with NULLIF pattern (from 008)
    op.execute("ALTER TABLE portfolio_photos ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE portfolio_photos FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY portfolio_photos_master_isolation ON portfolio_photos "
        "USING (master_id = NULLIF(current_setting('app.current_master_id', true), '')::uuid);"
    )

    # Grant permissions to app_user
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON portfolio_photos TO app_user;"
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS portfolio_photos_master_isolation ON portfolio_photos;"
    )
    op.execute("ALTER TABLE portfolio_photos DISABLE ROW LEVEL SECURITY;")
    op.drop_index("ix_portfolio_photos_master_id", table_name="portfolio_photos")
    op.drop_table("portfolio_photos")
