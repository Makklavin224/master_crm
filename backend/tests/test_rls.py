import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Master, Service


class TestRLSIsolation:
    async def test_rls_blocks_cross_tenant_read(
        self, db_session: AsyncSession
    ):
        """Master A's services are invisible to Master B's RLS context."""
        # Create two masters (masters table is NOT RLS-protected)
        master_a = Master(
            email="a@test.com", name="Master A", hashed_password="hash"
        )
        master_b = Master(
            email="b@test.com", name="Master B", hashed_password="hash"
        )
        db_session.add_all([master_a, master_b])
        await db_session.flush()

        # Create a service for Master A
        await db_session.execute(
            text("SET LOCAL app.current_master_id = :mid"),
            {"mid": str(master_a.id)},
        )
        service = Service(
            master_id=master_a.id,
            name="Haircut",
            duration_minutes=60,
            price=150000,
        )
        db_session.add(service)
        await db_session.flush()

        # Switch RLS context to Master B
        await db_session.execute(
            text("SET LOCAL app.current_master_id = :mid"),
            {"mid": str(master_b.id)},
        )

        # Master B should see zero services (RLS filters out Master A's service)
        result = await db_session.execute(select(Service))
        services = result.scalars().all()
        assert len(services) == 0, (
            f"RLS failed: Master B sees {len(services)} services "
            "that belong to Master A"
        )

    async def test_rls_allows_own_tenant_read(
        self, db_session: AsyncSession
    ):
        """Master A can see their own services."""
        master_a = Master(
            email="own@test.com", name="Master Own", hashed_password="hash"
        )
        db_session.add(master_a)
        await db_session.flush()

        await db_session.execute(
            text("SET LOCAL app.current_master_id = :mid"),
            {"mid": str(master_a.id)},
        )
        service = Service(
            master_id=master_a.id,
            name="Manicure",
            duration_minutes=45,
            price=200000,
        )
        db_session.add(service)
        await db_session.flush()

        result = await db_session.execute(select(Service))
        services = result.scalars().all()
        assert len(services) == 1
        assert services[0].name == "Manicure"

    async def test_rls_no_context_returns_nothing(
        self, db_session: AsyncSession
    ):
        """Without RLS context set, queries return no rows (fail closed)."""
        master = Master(
            email="nocontext@test.com",
            name="Master NC",
            hashed_password="hash",
        )
        db_session.add(master)
        await db_session.flush()

        # Set context to create the service
        await db_session.execute(
            text("SET LOCAL app.current_master_id = :mid"),
            {"mid": str(master.id)},
        )
        service = Service(
            master_id=master.id,
            name="Pedicure",
            duration_minutes=60,
            price=250000,
        )
        db_session.add(service)
        await db_session.flush()

        # Reset context (simulate no auth)
        await db_session.execute(text("RESET app.current_master_id"))

        result = await db_session.execute(select(Service))
        services = result.scalars().all()
        assert len(services) == 0, (
            "RLS should return nothing when no context is set (fail closed)"
        )
