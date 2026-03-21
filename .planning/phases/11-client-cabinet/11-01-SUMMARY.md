---
phase: 11-client-cabinet
plan: 01
subsystem: api
tags: [otp, auth, cookie-session, fastapi, sha256, alembic]

# Dependency graph
requires:
  - phase: 10-public-master-page
    provides: "Public SPA infrastructure, client_sessions model, review model"
provides:
  - "OTP auth endpoints: POST /client/auth/request-code, POST /client/auth/verify-code"
  - "Client cabinet endpoints: GET /client/bookings, POST /client/reviews"
  - "get_current_client dependency for cookie-based client auth"
  - "Alembic migration 014: otp_hash, otp_attempts, is_verified on client_sessions"
affects: [11-client-cabinet, 12-reviews-reputation]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Cookie-based OTP auth with SHA256 hash and attempt tracking"]

key-files:
  created:
    - backend/app/api/v1/client_auth.py
    - backend/app/api/v1/client_cabinet.py
    - backend/alembic/versions/014_add_otp_columns_to_client_sessions.py
  modified:
    - backend/app/core/dependencies.py
    - backend/app/models/client_session.py
    - backend/app/schemas/client.py
    - backend/app/api/v1/router.py

key-decisions:
  - "OTP stored as SHA256 hash in client_sessions table (not separate table or in-memory)"
  - "Session token set as httpOnly secure cookie with 7-day expiry"
  - "Messenger delivery priority: telegram > max > vk"
  - "Reviews with rating >= 3 auto-publish, rating < 3 set to pending_reply"

patterns-established:
  - "Cookie-based client auth: get_current_client reads client_session cookie, validates against client_sessions where is_verified=True"
  - "OTP security pattern: SHA256 hash, 5-min expiry, 3 attempts max, 60-sec cooldown"

requirements-completed: [CCAB-01, CCAB-02, CCAB-03, CCAB-04, CCAB-05, CCAB-06, CCAB-07]

# Metrics
duration: 3min
completed: 2026-03-21
---

# Phase 11 Plan 01: Client Cabinet API Summary

**OTP auth via messenger bots with SHA256-hashed codes, cookie sessions (7d), cross-master bookings list, and validated review submission**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T05:09:13Z
- **Completed:** 2026-03-21T05:12:48Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- OTP authentication flow: request-code sends 6-digit code via messenger bot, verify-code validates with 3-attempt limit and sets httpOnly cookie
- Cross-master bookings endpoint returns upcoming (confirmed, future) and past (completed/cancelled) bookings with master/service names
- Review submission with full validation chain: completed booking, client ownership, no duplicates, 30-day window
- get_current_client dependency for protecting all client cabinet routes via cookie-based auth

## Task Commits

Each task was committed atomically:

1. **Task 1: Client auth endpoints (OTP request + verify) and get_current_client dependency** - `c3eecdb` (feat)
2. **Task 2: Client bookings and reviews endpoints** - `f980916` (feat)

## Files Created/Modified
- `backend/app/api/v1/client_auth.py` - OTP request/verify endpoints with cooldown, hashing, messenger delivery
- `backend/app/api/v1/client_cabinet.py` - Client bookings list and review submission endpoints
- `backend/alembic/versions/014_add_otp_columns_to_client_sessions.py` - Adds otp_hash, otp_attempts, is_verified columns
- `backend/app/models/client_session.py` - Added 3 new mapped columns for OTP tracking
- `backend/app/core/dependencies.py` - Added get_current_client dependency (cookie-based)
- `backend/app/schemas/client.py` - Added OTP schemas + booking/review schemas (8 new classes)
- `backend/app/api/v1/router.py` - Registered /client/auth and /client route prefixes

## Decisions Made
- OTP stored as SHA256 hash in client_sessions table with otp_attempts counter (cleaner than separate table)
- Session token set as httpOnly secure cookie with SameSite=lax (7-day expiry after verify)
- Messenger delivery priority: telegram > max > vk (first successful delivery wins)
- Graceful fallback when no messenger platform found (logs warning, returns success with SMS-not-implemented message)
- Reviews with rating >= 3 auto-publish, rating < 3 set to pending_reply (moderation for negative reviews)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Client auth and cabinet API complete, ready for frontend (11-02: React cabinet SPA)
- Existing cancel/reschedule endpoints at /bookings/{id}/cancel and /bookings/{id}/reschedule work for client auth
- Migration 014 ready to run on deployment

---
*Phase: 11-client-cabinet*
*Completed: 2026-03-21*
