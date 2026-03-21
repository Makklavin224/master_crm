---
phase: 15-reviews
plan: 01
subsystem: notifications
tags: [apscheduler, review-collection, inline-keyboards, bot-callbacks, polling-service]

# Dependency graph
requires:
  - phase: 13-receipts
    provides: APScheduler pattern for background polling jobs
  - phase: 09-v2-models
    provides: Review model with booking_id FK and status field
provides:
  - Review request polling service (10min interval, 2h delay after completed visits)
  - Auto-publish polling service (hourly, 7-day stale review publishing)
  - send_review_request adapter method across TG/MAX/VK with inline star buttons
  - Bot callback handlers for review_star, review_text, review_done flows
affects: [15-reviews]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sentinel Review row (rating=0, status=request_sent) as idempotency guard"
    - "Module-level dict for pending review text state across callback-to-message flow"
    - "Callback data format: review_star:{booking_id}:{rating}"

key-files:
  created:
    - backend/app/services/review_request_service.py
    - backend/app/services/auto_publish_service.py
  modified:
    - backend/app/bots/common/adapter.py
    - backend/app/bots/common/notification.py
    - backend/app/bots/telegram/adapter.py
    - backend/app/bots/max/adapter.py
    - backend/app/bots/vk/adapter.py
    - backend/app/bots/telegram/handlers/callbacks.py
    - backend/app/bots/max/handlers/callbacks.py
    - backend/app/bots/vk/handlers/callbacks.py
    - backend/app/bots/max/bot.py
    - backend/app/bots/vk/bot.py
    - backend/app/main.py

key-decisions:
  - "Sentinel Review row with rating=0, status=request_sent prevents duplicate review requests without DB migration"
  - "Rating >= 3 auto-publishes, rating < 3 gets pending_reply status for master review"
  - "Module-level dict tracks pending review text state (no FSM framework needed)"

patterns-established:
  - "Review callback flow: star rating -> optional text -> confirmation"
  - "Background service pattern: separate AsyncIOScheduler per service domain"

requirements-completed: [REVW-01, REVW-04, REVW-06]

# Metrics
duration: 6min
completed: 2026-03-21
---

# Phase 15 Plan 01: Review Collection System Summary

**APScheduler-based review request polling (2h after visit) with bot star-rating flow and 7-day auto-publish for stale negative reviews**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-21T06:56:19Z
- **Completed:** 2026-03-21T07:02:37Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Review request service polls every 10min, finds completed bookings 2h+ old with no Review row, sends star-button message to client via bot
- Sentinel Review row (rating=0, status=request_sent) prevents duplicate requests without schema migration
- All 3 bot platforms (TG/MAX/VK) handle star rating callback, optional text comment, and confirmation
- Auto-publish service polls hourly, publishes pending_reply reviews older than 7 days

## Task Commits

Each task was committed atomically:

1. **Task 1: Review request service + auto-publish service + adapter methods** - `889a6a7` (feat)
2. **Task 2: Bot callback handlers for review star rating + optional text flow** - `591ad1e` (feat)

## Files Created/Modified
- `backend/app/services/review_request_service.py` - Polls for completed bookings, sends review requests via bot
- `backend/app/services/auto_publish_service.py` - Auto-publishes stale pending_reply reviews after 7 days
- `backend/app/bots/common/adapter.py` - Added send_review_request abstract method
- `backend/app/bots/common/notification.py` - Added send_review_request routing method
- `backend/app/bots/telegram/adapter.py` - TG implementation with InlineKeyboardMarkup star buttons
- `backend/app/bots/max/adapter.py` - MAX implementation with inline keyboard star buttons
- `backend/app/bots/vk/adapter.py` - VK implementation with callback keyboard star buttons
- `backend/app/bots/telegram/handlers/callbacks.py` - review_star, review_text, review_done handlers + text message handler
- `backend/app/bots/max/handlers/callbacks.py` - MAX review callback handlers + text message handler
- `backend/app/bots/vk/handlers/callbacks.py` - VK review callback handlers + text message handler
- `backend/app/bots/max/bot.py` - Routes text messages through review text handler
- `backend/app/bots/vk/bot.py` - Routes text messages through review text handler
- `backend/app/main.py` - Starts/stops review_request_scheduler and auto_publish_scheduler

## Decisions Made
- Sentinel Review row (rating=0, status=request_sent) chosen over adding a boolean column to bookings table -- avoids DB migration, uses existing Review table uniqueness constraint on booking_id
- Rating >= 3 auto-publishes (status=published), rating < 3 sets status=pending_reply for master response window
- Module-level dict for pending review text state instead of FSM -- simpler, matches existing codebase pattern, no extra dependencies

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added review text message routing in MAX/VK bot modules**
- **Found during:** Task 2 (Bot callback handlers)
- **Issue:** Plan specified text handlers in callback files but MAX/VK bots needed message routing to deliver text messages to the review handler
- **Fix:** Added handle_review_text_message() in MAX/VK callback modules and routed unhandled messages through it in bot.py
- **Files modified:** backend/app/bots/max/bot.py, backend/app/bots/vk/bot.py
- **Verification:** Message flow: user types text -> bot.py routes to handle_review_text_message -> updates Review.text
- **Committed in:** 591ad1e (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for text collection flow to work. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Review collection backend complete, ready for Plan 02 (review management API endpoints and UI)
- Status flow: request_sent -> published (>=3) or pending_reply (<3) -> published (auto after 7d)

## Self-Check: PASSED

All 13 files verified present. Both task commits (889a6a7, 591ad1e) verified in git log.

---
*Phase: 15-reviews*
*Completed: 2026-03-21*
