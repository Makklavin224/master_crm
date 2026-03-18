import asyncio
import uuid
from datetime import datetime, time, timedelta
from typing import AsyncGenerator
from zoneinfo import ZoneInfo

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models import Base, Booking, Master, MasterSchedule, Service
from app.models.client import Client, ClientPlatform, MasterClient

# Test database URLs: use the owner role for DDL (create tables, RLS policies)
# and the app role for DML (actual test queries with RLS enforced).
# Replace the database name to use a separate test database.
# The test database must be created beforehand:
#   docker compose exec db psql -U mastercrm_owner -c "CREATE DATABASE mastercrm_test;"
#   docker compose exec db psql -U mastercrm_owner -d mastercrm_test \
#     -c "GRANT ALL ON DATABASE mastercrm_test TO app_user;"
TEST_DATABASE_URL = settings.database_url.replace(
    "/mastercrm", "/mastercrm_test"
)
TEST_APP_DATABASE_URL = settings.database_app_url.replace(
    "/mastercrm", "/mastercrm_test"
)

# Lazy-initialized engines (only created when DB tests actually run)
_test_engine = None
_test_app_engine = None
_test_session_factory = None


def _get_test_engine():
    global _test_engine
    if _test_engine is None:
        _test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    return _test_engine


def _get_test_app_engine():
    global _test_app_engine
    if _test_app_engine is None:
        _test_app_engine = create_async_engine(
            TEST_APP_DATABASE_URL, echo=False
        )
    return _test_app_engine


def _get_test_session_factory():
    global _test_session_factory
    if _test_session_factory is None:
        _test_session_factory = async_sessionmaker(
            _get_test_app_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _test_session_factory


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


_db_initialized = False


async def _ensure_test_db():
    """Create test database tables once (idempotent)."""
    global _db_initialized
    if _db_initialized:
        return
    engine = _get_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # Grant permissions to app_user on test tables
        await conn.execute(
            text(
                "GRANT SELECT, INSERT, UPDATE, DELETE "
                "ON ALL TABLES IN SCHEMA public TO app_user"
            )
        )
        await conn.execute(
            text("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user")
        )
        # Enable RLS on tenant-scoped tables
        rls_tables = [
            "services",
            "bookings",
            "payments",
            "master_schedules",
            "schedule_exceptions",
            "master_clients",
            "scheduled_reminders",
        ]
        for table in rls_tables:
            await conn.execute(
                text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            )
            await conn.execute(
                text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
            )
            await conn.execute(
                text(
                    f"CREATE POLICY IF NOT EXISTS {table}_master_isolation "
                    f"ON {table} "
                    f"USING (master_id = current_setting("
                    f"'app.current_master_id', true)::uuid)"
                )
            )
    _db_initialized = True


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test.
    Automatically initializes the test database on first use."""
    await _ensure_test_db()
    async with _get_test_session_factory()() as session:
        yield session
        await session.rollback()


@pytest.fixture
def app():
    """Create a fresh app instance (no DB override -- used by non-DB tests)."""
    return create_app()


@pytest.fixture
def app_with_db(db_session):
    """Create app with test DB session override (used by DB-dependent tests)."""
    application = create_app()

    async def override_get_db():
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest.fixture
async def simple_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Lightweight async HTTP client (no DB -- for health/smoke tests)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def client(app_with_db) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing (uses DB-backed app)."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def master_factory(db_session):
    """Factory to create test masters directly in the database."""

    async def _create(
        email: str | None = None,
        name: str = "Test Master",
        password: str = "testpass123",
    ) -> Master:
        if email is None:
            email = f"test-{uuid.uuid4().hex[:8]}@example.com"
        master = Master(
            email=email,
            hashed_password=hash_password(password),
            name=name,
        )
        db_session.add(master)
        await db_session.flush()
        return master

    return _create


@pytest.fixture
async def auth_headers(master_factory):
    """Create a master and return auth headers with valid JWT."""
    master = await master_factory()
    token = create_access_token(data={"sub": str(master.id)})
    return {"Authorization": f"Bearer {token}"}, master


@pytest.fixture
async def service_factory(db_session):
    """Factory to create test services directly in the database."""

    async def _create(
        master_id: uuid.UUID,
        name: str = "Test Service",
        duration_minutes: int = 60,
        price: int = 250000,
        category: str | None = "General",
    ) -> Service:
        service = Service(
            master_id=master_id,
            name=name,
            duration_minutes=duration_minutes,
            price=price,
            category=category,
        )
        db_session.add(service)
        await db_session.flush()
        return service

    return _create


@pytest.fixture
async def schedule_factory(db_session):
    """Factory to create a 7-day weekly schedule for a master."""

    async def _create(
        master_id: uuid.UUID,
        start_time: time = time(9, 0),
        end_time: time = time(18, 0),
        break_start: time | None = time(13, 0),
        break_end: time | None = time(14, 0),
        working_days: list[int] | None = None,
    ) -> list[MasterSchedule]:
        if working_days is None:
            working_days = [0, 1, 2, 3, 4]  # Mon-Fri

        schedules = []
        for day in range(7):
            sched = MasterSchedule(
                master_id=master_id,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                break_start=break_start if day in working_days else None,
                break_end=break_end if day in working_days else None,
                is_working=day in working_days,
            )
            db_session.add(sched)
            schedules.append(sched)

        await db_session.flush()
        return schedules

    return _create


@pytest.fixture
async def booking_factory(db_session):
    """Factory to create test bookings directly in the database."""

    async def _create(
        master_id: uuid.UUID,
        service_id: uuid.UUID,
        client_id: uuid.UUID,
        starts_at: datetime | None = None,
        duration_minutes: int = 60,
        status: str = "confirmed",
    ) -> Booking:
        if starts_at is None:
            tz = ZoneInfo("Europe/Moscow")
            starts_at = datetime.now(tz) + timedelta(days=1)

        ends_at = starts_at + timedelta(minutes=duration_minutes)

        booking = Booking(
            master_id=master_id,
            service_id=service_id,
            client_id=client_id,
            starts_at=starts_at,
            ends_at=ends_at,
            status=status,
            source_platform="telegram",
        )
        db_session.add(booking)
        await db_session.flush()
        return booking

    return _create


@pytest.fixture
async def client_factory(db_session):
    """Factory to create test clients directly in the database."""

    async def _create(
        phone: str | None = None,
        name: str = "Test Client",
    ) -> Client:
        if phone is None:
            phone = f"+7916{uuid.uuid4().hex[:7]}"
        client = Client(phone=phone, name=name)
        db_session.add(client)
        await db_session.flush()
        return client

    return _create


@pytest.fixture
async def client_platform_factory(db_session):
    """Factory to create test client platforms directly in the database."""

    async def _create(
        client_id: uuid.UUID,
        platform: str = "telegram",
        platform_user_id: str | None = None,
    ) -> ClientPlatform:
        if platform_user_id is None:
            platform_user_id = f"tg_{uuid.uuid4().hex[:8]}"
        cp = ClientPlatform(
            client_id=client_id,
            platform=platform,
            platform_user_id=platform_user_id,
        )
        db_session.add(cp)
        await db_session.flush()
        return cp

    return _create
