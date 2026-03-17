---
phase: 01-foundation
plan: 02
subsystem: auth
tags: [jwt, pyjwt, pwdlib, argon2, fastapi, cors, rls, pytest, httpx, integration-tests]

# Dependency graph
requires:
  - phase: 01-foundation/01
    provides: "FastAPI app factory, SQLAlchemy models, database layer, Docker stack"
provides:
  - JWT authentication (register, login, /me) with PyJWT + Argon2 password hashing
  - FastAPI dependencies (get_db, get_current_master, get_db_with_rls)
  - Auth schemas (RegisterRequest, LoginRequest, TokenResponse, MasterRead)
  - Integration test suite covering auth flow and RLS tenant isolation
  - CORS middleware configured for allowed origins
affects: [02-booking, 03-payments, 04-notifications, 05-multi-messenger, 06-web-panel]

# Tech tracking
tech-stack:
  added: [pyjwt, pwdlib, argon2, httpx, pytest-asyncio]
  patterns: [oauth2-bearer-auth, timing-attack-prevention, set-local-rls-context, dependency-override-testing, transactional-test-rollback]

key-files:
  created:
    - backend/app/core/security.py
    - backend/app/core/dependencies.py
    - backend/app/services/auth_service.py
    - backend/app/schemas/auth.py
    - backend/app/schemas/master.py
    - backend/app/api/v1/auth.py
    - backend/tests/test_auth.py
    - backend/tests/test_rls.py
  modified:
    - backend/app/api/v1/router.py
    - backend/app/main.py
    - backend/tests/conftest.py
    - backend/tests/test_health.py

key-decisions:
  - "PyJWT + pwdlib (Argon2) for auth, NOT python-jose + passlib (deprecated)"
  - "SET LOCAL for RLS context (transaction-scoped, prevents connection pool leaks)"
  - "Timing attack prevention with DUMMY_HASH on failed login lookups"
  - "OAuth2PasswordBearer with tokenUrl=/api/v1/auth/login for Swagger UI integration"

patterns-established:
  - "Auth dependency chain: OAuth2PasswordBearer -> get_current_master -> get_db_with_rls"
  - "Service layer pattern: router calls service functions, service handles business logic and raises HTTPException"
  - "Test infrastructure: override get_db dependency, transactional rollback per test, master_factory fixture"
  - "RLS testing: create two masters, switch SET LOCAL context, verify isolation"

requirements-completed: [INFR-02, INFR-04]

# Metrics
duration: 5min
completed: 2026-03-17
---

# Phase 1 Plan 02: Auth System Summary

**JWT auth with Argon2 password hashing via PyJWT + pwdlib, three auth endpoints (register/login/me), RLS-aware database dependencies, and integration test suite verifying auth flow and tenant isolation**

## Performance

- **Duration:** 5 min (code execution) + checkpoint review
- **Started:** 2026-03-17T10:35:18Z
- **Completed:** 2026-03-17T11:00:13Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 13

## Accomplishments
- Complete auth system: email+password registration with validation, login with timing-attack-safe password verification, JWT token issuance and decoding
- FastAPI dependency chain: get_db (session with auto-commit/rollback), get_current_master (JWT decode + user lookup), get_db_with_rls (SET LOCAL context injection)
- Integration test suite: 11 auth tests (register success/duplicate/short-password/invalid-email, login success/wrong-password/nonexistent, me authenticated/no-token/invalid-token/expired-token) + 3 RLS tests (cross-tenant blocked, own-tenant visible, no-context returns nothing)
- CORS middleware configured with settings.allowed_origins for cross-origin mini-app requests

## Task Commits

Each task was committed atomically:

1. **Task 1: Security module, auth service, auth endpoints, dependencies** - `f54a790` (feat)
2. **Task 2 RED: Failing tests for auth flow and RLS** - `05495b1` (test)
3. **Task 2 GREEN: Test infrastructure with DB fixtures, auth and RLS tests** - `beebb52` (feat)

_Task 3 was a checkpoint:human-verify (Docker stack verification) -- approved by user, no code commit required._

## Files Created/Modified
- `backend/app/core/security.py` - JWT encode/decode with PyJWT, Argon2 password hashing with pwdlib, DUMMY_HASH for timing attack prevention
- `backend/app/core/dependencies.py` - get_db (async session), get_current_master (JWT + DB lookup), get_db_with_rls (SET LOCAL for tenant isolation)
- `backend/app/services/auth_service.py` - register_master (email validation, uniqueness, password hashing), authenticate_master (timing-safe login)
- `backend/app/schemas/auth.py` - RegisterRequest, LoginRequest, TokenResponse Pydantic models
- `backend/app/schemas/master.py` - MasterRead schema with from_attributes config
- `backend/app/api/v1/auth.py` - POST /register (201), POST /login (200), GET /me (authenticated)
- `backend/app/api/v1/router.py` - Added auth_router include
- `backend/app/main.py` - Added CORSMiddleware with settings.allowed_origins
- `backend/tests/conftest.py` - Full test infrastructure: test DB engines, session override, master_factory, auth_headers fixtures
- `backend/tests/test_auth.py` - 11 integration tests across TestRegister, TestLogin, TestMe classes
- `backend/tests/test_rls.py` - 3 RLS isolation tests: cross-tenant blocked, own-tenant allowed, no-context returns nothing
- `backend/tests/test_health.py` - Updated to work with new conftest structure

## Decisions Made
- **PyJWT + pwdlib over python-jose + passlib:** Following research recommendations -- python-jose is unmaintained, passlib deprecated. PyJWT is actively maintained, pwdlib provides modern Argon2 hashing.
- **SET LOCAL for RLS context:** Transaction-scoped setting prevents tenant context from leaking across connection pool reuse. This is defense-in-depth beyond application-level filtering.
- **DUMMY_HASH timing attack prevention:** When login email is not found, we still run a password verification against a dummy hash to ensure constant-time response, preventing user enumeration.
- **OAuth2PasswordBearer tokenUrl:** Points to /api/v1/auth/login enabling Swagger UI "Authorize" button for interactive API testing.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 1 (Foundation) is now complete: all infrastructure, models, auth, and tests are in place
- Ready for Phase 2 (Booking Engine + Telegram): auth system provides JWT tokens for API authentication, RLS provides tenant isolation for all booking/service/payment data
- Docker Compose stack runs the full environment with `docker compose up`
- Test infrastructure established for future phases to add integration tests easily

## Self-Check: PASSED

All 12 key files verified on disk. All 3 task commits verified in git history.

---
*Phase: 01-foundation*
*Completed: 2026-03-17*
