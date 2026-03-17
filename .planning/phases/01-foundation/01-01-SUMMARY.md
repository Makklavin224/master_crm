---
phase: 01-foundation
plan: 01
subsystem: infra
tags: [fastapi, postgresql, sqlalchemy, alembic, docker, caddy, rls, phonenumbers, pydantic]

# Dependency graph
requires: []
provides:
  - FastAPI app factory with lifespan and /api/v1 health endpoint
  - Async SQLAlchemy engine with dual DB roles (owner for migrations, app_user for RLS)
  - 9 domain models (Master, Client, ClientPlatform, MasterClient, Service, Booking, Payment, MasterSchedule, ScheduleException)
  - Alembic async migrations with initial schema and RLS policies
  - Phone normalization service (E.164 via phonenumbers library)
  - Docker Compose stack (api + db + caddy) with healthcheck
  - Pydantic Settings configuration from .env
affects: [01-02, 02-booking, 03-payments, 04-notifications, 05-multi-messenger, 06-web-panel]

# Tech tracking
tech-stack:
  added: [fastapi 0.135.1, sqlalchemy 2.0.48, asyncpg 0.31.0, alembic 1.18.4, pydantic-settings 2.13.1, pyjwt 2.12.1, pwdlib 0.3.0, phonenumbers 9.0.26, uvicorn 0.42.0, caddy 2-alpine, postgres 16-alpine]
  patterns: [app-factory-with-lifespan, dual-db-roles, rls-tenant-isolation, pydantic-settings-config, e164-phone-normalization]

key-files:
  created:
    - backend/app/main.py
    - backend/app/core/config.py
    - backend/app/core/database.py
    - backend/app/models/master.py
    - backend/app/models/client.py
    - backend/app/models/service.py
    - backend/app/models/booking.py
    - backend/app/models/payment.py
    - backend/app/models/schedule.py
    - backend/app/services/phone_service.py
    - backend/alembic/env.py
    - backend/alembic/versions/001_initial_schema.py
    - backend/alembic/versions/002_enable_rls.py
    - docker-compose.yml
    - backend/Dockerfile
    - Caddyfile
    - backend/scripts/init-db.sql
  modified: []

key-decisions:
  - "Dual database URLs: DATABASE_URL (owner) for Alembic migrations, DATABASE_APP_URL (app_user) for runtime RLS enforcement"
  - "Config resolves .env from project root via Path resolution, supporting both Docker and local dev"
  - "RLS policies use current_setting('app.current_master_id', true)::uuid with fail-closed semantics"
  - "Price stored in kopecks (integer) to avoid float precision issues"

patterns-established:
  - "App factory: create_app() with lifespan context manager, not module-level initialization"
  - "Dual DB roles: owner for schema changes, app_user for application queries (RLS enforced)"
  - "SQLAlchemy 2.0 mapped_column() with type annotations, UUID PKs, timezone-aware timestamps"
  - "Naming conventions on MetaData for Alembic auto-naming of constraints"
  - "Phone normalization at boundary: phonenumbers library, never hand-rolled regex"

requirements-completed: [INFR-01, INFR-05, CLNT-02]

# Metrics
duration: 21min
completed: 2026-03-17
---

# Phase 1 Plan 01: Foundation Scaffolding Summary

**FastAPI + PostgreSQL monorepo with 9 domain models, Alembic async migrations, RLS tenant isolation, E.164 phone normalization, and Docker Compose stack (api + db + caddy)**

## Performance

- **Duration:** 21 min
- **Started:** 2026-03-17T09:54:45Z
- **Completed:** 2026-03-17T10:16:42Z
- **Tasks:** 2
- **Files modified:** 38

## Accomplishments
- Full monorepo scaffolding with FastAPI app factory, Pydantic settings, and async SQLAlchemy database layer
- 9 SQLAlchemy domain models with UUID PKs, foreign keys, indexes, unique constraints, and timezone-aware timestamps
- Alembic async migrations: initial schema (001) and RLS policies with FORCE ROW LEVEL SECURITY on 6 tenant-scoped tables (002)
- Phone normalization service using Google's phonenumbers library handling all Russian number formats
- Docker Compose with PostgreSQL healthcheck, hot-reload uvicorn, and Caddy reverse proxy
- 10 unit tests passing (8 phone normalization + 2 health endpoint)

## Task Commits

Each task was committed atomically:

1. **Task 1: Monorepo scaffolding, FastAPI app factory, configuration, and Docker stack** - `7360f05` (feat)
2. **Task 2 RED: Failing tests for phone normalization and health** - `61e5927` (test)
3. **Task 2 GREEN: Domain models, Alembic, phone service, RLS** - `f8a20b2` (feat)

## Files Created/Modified
- `docker-compose.yml` - Full stack orchestration (api, db, caddy services)
- `docker-compose.override.yml` - Development overrides placeholder
- `Caddyfile` - Reverse proxy config routing to api:8000
- `.env.example` - Environment variable template with dual DB URLs
- `.gitignore` - Python/Docker ignore patterns
- `backend/pyproject.toml` - uv project with all dependencies, pytest config
- `backend/uv.lock` - Locked dependency versions
- `backend/Dockerfile` - Multi-stage build with uv
- `backend/scripts/init-db.sql` - Creates app_user PostgreSQL role
- `backend/app/main.py` - FastAPI app factory with lifespan
- `backend/app/core/config.py` - Pydantic Settings with dual DB URLs
- `backend/app/core/database.py` - Async engine using app_user URL
- `backend/app/models/base.py` - DeclarativeBase with naming conventions
- `backend/app/models/master.py` - Master model with email, phone, business_name
- `backend/app/models/client.py` - Client, ClientPlatform, MasterClient models
- `backend/app/models/service.py` - Service model with price in kopecks
- `backend/app/models/booking.py` - Booking model with status and source_platform
- `backend/app/models/payment.py` - Payment model with receipt_status
- `backend/app/models/schedule.py` - MasterSchedule and ScheduleException models
- `backend/app/models/__init__.py` - Re-exports all 9 model classes
- `backend/app/services/phone_service.py` - E.164 normalization with phonenumbers
- `backend/app/schemas/common.py` - HealthResponse Pydantic model
- `backend/app/api/v1/health.py` - Health endpoint returning status and version
- `backend/app/api/v1/router.py` - V1 router aggregator
- `backend/alembic.ini` - Alembic config (URL overridden in env.py)
- `backend/alembic/env.py` - Async migration runner with owner-role URL
- `backend/alembic/versions/001_initial_schema.py` - Creates all 9 tables
- `backend/alembic/versions/002_enable_rls.py` - RLS policies and app_user grants
- `backend/tests/conftest.py` - AsyncClient fixture with ASGI transport
- `backend/tests/test_health.py` - Health endpoint and API prefix tests
- `backend/tests/test_phone.py` - 8 phone normalization tests

## Decisions Made
- **Dual database URLs:** `DATABASE_URL` (mastercrm_owner) for Alembic migrations with DDL privileges; `DATABASE_APP_URL` (app_user) for runtime queries with RLS enforcement. This follows the research recommendation for defense-in-depth.
- **Config .env resolution:** Settings resolves .env from project root via `Path(__file__).parents[3]`, supporting both Docker (`env_file` in compose) and local development without Docker.
- **Fail-closed RLS:** `current_setting('app.current_master_id', true)::uuid` returns NULL when setting is missing, causing queries to return no rows rather than throwing an error.
- **Price in kopecks:** Integer storage avoids floating-point precision issues in financial calculations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] uv not installed on system**
- **Found during:** Task 1 (project initialization)
- **Issue:** `uv` package manager not found on PATH
- **Fix:** Installed uv via `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Files modified:** None (system-level install)
- **Verification:** `uv --version` returns 0.10.11
- **Committed in:** N/A (no code change)

**2. [Rule 3 - Blocking] Settings could not find .env from backend/ working directory**
- **Found during:** Task 1 (app import verification)
- **Issue:** Pydantic Settings looks for `.env` relative to CWD. When running from `backend/`, the `.env` at project root was not found.
- **Fix:** Added Path-based resolution to find .env from project root (`Path(__file__).parents[3] / ".env"`)
- **Files modified:** `backend/app/core/config.py`
- **Verification:** `uv run python -c "from app.main import app; print(app.title)"` succeeds
- **Committed in:** 7360f05 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary for basic functionality. No scope creep.

## Issues Encountered
- uv generated a `main.py` in the backend root during `uv init` which was removed to avoid confusion with `app/main.py`

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All domain models and database schema ready for Plan 02 (auth system)
- JWT dependencies (pyjwt, pwdlib) already installed and available
- App factory pattern established for easy test fixture creation
- Docker stack ready for `docker compose up` to run full verification

## Self-Check: PASSED

All 15 key files verified on disk. All 3 task commits verified in git history.

---
*Phase: 01-foundation*
*Completed: 2026-03-17*
