# Phase 1: Foundation - Research

**Researched:** 2026-03-17
**Domain:** FastAPI backend scaffolding, PostgreSQL schema with RLS, JWT authentication, Docker Compose deployment
**Confidence:** HIGH

## Summary

Phase 1 establishes the entire backend foundation for a multi-messenger CRM: project scaffolding with FastAPI, PostgreSQL database schema covering all domain entities, master authentication via JWT, phone number normalization to E.164, and a Docker Compose stack (FastAPI + PostgreSQL + Caddy) that deploys with a single command.

The research uncovered two critical deprecations in the STACK.md recommendations: **python-jose is abandoned** (last release 2021, broken on Python >= 3.10) and **passlib is unmaintained** (last release 2020, breaks on Python 3.13). FastAPI's official documentation now recommends **PyJWT** + **pwdlib[argon2]** as replacements. These substitutions are mandatory. Additionally, the `phonenumbers` library (Google's libphonenumber port) is the correct tool for E.164 normalization of Russian phone numbers, avoiding hand-rolled regex patterns.

The RLS (Row-Level Security) pattern for multi-tenant isolation is well-established: enable RLS on tables with `master_id`, create policies using `current_setting('app.current_master_id')`, and set the context per-request via `SET LOCAL` in a FastAPI dependency. The key requirement is using a dedicated unprivileged database role for the application (the table owner bypasses RLS by default).

**Primary recommendation:** Use `uv` for dependency management, `PyJWT` + `pwdlib[argon2]` for auth, `Alembic` with async template for migrations, `phonenumbers` library for E.164 normalization, and Caddy for automatic HTTPS. Create a separate PostgreSQL role (`app_user`) for the application connection so RLS policies are enforced.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Multiple auth methods: TG bot auth (primary), email+password (web panel fallback), QR code/magic link from bot for web panel quick login
- No SMS/OTP for now -- too expensive for pre-revenue stage. Can be added later.
- TG auth flow: master sends /start -> bot creates account -> JWT token issued
- Web panel: login via email+password OR scan QR from bot OR click magic link sent by bot
- MAX and VK bot auth follows same pattern as TG bot auth
- Clients don't register -- no accounts needed
- Client simply provides name + phone when making a booking
- Phone number is the identifier across messengers (E.164 normalization)
- Monorepo: backend/, frontend/, bots/ all in one repository
- Single `docker-compose.yml` at root for full stack
- Shared types/schemas between components
- All English: table names, API fields, variable names, comments
- Russian only in user-facing strings (UI text, bot messages, notifications)
- Everything in Docker for local dev: `docker compose up` starts full stack
- Docker Compose with hot-reload for backend (uvicorn --reload with volume mount)
- PostgreSQL in Docker container, persistent volume for data

### Claude's Discretion
- FastAPI project layout (routers, services, repositories pattern)
- Alembic vs raw SQL for migrations
- JWT implementation details (secret rotation, token expiry)
- Docker Compose service naming and networking
- Caddy vs nginx for reverse proxy
- Redis inclusion (if needed for sessions/cache)

### Deferred Ideas (OUT OF SCOPE)
- SMS OTP authentication -- deferred due to cost, add when revenue justifies it
- MAX/VK specific auth quirks -- will be addressed in Phase 5
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFR-01 | FastAPI backend with PostgreSQL, deployed in Docker Compose on VPS | Standard stack (FastAPI 0.135.1, PostgreSQL 16, SQLAlchemy 2.0.48, asyncpg 0.31.0) + Docker Compose with Caddy + Alembic for migrations |
| INFR-02 | REST API for mini-app and web panel | FastAPI routers with versioned API prefix (/api/v1/), Pydantic schemas for request/response validation, OpenAPI auto-generated docs |
| INFR-04 | Master authentication (registration/login via messenger) | PyJWT for tokens, pwdlib[argon2] for password hashing, OAuth2PasswordBearer scheme, FastAPI dependency injection for auth |
| INFR-05 | Multi-tenant isolation (master_id on all tables, PostgreSQL RLS) | RLS policies with current_setting('app.current_master_id'), SET LOCAL in FastAPI dependency, dedicated app_user PostgreSQL role |
| CLNT-02 | Client identified by phone number (E.164 normalization) | phonenumbers library (Google libphonenumber port) for parsing Russian numbers, E.164 unique constraint on clients table |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.1 | Web framework | Async-native, auto OpenAPI docs, Pydantic validation, dependency injection. Official release Mar 2026. |
| Pydantic | 2.12+ | Data validation | Core of FastAPI. V2 has 5-50x perf boost over V1. |
| pydantic-settings | 2.13.1 | Configuration from env | Loads .env files, env vars, Docker secrets. Type-safe config with validation. |
| SQLAlchemy | 2.0.48 | ORM + query builder | Async support via create_async_engine. Mature, battle-tested. Released Mar 2026. |
| asyncpg | 0.31.0 | PostgreSQL async driver | 5x faster than psycopg3. Native asyncio. Released Nov 2025. |
| Alembic | 1.18.4 | Database migrations | Only migration tool for SQLAlchemy. Async template for asyncpg. Released Feb 2026. |
| PostgreSQL | 16-alpine | Primary database | RLS support, TIMESTAMPTZ, exclusion constraints, JSONB. Docker image. |
| Uvicorn | 0.34+ | ASGI server | Standard production server for FastAPI. |
| Caddy | 2-alpine | Reverse proxy + HTTPS | Auto Let's Encrypt, 3-line config, HTTP/2+3. Docker image. |

### Authentication

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyJWT | 2.12.1 | JWT token encode/decode | **Replaces deprecated python-jose**. FastAPI official docs now use PyJWT. Released Mar 2026. |
| pwdlib[argon2] | 0.3.0 | Password hashing | **Replaces deprecated passlib**. FastAPI official docs now use pwdlib. Argon2 is OWASP-recommended. Released Oct 2025. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| phonenumbers | 9.0.26 | Phone normalization to E.164 | Every phone number input. Google's libphonenumber port. Handles Russian 8-prefix, +7, spaces, dashes. Released Mar 2026. |
| httpx | 0.28.1 | Async HTTP client for testing | FastAPI AsyncClient for tests. Also useful for external API calls. |
| pytest | latest | Test framework | Unit and integration tests. |
| pytest-asyncio | latest | Async test support | Running async test functions with pytest. |
| ruff | latest | Linter + formatter | Replaces flake8 + black + isort. Single tool. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyJWT | python-jose | python-jose is **abandoned** (last release 2021), broken on Python >= 3.10. Do NOT use. |
| pwdlib[argon2] | passlib[bcrypt] | passlib is **unmaintained** (last release 2020), breaks on Python 3.13. Do NOT use. |
| phonenumbers | Hand-rolled regex | Regex misses edge cases (Kazakhstan +7, double prefix, parentheses). phonenumbers handles all of them. |
| Alembic | Raw SQL migrations | Alembic auto-generates from model changes, tracks state, supports async. No reason to hand-roll. |
| Caddy | Nginx | Nginx requires manual certbot, 50+ lines config. Caddy does auto-HTTPS in 3 lines. |
| uv | pip/poetry | uv is 100x faster, resolves correctly, native lockfile. 2026 standard for Python projects. |

**Installation:**
```bash
# Initialize project with uv
uv init backend --python 3.12
cd backend

# Core dependencies
uv add "fastapi[standard]" uvicorn
uv add sqlalchemy[asyncio] asyncpg alembic
uv add pydantic pydantic-settings

# Authentication
uv add pyjwt "pwdlib[argon2]"

# Phone normalization
uv add phonenumbers

# Dev dependencies
uv add --dev pytest pytest-asyncio httpx ruff mypy
```

## Architecture Patterns

### Recommended Project Structure

```
master_crm/                      # Monorepo root
  docker-compose.yml             # Full stack: api + db + caddy
  docker-compose.override.yml    # Dev overrides (hot-reload, ports)
  Caddyfile                      # Reverse proxy config
  .env.example                   # Template for env vars
  backend/
    pyproject.toml               # uv project file
    uv.lock                      # Lockfile (committed)
    Dockerfile                   # Multi-stage build
    alembic.ini                  # Alembic config
    alembic/
      env.py                     # Async migration runner
      versions/                  # Migration files
    app/
      __init__.py
      main.py                    # FastAPI app factory
      core/
        __init__.py
        config.py                # pydantic-settings (Settings class)
        security.py              # JWT encode/decode, password hash
        database.py              # AsyncEngine, AsyncSession factory
        dependencies.py          # get_db, get_current_master, set_rls_context
      models/
        __init__.py
        base.py                  # DeclarativeBase with naming conventions
        master.py                # Master model
        client.py                # Client, ClientPlatform models
        service.py               # Service model
        booking.py               # Booking model
        payment.py               # Payment model
        schedule.py              # MasterSchedule, ScheduleException models
      schemas/
        __init__.py
        auth.py                  # TokenResponse, LoginRequest, RegisterRequest
        master.py                # MasterRead, MasterUpdate
        client.py                # ClientRead, ClientCreate
        common.py                # HealthResponse, PaginatedResponse
      api/
        __init__.py
        v1/
          __init__.py
          router.py              # Main v1 router (includes sub-routers)
          auth.py                # /auth/register, /auth/login, /auth/token
          health.py              # /health
      services/
        __init__.py
        auth_service.py          # Registration, login logic
        phone_service.py         # E.164 normalization
    tests/
      __init__.py
      conftest.py                # Async fixtures, test DB setup
      test_health.py             # Health endpoint test
      test_auth.py               # Auth flow tests
      test_phone.py              # Phone normalization tests
```

### Pattern 1: FastAPI App Factory

**What:** Create the FastAPI application in a factory function, not at module level. This allows test configuration overrides and clean startup/shutdown lifecycle.

**When:** Always. This is the entry point.

**Example:**
```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine
from app.api.v1.router import api_v1_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connection
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    # Shutdown: dispose engine
    await engine.dispose()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Master CRM API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_v1_router, prefix="/api/v1")
    return app

app = create_app()
```

### Pattern 2: Async Database Session with RLS Context

**What:** FastAPI dependency that creates an async SQLAlchemy session, sets the RLS tenant context via `SET LOCAL`, and ensures proper cleanup.

**When:** Every authenticated API endpoint that accesses tenant data.

**Example:**
```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# app/core/dependencies.py
from fastapi import Depends
from sqlalchemy import text

async def get_db():
    """Yield a database session, rollback on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_db_with_rls(
    session: AsyncSession = Depends(get_db),
    master: Master = Depends(get_current_master),
) -> AsyncSession:
    """Set RLS context for the current master."""
    await session.execute(
        text("SET LOCAL app.current_master_id = :master_id"),
        {"master_id": str(master.id)},
    )
    return session
```

### Pattern 3: Pydantic Settings Configuration

**What:** Single Settings class using pydantic-settings that loads from environment variables and .env files.

**When:** Application startup. Cached via `@lru_cache`.

**Example:**
```python
# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    debug: bool = False
    app_name: str = "Master CRM"

    # Database
    database_url: str  # postgresql+asyncpg://user:pass@host:5432/db
    db_echo: bool = False

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Caddy / Proxy
    allowed_origins: list[str] = ["http://localhost:3000"]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### Pattern 4: JWT Authentication with PyJWT + pwdlib

**What:** Official FastAPI authentication pattern using PyJWT for token encoding/decoding and pwdlib with Argon2 for password hashing.

**When:** Master registration, login, and all authenticated endpoints.

**Example:**
```python
# app/core/security.py
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from app.core.config import settings

password_hash = PasswordHash.recommended()  # Argon2
DUMMY_HASH = password_hash.hash("dummy")    # Timing attack prevention

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
```

### Pattern 5: E.164 Phone Normalization with phonenumbers

**What:** Normalize all phone numbers to E.164 format using Google's libphonenumber. Handles Russian 8-prefix, missing country code, spaces, dashes, parentheses.

**When:** Every time a phone number enters the system (registration, booking, client creation).

**Example:**
```python
# app/services/phone_service.py
import phonenumbers
from phonenumbers import NumberParseException

def normalize_phone(raw_phone: str, default_region: str = "RU") -> str | None:
    """
    Normalize a phone number to E.164 format.
    Returns None if the number is invalid.

    Examples:
      "89161234567"      -> "+79161234567"
      "+7 (916) 123-45-67" -> "+79161234567"
      "9161234567"       -> "+79161234567"
      "+79161234567"     -> "+79161234567"
    """
    try:
        parsed = phonenumbers.parse(raw_phone, default_region)
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
    except NumberParseException:
        return None
```

### Pattern 6: PostgreSQL RLS Setup

**What:** Row-Level Security policies that enforce tenant isolation at the database level. Defense-in-depth: even if application code misses a WHERE clause, the database blocks cross-tenant access.

**Critical requirement:** The application must connect as a non-owner role (`app_user`). Table owners bypass RLS by default.

**Example (Alembic migration):**
```python
# alembic/versions/xxxx_enable_rls.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create application role (if not exists)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
                CREATE ROLE app_user LOGIN PASSWORD 'changeme';
            END IF;
        END $$;
    """)

    # Grant permissions
    op.execute("GRANT USAGE ON SCHEMA public TO app_user;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;")
    op.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;")

    # Enable RLS on tenant-scoped tables
    for table in ['services', 'bookings', 'payments', 'master_schedules',
                   'schedule_exceptions', 'master_clients']:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY {table}_master_isolation ON {table}
                USING (master_id = current_setting('app.current_master_id', true)::uuid);
        """)

def downgrade():
    for table in ['services', 'bookings', 'payments', 'master_schedules',
                   'schedule_exceptions', 'master_clients']:
        op.execute(f"DROP POLICY IF EXISTS {table}_master_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
```

### Anti-Patterns to Avoid

- **Module-level app creation without factory:** Makes testing impossible without import side effects. Always use `create_app()`.
- **Sync SQLAlchemy with asyncpg:** Mixing `create_engine` (sync) with asyncpg driver causes hard-to-debug errors. Always use `create_async_engine`.
- **RLS on table owner role:** PostgreSQL table owners bypass RLS. The application must connect as a separate `app_user` role with `FORCE ROW LEVEL SECURITY` enabled.
- **Missing `current_setting('...', true)`:** The second argument `true` means return NULL if the setting is missing (instead of throwing an error). Without it, any query without RLS context set will crash instead of failing safely. Use `true` to fail closed (return no rows when context is missing).
- **Storing passwords with bcrypt via passlib:** Both passlib and python-jose are abandoned. Use pwdlib[argon2] and PyJWT as per current FastAPI official docs.
- **Hand-rolling phone normalization with regex:** Russian phone numbers have too many edge cases (8-prefix, +7 overlap with Kazakhstan, parentheses, double prefix). Use the `phonenumbers` library.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Phone normalization | Regex for +7/8 prefix stripping | `phonenumbers` library | Handles Kazakhstan +7 6xx/7xx, parentheses, double prefix, validation. 100+ countries. |
| Password hashing | Custom bcrypt/scrypt wrapper | `pwdlib[argon2]` | Argon2 is OWASP-recommended. pwdlib handles salt, timing attack prevention, hash upgrades. |
| JWT tokens | Manual base64 + HMAC | `PyJWT` | Handles expiration, algorithm validation, claim parsing, error types. |
| Database migrations | Hand-written SQL scripts | `Alembic` with async template | Auto-generates from model diffs, tracks migration state, supports downgrades, async-native. |
| Config management | os.environ.get() everywhere | `pydantic-settings` | Type validation, .env loading, Docker secrets, nested config, caching. |
| HTTPS certificates | Manual certbot + cron | `Caddy` | Auto-obtains and renews Let's Encrypt certs. Zero config. |

**Key insight:** Every "simple" hand-rolled solution in this domain has documented edge cases that cost days to debug. Phone normalization alone has 6+ Russian-specific quirks. JWT has timing attacks, algorithm confusion attacks, and expiration handling. Use proven libraries.

## Common Pitfalls

### Pitfall 1: RLS Bypassed by Table Owner
**What goes wrong:** RLS policies are enabled on tables, but the application connects as the PostgreSQL superuser or table owner role, which bypasses RLS entirely. All masters see all data.
**Why it happens:** Default Docker PostgreSQL setup uses `POSTGRES_USER` for everything. That user owns the tables and bypasses RLS.
**How to avoid:** Create a separate `app_user` role. Run migrations as the owner role, but the application connects as `app_user`. Use `ALTER TABLE ... FORCE ROW LEVEL SECURITY` to also force RLS on the table owner (belt-and-suspenders).
**Warning signs:** Queries return data from multiple masters when they should not.

### Pitfall 2: Missing SET LOCAL Before Queries
**What goes wrong:** The FastAPI dependency sets `app.current_master_id` but uses `SET` instead of `SET LOCAL`. The setting persists across connection pool reuse, leaking tenant context to the next request.
**Why it happens:** `SET` changes the session variable for the entire connection lifetime. With connection pooling (asyncpg pool), the connection is returned to the pool with the previous master's context.
**How to avoid:** Always use `SET LOCAL` which scopes the setting to the current transaction only. When the transaction commits/rollbacks, the setting is automatically cleared.
**Warning signs:** Intermittent data leaks, tenant A seeing tenant B's data after specific request sequences.

### Pitfall 3: Deprecated Auth Libraries
**What goes wrong:** Following old tutorials that use `python-jose` + `passlib`. These libraries crash on modern Python versions.
**Why it happens:** Most FastAPI tutorials pre-2025 use the old stack. Even some 2025 articles still reference them.
**How to avoid:** Use `PyJWT` 2.12.1 + `pwdlib[argon2]` 0.3.0 as per current FastAPI official documentation.
**Warning signs:** Import errors on Python 3.13+, deprecation warnings, security vulnerabilities in unmaintained code.

### Pitfall 4: Phone Normalization Not Applied at Boundary
**What goes wrong:** Phone numbers are stored as-is in some code paths, normalized in others. The same client gets two records: one as "+79161234567", another as "89161234567".
**Why it happens:** Normalization is done in some API endpoints but missed in bot handlers or import flows.
**How to avoid:** Create a Pydantic validator type (`PhoneNumber`) that auto-normalizes on creation. Use it in all schemas that accept phone numbers. The normalization happens at the Pydantic validation boundary, before any business logic.
**Warning signs:** Duplicate client records, phone uniqueness constraint violations after migration.

### Pitfall 5: Alembic Not Configured for Async
**What goes wrong:** Running `alembic init alembic` creates a sync `env.py`. Migrations fail with "cannot use async engine with sync migration context."
**Why it happens:** Default Alembic template is sync. The async template must be explicitly selected.
**How to avoid:** Initialize with `alembic init -t async alembic`. This generates an `env.py` that uses `async_engine_from_config` and `run_async_migrations`.
**Warning signs:** Migration commands hang or throw asyncio errors.

### Pitfall 6: Docker Compose Healthcheck Missing
**What goes wrong:** FastAPI container starts before PostgreSQL is ready. First requests fail with connection errors. Alembic migrations fail.
**Why it happens:** `depends_on` without `condition: service_healthy` only waits for the container to start, not for the service inside to be ready.
**How to avoid:** Add `healthcheck` to the PostgreSQL service and use `depends_on: db: condition: service_healthy` for the API service.
**Warning signs:** Intermittent startup failures, "connection refused" errors in first few seconds.

## Code Examples

### Caddyfile for Reverse Proxy
```
# Caddyfile (production)
{domain_name} {
    reverse_proxy api:8000
}

# Caddyfile (development - localhost, no HTTPS)
:80 {
    reverse_proxy api:8000
}
```
Source: [Caddy reverse proxy docs](https://caddyserver.com/docs/quick-starts/reverse-proxy)

### Docker Compose (Development)
```yaml
# docker-compose.yml
services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mastercrm
      POSTGRES_USER: mastercrm_owner
      POSTGRES_PASSWORD: ${DB_PASSWORD:-devpassword}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./backend/scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mastercrm_owner -d mastercrm"]
      interval: 5s
      timeout: 5s
      retries: 5

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    depends_on:
      - api

volumes:
  pgdata:
  caddy_data:
```

### PostgreSQL Init Script (Create app_user role)
```sql
-- backend/scripts/init-db.sql
-- Run on first DB initialization to create the application role
-- The owner role (mastercrm_owner) runs migrations; app_user runs the application

CREATE ROLE app_user LOGIN PASSWORD 'changeme_in_production';
GRANT CONNECT ON DATABASE mastercrm TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;

-- After migrations create tables, grant access:
-- (Run via Alembic migration or post-migration script)
-- ALTER DEFAULT PRIVILEGES FOR ROLE mastercrm_owner IN SCHEMA public
--   GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
-- ALTER DEFAULT PRIVILEGES FOR ROLE mastercrm_owner IN SCHEMA public
--   GRANT USAGE ON SEQUENCES TO app_user;
```

### Dockerfile (Multi-stage with uv)
```dockerfile
# backend/Dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

WORKDIR /app

# Install dependencies first (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .
RUN uv sync --frozen --no-dev

# Production stage
FROM base AS production
EXPOSE 8000
CMD ["uv", "run", "gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### SQLAlchemy Base Model with Naming Conventions
```python
# app/models/base.py
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Alembic-friendly naming conventions for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)
```
Source: [Alembic naming conventions docs](https://alembic.sqlalchemy.org/en/latest/naming.html)

### Master Model Example
```python
# app/models/master.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Master(Base):
    __tablename__ = "masters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    business_name: Mapped[str | None] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Moscow")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
```

### Pydantic Validator Type for Phone Numbers
```python
# app/schemas/common.py
from typing import Annotated
from pydantic import AfterValidator
from app.services.phone_service import normalize_phone

def validate_phone(v: str) -> str:
    normalized = normalize_phone(v)
    if normalized is None:
        raise ValueError(f"Invalid phone number: {v}")
    return normalized

PhoneNumber = Annotated[str, AfterValidator(validate_phone)]

# Usage in schemas:
# class ClientCreate(BaseModel):
#     name: str
#     phone: PhoneNumber  # Auto-normalizes to E.164
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose for JWT | PyJWT 2.12.1 | 2025 (FastAPI docs updated) | Must use PyJWT. python-jose crashes on Python >= 3.10. |
| passlib[bcrypt] for passwords | pwdlib[argon2] 0.3.0 | 2025 (FastAPI docs updated) | Must use pwdlib. passlib breaks on Python 3.13. Argon2 > bcrypt per OWASP. |
| pip + requirements.txt | uv + pyproject.toml + uv.lock | 2024-2025 | 100x faster installs, proper lockfile, Docker cache-friendly. |
| Nginx + certbot | Caddy 2.x | 2023+ | Auto-HTTPS, 3 lines vs 50+. Industry shift for solo/small team projects. |
| @app.on_event("startup") | lifespan context manager | FastAPI 0.100+ | on_event is deprecated. Use lifespan for startup/shutdown. |
| SQLAlchemy 1.4 async | SQLAlchemy 2.0.48 async | 2023+ | Proper async support, mapped_column, type annotations. |

**Deprecated/outdated:**
- `python-jose`: Abandoned since 2021. Do not use.
- `passlib`: Unmaintained since 2020. Do not use.
- `@app.on_event("startup"/"shutdown")`: Deprecated in favor of `lifespan` context manager.
- `sqlalchemy.Column()` style: Use `mapped_column()` with type annotations in SQLAlchemy 2.0.

## Open Questions

1. **Alembic migration runner: owner role vs app role**
   - What we know: Migrations need DDL privileges (CREATE TABLE, ALTER TABLE). The `app_user` role should only have DML privileges (SELECT, INSERT, UPDATE, DELETE).
   - What's unclear: Whether to run Alembic as the owner role in a separate container/command or handle role switching in `env.py`.
   - Recommendation: Run Alembic as the owner role (use `DATABASE_URL` with owner credentials in the migration command). The FastAPI app uses `app_user` credentials. Two separate database URLs in config.

2. **Redis: include in Phase 1 or defer?**
   - What we know: Redis is in the STACK.md for cache, task broker, sessions. Phase 1 has no caching or task queue requirements.
   - What's unclear: Whether JWT token blacklisting (for logout) requires Redis in Phase 1.
   - Recommendation: Defer Redis to Phase 2 or later. JWT tokens are stateless; for Phase 1, token expiration is sufficient. If logout is needed, add a short-lived token with 30-minute expiry.

3. **TG bot auth flow in Phase 1 scope**
   - What we know: CONTEXT.md lists TG bot auth as primary. Phase 1 includes master authentication. But Phase 2 is "Booking + TG" where the actual bot is built.
   - What's unclear: Whether Phase 1 should implement the full TG auth flow or just email+password for testing.
   - Recommendation: Phase 1 implements email+password auth endpoints (the web panel fallback) plus the JWT infrastructure. The TG bot auth handler is added in Phase 2 when the bot is created. The auth service should be designed to support multiple auth methods from the start (strategy pattern).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (latest) |
| Config file | `backend/pyproject.toml` [tool.pytest.ini_options] or `backend/pytest.ini` -- Wave 0 |
| Quick run command | `cd backend && uv run pytest tests/ -x -q` |
| Full suite command | `cd backend && uv run pytest tests/ -v --tb=short` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFR-01 | FastAPI starts, health check responds | smoke | `uv run pytest tests/test_health.py -x` | No -- Wave 0 |
| INFR-01 | PostgreSQL connection works | integration | `uv run pytest tests/test_db.py -x` | No -- Wave 0 |
| INFR-02 | API versioning /api/v1/ prefix works | smoke | `uv run pytest tests/test_health.py::test_api_v1_prefix -x` | No -- Wave 0 |
| INFR-04 | Master can register with email+password | integration | `uv run pytest tests/test_auth.py::test_register -x` | No -- Wave 0 |
| INFR-04 | Master can login and receive JWT | integration | `uv run pytest tests/test_auth.py::test_login -x` | No -- Wave 0 |
| INFR-04 | JWT token authenticates subsequent requests | integration | `uv run pytest tests/test_auth.py::test_authenticated_request -x` | No -- Wave 0 |
| INFR-05 | RLS prevents cross-tenant data access | integration | `uv run pytest tests/test_rls.py -x` | No -- Wave 0 |
| CLNT-02 | Phone numbers normalized to E.164 | unit | `uv run pytest tests/test_phone.py -x` | No -- Wave 0 |
| CLNT-02 | "89161234567" and "+79161234567" resolve to same client | integration | `uv run pytest tests/test_phone.py::test_dedup -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && uv run pytest tests/ -x -q`
- **Per wave merge:** `cd backend && uv run pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/pyproject.toml` -- [tool.pytest.ini_options] section with `asyncio_mode = "auto"`
- [ ] `backend/tests/conftest.py` -- async test DB setup, AsyncClient fixture, test database creation/teardown
- [ ] `backend/tests/test_health.py` -- covers INFR-01, INFR-02
- [ ] `backend/tests/test_auth.py` -- covers INFR-04
- [ ] `backend/tests/test_phone.py` -- covers CLNT-02
- [ ] `backend/tests/test_rls.py` -- covers INFR-05
- [ ] `backend/tests/test_db.py` -- covers INFR-01 (database connectivity)
- [ ] Test database creation strategy: use separate test database or transaction rollback per test

## Sources

### Primary (HIGH confidence)
- [FastAPI Official JWT Tutorial (updated with PyJWT + pwdlib)](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) -- Auth pattern, library recommendations
- [FastAPI Official Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/) -- AsyncClient testing pattern
- [FastAPI Official Settings/Env](https://fastapi.tiangolo.com/advanced/settings/) -- pydantic-settings pattern
- [Alembic Official Docs](https://alembic.sqlalchemy.org/en/latest/tutorial.html) -- Async template, naming conventions
- [Caddy Official Docs](https://caddyserver.com/docs/quick-starts/reverse-proxy) -- Reverse proxy config
- [PyPI: FastAPI 0.135.1](https://pypi.org/project/fastapi/) -- Mar 2026
- [PyPI: SQLAlchemy 2.0.48](https://pypi.org/project/SQLAlchemy/) -- Mar 2026
- [PyPI: asyncpg 0.31.0](https://pypi.org/project/asyncpg/) -- Nov 2025
- [PyPI: Alembic 1.18.4](https://pypi.org/project/alembic/) -- Feb 2026
- [PyPI: PyJWT 2.12.1](https://pypi.org/project/PyJWT/) -- Mar 2026
- [PyPI: pwdlib 0.3.0](https://pypi.org/project/pwdlib/) -- Oct 2025
- [PyPI: pydantic-settings 2.13.1](https://pypi.org/project/pydantic-settings/) -- Feb 2026
- [PyPI: phonenumbers 9.0.26](https://pypi.org/project/phonenumbers/) -- Mar 2026
- [phonenumbers library (Google libphonenumber port)](https://github.com/daviddrysdale/python-phonenumbers) -- E.164 normalization

### Secondary (MEDIUM confidence)
- [FastAPI GitHub Discussion #9587: python-jose abandoned](https://github.com/fastapi/fastapi/discussions/9587) -- Confirmed deprecation
- [FastAPI GitHub Discussion #11773: passlib unmaintained](https://github.com/fastapi/fastapi/discussions/11773) -- Confirmed deprecation
- [pwdlib: Introducing a modern password hash helper](https://www.francoisvoron.com/blog/introducing-pwdlib-a-modern-password-hash-helper-for-python) -- pwdlib rationale
- [PostgreSQL RLS Implementation Guide (permit.io)](https://www.permit.io/blog/postgres-rls-implementation-guide) -- RLS best practices
- [FastAPI + SQLAlchemy + asyncpg integration](https://github.com/grillazz/fastapi-sqlalchemy-asyncpg) -- Reference implementation
- [Caddy Docker Compose setup (wirelessmoves)](https://blog.wirelessmoves.com/2025/06/caddy-as-a-docker-compose-reverse-proxy.html) -- Docker pattern
- [Dockerizing FastAPI with uv, Gunicorn, Caddy](https://medium.com/pythoneers/dockerizing-fastapi-the-right-way-uv-gunicorn-caddy-ci-cd-cd36f594da32) -- Production Docker pattern
- [Alembic async setup tutorial (berkkaraal)](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/) -- Async migration setup
- [uv FastAPI integration guide](https://docs.astral.sh/uv/guides/integration/fastapi/) -- Official uv docs

### Tertiary (LOW confidence)
- None. All findings verified with primary or secondary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All versions verified on PyPI with exact release dates. Library deprecations confirmed via FastAPI official docs and GitHub discussions.
- Architecture: HIGH -- Patterns sourced from FastAPI official docs, SQLAlchemy 2.0 docs, and multiple verified tutorials from 2025-2026.
- Pitfalls: HIGH -- RLS bypass is documented in PostgreSQL official docs. Auth deprecations confirmed. Phone normalization edge cases documented in phonenumbers library.
- Validation: MEDIUM -- Test patterns from FastAPI docs and community, but specific async test DB isolation strategy may need iteration.

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable stack, 30-day validity)
