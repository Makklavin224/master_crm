"""Fix RLS policies to handle empty string from current_setting

Revision ID: 008_fix_rls_empty_string
Revises: 007_add_qr_sessions_table
"""

from typing import Sequence, Union

from alembic import op

revision: str = "008_fix_rls_empty_string"
down_revision: Union[str, None] = "007_add_qr_sessions_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RLS_TABLES = [
    "services",
    "bookings",
    "payments",
    "master_schedules",
    "schedule_exceptions",
    "master_clients",
]


def upgrade() -> None:
    for table in RLS_TABLES:
        # Drop old policy
        op.execute(f"DROP POLICY IF EXISTS {table}_master_isolation ON {table};")
        # Create new policy that handles empty string gracefully
        # NULLIF converts '' to NULL, and NULL::uuid doesn't crash
        op.execute(
            f"CREATE POLICY {table}_master_isolation ON {table} "
            f"USING (master_id = NULLIF(current_setting('app.current_master_id', true), '')::uuid);"
        )


def downgrade() -> None:
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_master_isolation ON {table};")
        op.execute(
            f"CREATE POLICY {table}_master_isolation ON {table} "
            f"USING (master_id = current_setting('app.current_master_id', true)::uuid);"
        )
