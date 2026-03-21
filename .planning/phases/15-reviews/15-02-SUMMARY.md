---
phase: 15-reviews
plan: 02
subsystem: api
tags: [fastapi, antd, reviews, admin-panel, pagination, moderation]

# Dependency graph
requires:
  - phase: 15-reviews
    provides: Review model with status field, sentinel pattern, rating-based auto-publish
  - phase: 09-v2-models
    provides: Review model with booking_id FK, client/master relationships
provides:
  - Master-authenticated GET /reviews endpoint with status filter and pagination
  - PUT /reviews/{id}/reply endpoint that publishes review with master reply
  - Web admin ReviewsPage with Ant Design table, status filter, and reply modal
  - Sidebar navigation entry for reviews
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Review admin read includes joined client (name, phone) and booking->service (name)"
    - "Reply to review sets status=published (moderation gate release)"
    - "Segmented control for status filtering in admin table pages"

key-files:
  created:
    - backend/app/api/v1/reviews.py
    - web/src/api/reviews.ts
    - web/src/pages/ReviewsPage.tsx
  modified:
    - backend/app/api/v1/router.py
    - backend/app/schemas/review.py
    - web/src/App.tsx
    - web/src/layouts/AdminLayout.tsx

key-decisions:
  - "Reviews API uses get_db (not get_db_with_rls) since review filtering is done explicitly by master_id"
  - "Reply action publishes review regardless of original status (pending_reply or published without reply)"

patterns-established:
  - "Admin review listing pattern: selectinload client + booking->service for denormalized display"

requirements-completed: [REVW-02, REVW-03, REVW-05]

# Metrics
duration: 4min
completed: 2026-03-21
---

# Phase 15 Plan 02: Admin Reviews Management Summary

**Master-authenticated reviews API (list + reply) with Ant Design admin page featuring status filter, star ratings, and reply modal**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-21T07:09:12Z
- **Completed:** 2026-03-21T07:13:15Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- GET /reviews endpoint returns paginated reviews with client name/phone and service name, excluding request_sent sentinels
- PUT /reviews/{id}/reply sets master_reply, master_replied_at, and publishes the review
- ReviewsPage in web admin with Ant Design table (date, client, service, rating stars, text, status tag), Segmented status filter, and reply modal
- Sidebar menu item "Отзывы" with StarOutlined icon positioned between Payments and Settings

## Task Commits

Each task was committed atomically:

1. **Task 1: Admin reviews API + extended schemas** - `16d935c` (feat)
2. **Task 2: Web admin ReviewsPage** - `971df98` (feat)

## Files Created/Modified
- `backend/app/api/v1/reviews.py` - Master-authenticated list and reply endpoints
- `backend/app/schemas/review.py` - Extended with ReviewAdminRead, ReviewReplyRequest, ReviewsListResponse
- `backend/app/api/v1/router.py` - Registered reviews_router with /reviews prefix
- `web/src/api/reviews.ts` - React Query hooks for reviews API (useReviews, useReplyToReview)
- `web/src/pages/ReviewsPage.tsx` - Admin reviews page with table, status filter, reply modal
- `web/src/App.tsx` - Added /reviews route with ReviewsPage
- `web/src/layouts/AdminLayout.tsx` - Added sidebar menu item with StarOutlined icon

## Decisions Made
- Reviews API uses `get_db` instead of `get_db_with_rls` since review filtering is done explicitly by `master_id` check (consistent with security model)
- Reply action available for both `pending_reply` and `published` reviews without existing reply (master can add reply to any review)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Review system fully complete: collection (15-01) + management (15-02)
- Status flow: request_sent -> published (>=3 stars) or pending_reply (<3 stars) -> published (via master reply or 7-day auto-publish)
- Ready for Phase 16

## Self-Check: PASSED

All 7 files verified present. Both task commits (16d935c, 971df98) verified in git log.

---
*Phase: 15-reviews*
*Completed: 2026-03-21*
