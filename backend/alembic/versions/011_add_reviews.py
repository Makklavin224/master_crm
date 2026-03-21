"""Add reviews table with RLS

Revision ID: 011_add_reviews
Revises: 010_add_portfolio_photos
Create Date: 2026-03-21
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011_add_reviews"
down_revision: Union[str, None] = "010_add_portfolio_photos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "booking_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            unique=True,
            nullable=True,
        ),
        sa.Column(
            "master_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("masters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("text", sa.String(500), nullable=True),
        sa.Column("master_reply", sa.String(500), nullable=True),
        sa.Column(
            "master_replied_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'published'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )

    op.create_index(
        "ix_reviews_master_id",
        "reviews",
        ["master_id"],
    )

    # Enable RLS with NULLIF pattern (from 008)
    op.execute("ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE reviews FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY reviews_master_isolation ON reviews "
        "USING (master_id = NULLIF(current_setting('app.current_master_id', true), '')::uuid);"
    )

    # Grant permissions to app_user
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON reviews TO app_user;"
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS reviews_master_isolation ON reviews;"
    )
    op.execute("ALTER TABLE reviews DISABLE ROW LEVEL SECURITY;")
    op.drop_index("ix_reviews_master_id", table_name="reviews")
    op.drop_table("reviews")
