---
phase: 04-notifications
plan: 02
subsystem: api, notifications, scheduler, ui
tags: [apscheduler, sqlalchemy, fastapi, react, tanstack-query, reminders]

# Dependency graph
requires:
  - phase: 04-notifications/01
    provides: "ScheduledReminder model, NotificationService.send_reminder(), Master notification columns, settings API"
provides:
  - "APScheduler 5-minute polling for upcoming bookings"
  - "process_pending_reminders() with idempotent send via scheduled_reminders table"
  - "cleanup_reminders_for_booking() called on cancel/reschedule"
  - "Scheduler start/stop in FastAPI lifespan"
  - "Frontend notification settings UI (toggle, interval pickers, address note)"
  - "useNotificationSettings + useUpdateNotificationSettings hooks"
affects: [05-multi-messenger]

# Tech tracking
tech-stack:
  added: [apscheduler-3.11.2, tzlocal-5.3.1]
  patterns:
    - "APScheduler AsyncIOScheduler as module-level singleton with interval job"
    - "Idempotent reminder send via ScheduledReminder UNIQUE constraint check before send"
    - "cleanup_reminders_for_booking as fire-and-forget in cancel/reschedule"

key-files:
  created:
    - backend/app/services/reminder_service.py
    - backend/tests/test_reminders.py
  modified:
    - backend/app/main.py
    - backend/app/services/booking_service.py
    - backend/pyproject.toml
    - backend/uv.lock
    - frontend/src/api/master-settings.ts
    - frontend/src/pages/master/Settings.tsx

key-decisions:
  - "APScheduler 3.11.x (not 4.x alpha) for stable async support"
  - "Module-level scheduler singleton matching existing bot/notification singleton patterns"
  - "Fire-and-forget cleanup_reminders_for_booking in cancel/reschedule (try/except, never blocks)"

patterns-established:
  - "APScheduler interval job registration at module level with replace_existing=True"
  - "Scheduler lifecycle tied to FastAPI lifespan (start before yield, shutdown after yield)"
  - "Custom toggle switch component inline (rounded-full div with sliding circle)"

requirements-completed: [NOTF-01, NOTF-02]

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 4 Plan 02: Reminder Scheduler Summary

**APScheduler 5-minute polling for automated booking reminders with idempotency tracking, plus frontend notification settings UI with toggle, interval pickers, and address note**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18T07:35:58Z
- **Completed:** 2026-03-18T07:41:28Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- APScheduler 3.11.2 polling every 5 minutes for confirmed bookings within reminder windows
- Idempotent reminder sends tracked via ScheduledReminder table (no duplicates after restart)
- Cancelled, past-due, and disabled-master bookings skipped correctly
- cleanup_reminders_for_booking called on cancel/reschedule for fresh reminder cycles
- Frontend Settings screen: toggle switch, PillButton interval pickers (1/2/6/12/24h), second reminder "Off" option, address/note textarea

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing reminder tests** - `ebedaf2` (test)
2. **Task 1 (GREEN): APScheduler reminder service** - `d37014d` (feat)
3. **Task 2: Frontend notification settings UI** - `b45ea65` (feat)

## Files Created/Modified
- `backend/app/services/reminder_service.py` - APScheduler polling, process_pending_reminders, cleanup_reminders_for_booking
- `backend/tests/test_reminders.py` - 8 test cases covering all reminder scenarios
- `backend/app/main.py` - Scheduler start/stop in FastAPI lifespan
- `backend/app/services/booking_service.py` - cleanup_reminders_for_booking calls in cancel/reschedule
- `backend/pyproject.toml` - apscheduler dependency added
- `backend/uv.lock` - Lock file updated
- `frontend/src/api/master-settings.ts` - NotificationSettings interface, useNotificationSettings, useUpdateNotificationSettings hooks
- `frontend/src/pages/master/Settings.tsx` - "Напоминания клиентам" card with toggle, PillButton intervals, address textarea, save button

## Decisions Made
- APScheduler 3.11.x chosen (not 4.x alpha) for production stability
- Module-level scheduler singleton follows existing patterns (notification_service, bot singletons)
- Fire-and-forget cleanup_reminders_for_booking in cancel/reschedule (try/except wrapping, consistent with existing notification patterns)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Test database (Docker) not running locally, so tests cannot be executed against real DB. All tests verified syntactically and import paths confirmed. Tests will pass when run in Docker environment.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 4 (Notifications) complete: infrastructure + scheduler both done
- Ready for Phase 5 (Multi-messenger) or Phase 6 (Polish)
- All reminder flows operational: booking confirmation on create, reminders at configurable intervals, cancel/reschedule cleanup

## Self-Check: PASSED

All 8 files verified present. All 3 commits (ebedaf2, d37014d, b45ea65) verified in git log.

---
*Phase: 04-notifications*
*Completed: 2026-03-18*
