---
phase: 09-backend-foundation
plan: 01
subsystem: database
tags: [alembic, sqlalchemy, postgresql, rls, migrations, models]

# Dependency graph
requires:
  - phase: 08-web-admin-ux-polish
    provides: "Stable v1.x schema through migration 008"
provides:
  - "Alembic migrations 009-013 for v2.0 schema (profile, portfolio, reviews, client sessions, FNS receipts)"
  - "PortfolioPhoto, Review, ClientSession SQLAlchemy models"
  - "Master model extended with profile and FNS fields"
  - "Payment model extended with FNS receipt tracking"
  - "RLS policies on portfolio_photos and reviews tables"
affects: [10-master-profile-api, 11-public-page, 12-reviews, 13-client-cabinet, 14-fns-receipts]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "NULLIF RLS pattern for new tenant-scoped tables"
    - "sa.text() alias to avoid column name shadowing in models with 'text' columns"

key-files:
  created:
    - backend/alembic/versions/009_add_master_profile_fields.py
    - backend/alembic/versions/010_add_portfolio_photos.py
    - backend/alembic/versions/011_add_reviews.py
    - backend/alembic/versions/012_add_client_sessions.py
    - backend/alembic/versions/013_add_payment_fns_receipt.py
    - backend/app/models/portfolio_photo.py
    - backend/app/models/review.py
    - backend/app/models/client_session.py
  modified:
    - backend/app/models/master.py
    - backend/app/models/payment.py
    - backend/app/models/__init__.py

key-decisions:
  - "Used sa.text() instead of text() in Review model to avoid shadowing by 'text' column name"
  - "Added CHECK constraint on reviews.rating (1-5) at migration level for DB-level validation"
  - "client_sessions table has no RLS -- clients span masters by design"

patterns-established:
  - "New tenant-scoped tables use NULLIF RLS pattern from migration 008"
  - "Cross-tenant tables (client_sessions) skip RLS intentionally"
  - "Models with 'text' column name import sqlalchemy as sa to use sa.text() for server_default"

requirements-completed: [PBUK-02]

# Metrics
duration: 3min
completed: 2026-03-21
---

# Phase 9 Plan 01: Database Migrations & Models Summary

**5 Alembic migrations (009-013) with RLS policies and 3 new SQLAlchemy models for v2.0 schema foundation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T03:34:08Z
- **Completed:** 2026-03-21T03:37:41Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Complete migration chain 008 -> 009 -> 010 -> 011 -> 012 -> 013 with proper revision linking
- RLS policies on portfolio_photos and reviews using NULLIF pattern; no RLS on client_sessions (cross-master)
- Master model extended with 8 profile/FNS fields and 2 new relationships
- Payment model extended with FNS receipt tracking (url + attempt counter)
- PortfolioPhoto, Review, ClientSession models created with lazy="raise_on_sql" relationships

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 5 Alembic migrations (009-013)** - `14c3a63` (feat)
2. **Task 2: Create new models and extend existing ones** - `0b5d757` (feat)

## Files Created/Modified
- `backend/alembic/versions/009_add_master_profile_fields.py` - Master profile + FNS column additions
- `backend/alembic/versions/010_add_portfolio_photos.py` - portfolio_photos table with RLS
- `backend/alembic/versions/011_add_reviews.py` - reviews table with RLS + rating CHECK
- `backend/alembic/versions/012_add_client_sessions.py` - client_sessions table (no RLS)
- `backend/alembic/versions/013_add_payment_fns_receipt.py` - Payment FNS receipt columns
- `backend/app/models/portfolio_photo.py` - PortfolioPhoto SQLAlchemy model
- `backend/app/models/review.py` - Review SQLAlchemy model
- `backend/app/models/client_session.py` - ClientSession SQLAlchemy model
- `backend/app/models/master.py` - Extended with profile/FNS fields + relationships
- `backend/app/models/payment.py` - Extended with FNS receipt fields
- `backend/app/models/__init__.py` - Exports 3 new models

## Decisions Made
- Used `sa.text()` (import sqlalchemy as sa) in Review model because the `text` column name shadows SQLAlchemy's `text()` function -- prevents TypeError at class definition time
- Added `CHECK(rating >= 1 AND rating <= 5)` constraint in migration 011 for DB-level validation of review ratings
- client_sessions deliberately has no RLS since clients exist across masters

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed text() function shadowing in Review model**
- **Found during:** Task 2 (model creation)
- **Issue:** The Review model has a column named `text`, which shadows the imported `text()` function from SQLAlchemy. This caused `TypeError: 'MappedColumn' object is not callable` when defining `server_default=text("'published'")` on the status column.
- **Fix:** Imported `sqlalchemy as sa` and used `sa.text()` for all server_default values in the Review model.
- **Files modified:** backend/app/models/review.py
- **Verification:** `from app.models import Review` succeeds; all attributes accessible
- **Committed in:** 0b5d757 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for model to be importable. No scope creep.

## Issues Encountered
None beyond the text() shadowing bug documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All v2.0 database tables and columns are defined
- Migration chain is complete and ready to run against the database
- Models are importable and can be used by all subsequent phases (10-16)
- No blockers for Phase 9 Plan 2 or subsequent phases

## Self-Check: PASSED

All 8 created files verified present on disk. Both task commits (14c3a63, 0b5d757) verified in git log.

---
*Phase: 09-backend-foundation*
*Completed: 2026-03-21*
