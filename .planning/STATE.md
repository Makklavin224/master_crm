---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Feature Expansion
status: completed
stopped_at: Completed 13-02-PLAN.md
last_updated: "2026-03-21T06:36:05.723Z"
last_activity: 2026-03-21 -- Completed 13-02 Auto-Receipts Frontend
progress:
  total_phases: 8
  completed_phases: 5
  total_plans: 20
  completed_plans: 13
  percent: 65
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-20)

**Core value:** Master taps "Complete" -- client gets SBP payment link -- tax receipt auto-generates. 3 steps instead of 9.
**Current focus:** v2.0 Feature Expansion -- Phase 13 (Auto-Receipts) complete, moving to Phase 14

## Current Position

Phase: 13 of 16 (Auto-Receipts)
Plan: 2 of 2 -- DONE
Status: Phase 13 complete, ready for Phase 14
Last activity: 2026-03-21 -- Completed 13-02 Auto-Receipts Frontend

Progress: [███████░░░] 65%

## Performance Metrics

**Velocity:**
- Total plans completed: 29
- Average duration: 6min
- Total execution time: ~2.8 hours

**By Phase (v1.0 + v1.1):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 2/2 | 26min | 13min |
| 2. Booking Engine | 4/4 | 55min | 14min |
| 3. Payments + Tax | 3/3 | 19min | 6min |
| 4. Notifications | 2/2 | 12min | 6min |
| 5. Multi-Messenger | 3/3 | 20min | 7min |
| 6. Web Admin Panel | 3/3 | 16min | 5min |
| 7. Mini-App UX Polish | 5/5 | 11min | 2min |
| 8. Web Admin UX Polish | 3/3 | 6min | 2min |

**Recent Trend:**
- Last 5 plans: 3min, 3min, 3min, 3min, 4min
- Trend: consistent
| Phase 10 P01 | 3min | 2 tasks | 17 files |
| Phase 10 P02 | 2min | 2 tasks | 10 files |
| Phase 10 P03 | 4min | 2 tasks | 10 files |
| Phase 10 P04 | 2min | 2 tasks | 4 files |
| Phase 11 P01 | 3min | 2 tasks | 7 files |
| Phase 11 P02 | 4min | 2 tasks | 4 files |
| Phase 11 P03 | 3min | 2 tasks | 10 files |
| Phase 12 P01 | 4min | 2 tasks | 6 files |
| Phase 12 P02 | 2min | 2 tasks | 4 files |
| Phase 13 P01 | 7min | 2 tasks | 9 files |
| Phase 13 P02 | 3min | 2 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- v2.0 design spec approved (2026-03-20): 8 phases, 47 requirements
- Phase structure follows design spec Section 10 priority order
- Public page is separate React SPA in /public/ dir (not part of admin or mini-app)
- Robokassa ReceiptAttach for cash/card receipts (not direct FNS API)
- Client cabinet shares SPA with public page (both under /public/, routes /m/ and /my/)
- Portfolio stored in Docker volume (/data/portfolio/) for MVP; S3/MinIO later
- Used sa.text() in Review model to avoid 'text' column shadowing SQLAlchemy text() function
- client_sessions has no RLS (cross-master table by design)
- Rating CHECK constraint (1-5) added at DB level in reviews migration
- Public API uses dual-identifier pattern: UUID parsed first, username fallback
- Review stats computed on-the-fly via SQL aggregates (not denormalized)
- Public SPA uses same dep versions as frontend/ for consistency, omits Telegram-specific packages
- Base path convention: /app/ (mini-app), /admin/ (web admin), /m/ (public master pages)
- [Phase 10]: Public SPA uses same dep versions as frontend/ for consistency, omits Telegram-specific packages
- [Phase 10-02]: SlotsSection fetches slots for first service only to limit API calls
- [Phase 10-02]: StarRating uses opacity-60 for half-star approximation
- [Phase 10-02]: StickyBookButton always visible (no scroll observer) for MVP
- [Phase 10-03]: Zustand store adapted from frontend/ without platform deps (no TG/MAX bridges)
- [Phase 10-03]: Date picker uses 14-day grid cards instead of react-day-picker (no extra dep)
- [Phase 10-03]: source_platform hardcoded as "web" for public page bookings
- [Phase 10-04]: Client-side meta tags via useEffect (sufficient for Telegram/WhatsApp/VK link previews)
- [Phase 11-01]: OTP stored as SHA256 hash in client_sessions table (not separate table)
- [Phase 11-01]: Session token as httpOnly secure cookie with SameSite=lax (7-day expiry)
- [Phase 11-01]: Messenger delivery priority: telegram > max > vk
- [Phase 11-01]: Reviews with rating >= 3 auto-publish, rating < 3 pending_reply
- [Phase 11-02]: Removed strip_prefix from /m/* Caddy block; SPA receives full path
- [Phase 11-02]: Added /assets/* Caddy handler for Vite build output with base "/"
- [Phase 11-02]: Navigate calls use absolute /m/ prefix paths (pre-applied by 11-01)
- [Phase 11-03]: Auth session check via GET /client/bookings (reuses endpoint, no /me needed)
- [Phase 11-03]: OTP input uses 6 separate fields with auto-focus and paste support
- [Phase 11-03]: Reschedule MVP shows alert placeholder (requires time picker UI, deferred)
- [Phase 11-03]: Review form renders inline below BookingCard (not modal/bottom sheet)
- [Phase 12-01]: amount_override sent only when differs from service price (avoids unnecessary override)
- [Phase 12-01]: SBP payment routes through Robokassa when has_robokassa; all other methods use manual payment
- [Phase 12-01]: Revenue query always filters status=paid regardless of status_filter
- [Phase 12-02]: CSV export uses StreamingResponse with BOM prefix for Excel UTF-8 compatibility
- [Phase 12-02]: Calendar payment indicator uses lightweight payment query + Set for O(1) lookup
- [Phase 13-01]: ReceiptAttach uses same URL for test/prod, IsTest=1 flag differentiates
- [Phase 13-01]: Receipt retry reuses APScheduler from reminder_service (receipt_retry_poll job)
- [Phase 13-01]: send_receipt_link wraps send_message (no new adapter method needed)
- [Phase 13-01]: INN binding requires Robokassa connected first (returns 400 if not)
- [Phase 13-02]: Web admin allows INN binding directly (not read-only) for admin convenience
- [Phase 13-02]: INN input uses digit-only filter with maxLength 12 and inputMode numeric

### Pending Todos

None yet.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-03-21T06:34:00Z
Stopped at: Completed 13-02-PLAN.md
Resume file: None
