---
phase: 05-multi-messenger-expansion
plan: 01
subsystem: auth, api, database
tags: [hmac, jwt, max, vk, alembic, pydantic, fastapi]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "Master model, auth system, config pattern, security module"
  - phase: 02-booking-engine-telegram
    provides: "TG initData validation pattern, tg_auth endpoint pattern"
provides:
  - "MAX/VK config settings (8 new fields)"
  - "validate_max_init_data (delegates to TG validator)"
  - "validate_vk_launch_params (HMAC-SHA256 + URL-safe base64)"
  - "Master.max_user_id and Master.vk_user_id columns"
  - "Alembic migration 006"
  - "POST /auth/max and POST /auth/vk endpoints"
  - "MaxAuthRequest and VkAuthRequest Pydantic schemas"
affects: [05-02-PLAN, 05-03-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: ["validate_max delegates to validate_tg (algorithm reuse, not duplication)", "VK launch params validation with URL-safe base64 HMAC", "Messenger auth endpoint pattern (validate -> extract user_id -> lookup master -> JWT)"]

key-files:
  created:
    - backend/alembic/versions/006_add_max_vk_master_columns.py
  modified:
    - backend/app/core/config.py
    - backend/app/core/security.py
    - backend/app/models/master.py
    - backend/app/schemas/auth.py
    - backend/app/api/v1/auth.py

key-decisions:
  - "validate_max_init_data delegates to validate_tg_init_data (identical HMAC-SHA256 algorithm, zero code duplication)"
  - "VK validation uses OrderedDict for deterministic param sorting and URL-safe base64 encoding"
  - "All 8 new config fields default to empty string (app starts without them, same pattern as TG)"
  - "Manual Alembic migration (not autogenerate) for explicit control over column/index creation"

patterns-established:
  - "Messenger auth endpoint pattern: validate initData/params -> extract platform user_id -> lookup Master by platform column -> return JWT"
  - "Platform user ID columns: nullable, unique, indexed String(100) on masters table"

requirements-completed: [MSG-03, MSG-04, MSG-05, MSG-06]

# Metrics
duration: 3min
completed: 2026-03-18
---

# Phase 5 Plan 01: Shared Backend Infrastructure Summary

**MAX/VK config, HMAC validation functions, Master model columns, Alembic migration, and auth endpoints for multi-messenger expansion**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-18T12:31:07Z
- **Completed:** 2026-03-18T12:34:18Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- 8 config fields for MAX and VK messenger settings with safe empty defaults
- Two validation functions: validate_max_init_data (delegates to TG) and validate_vk_launch_params (VK-specific HMAC-SHA256 + URL-safe base64)
- Master model extended with max_user_id and vk_user_id columns (nullable, unique, indexed)
- Alembic migration 006 for new columns
- POST /auth/max and POST /auth/vk endpoints following the same pattern as /auth/tg
- MaxAuthRequest and VkAuthRequest Pydantic schemas

## Task Commits

Each task was committed atomically:

1. **Task 1: Config, security validation, Master model columns, Alembic migration** - `4069ec8` (feat)
2. **Task 2: Auth schemas and auth endpoints for MAX and VK** - `310a0da` (feat)

## Files Created/Modified
- `backend/app/core/config.py` - Added 8 MAX/VK config fields to Settings class
- `backend/app/core/security.py` - Added validate_max_init_data and validate_vk_launch_params functions
- `backend/app/models/master.py` - Added max_user_id and vk_user_id columns
- `backend/alembic/versions/006_add_max_vk_master_columns.py` - Migration adding both columns with unique indexes
- `backend/app/schemas/auth.py` - Added MaxAuthRequest and VkAuthRequest Pydantic models
- `backend/app/api/v1/auth.py` - Added POST /auth/max and POST /auth/vk endpoints

## Decisions Made
- validate_max_init_data delegates to validate_tg_init_data -- MAX uses the identical HMAC-SHA256 algorithm as Telegram, so zero code duplication
- VK validation uses OrderedDict for deterministic param sorting and URL-safe base64 encoding per VK official algorithm
- All 8 new config fields default to empty string -- app starts without them configured (same pattern as existing TG settings)
- Manual Alembic migration written (not autogenerate) for explicit control over column/index creation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Test suite requires running PostgreSQL database (Docker), which is not available in local dev environment. Verified correctness via import checks and functional validation tests instead.

## User Setup Required

None - no external service configuration required. MAX/VK tokens will be configured when Plans 02 and 03 are implemented.

## Next Phase Readiness
- Both Plans 02 (MAX full stack) and 03 (VK full stack) can now proceed independently -- they share this foundation
- Config fields, validation functions, model columns, and auth endpoints are all in place
- No blockers

---
*Phase: 05-multi-messenger-expansion*
*Completed: 2026-03-18*
