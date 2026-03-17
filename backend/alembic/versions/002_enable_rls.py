"""Enable Row-Level Security on tenant-scoped tables

Revision ID: 002_enable_rls
Revises: 001_initial_schema
Create Date: 2026-03-17
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_enable_rls"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables with master_id that need RLS policies
RLS_TABLES = [
    "services",
    "bookings",
    "payments",
    "master_schedules",
    "schedule_exceptions",
    "master_clients",
]


def upgrade() -> None:
    # Grant permissions to app_user role
    op.execute("GRANT USAGE ON SCHEMA public TO app_user;")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE mastercrm_owner IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;"
    )
    op.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;")
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE mastercrm_owner IN SCHEMA public "
        "GRANT USAGE ON SEQUENCES TO app_user;"
    )

    # Enable RLS on tenant-scoped tables
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        # Policy uses current_setting with true parameter: returns NULL when
        # setting is missing instead of throwing an error (fail closed --
        # queries return no rows when context is not set)
        op.execute(
            f"CREATE POLICY {table}_master_isolation ON {table} "
            f"USING (master_id = current_setting('app.current_master_id', true)::uuid);"
        )


def downgrade() -> None:
    for table in RLS_TABLES:
        op.execute(
            f"DROP POLICY IF EXISTS {table}_master_isolation ON {table};"
        )
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE mastercrm_owner IN SCHEMA public "
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM app_user;"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES FOR ROLE mastercrm_owner IN SCHEMA public "
        "REVOKE USAGE ON SEQUENCES FROM app_user;"
    )
    op.execute(
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM app_user;"
    )
    op.execute("REVOKE USAGE ON SCHEMA public FROM app_user;")
