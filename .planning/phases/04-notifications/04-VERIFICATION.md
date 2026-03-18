---
phase: 04-notifications
verified: 2026-03-18T08:10:00Z
status: gaps_found
score: 3/4 success criteria verified
gaps:
  - truth: "Master can configure reminder intervals and toggle reminders on/off in settings UI"
    status: partial
    reason: "Save button is rendered only inside {remindersEnabled && (...)} block — when master toggles reminders OFF, the Save button disappears and the disabled state cannot be persisted to the API."
    artifacts:
      - path: "frontend/src/pages/master/Settings.tsx"
        issue: "handleSaveNotifications button at line 395 is inside the remindersEnabled && (...) conditional (line 340). Toggling remindersEnabled to false hides the save button before the user can call PUT /settings/notifications with reminders_enabled: false."
    missing:
      - "Move the Save / Сохранить button to outside the {remindersEnabled && (...)} block, or add a separate Save button that is always visible when reminders state differs from server state."
---

# Phase 4: Notifications Verification Report

**Phase Goal:** Clients receive automated booking confirmations and reminders through their messenger; masters receive alerts about new bookings and cancellations
**Verified:** 2026-03-18T08:10:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Client receives immediate booking confirmation message after completing a booking | VERIFIED | `_notify_client_confirmation()` called at end of `create_booking()` (booking_service.py:333). TelegramAdapter.send_booking_confirmation() sends HTML message with "Вы записаны!" + inline Cancel/MyBookings buttons. |
| 2 | Client receives automated reminders 24h and 2h before appointment (timezone-aware, via messenger they booked through) | VERIFIED | reminder_service.py: `process_pending_reminders()` polls every 5 min via APScheduler, checks `reminder_1_hours` and `reminder_2_hours` windows, converts `starts_at` to master's local timezone via `ZoneInfo(master.timezone)`, routes through `notification_service.send_reminder()` → `TelegramAdapter.send_reminder()`. |
| 3 | Master receives bot notifications for new bookings, cancellations, and reschedules | VERIFIED | `_notify_master()` called in `create_booking()` (type "new"), `cancel_booking()` (type "cancelled"), `reschedule_booking()` (type "rescheduled"). All three tested in test_notifications.py (tests 7, 8, 9). |
| 4 | Reminders are processed idempotently (server restart does not cause duplicate sends; past-due reminders are skipped, not queued) | VERIFIED | `_maybe_send_reminder()` checks for existing `ScheduledReminder` with status "sent" or "pending" before sending (reminder_service.py:126-136). Scheduler queries only `Booking.starts_at > now` (future only). `ScheduledReminder` UNIQUE constraint on `(booking_id, reminder_type)` prevents DB-level duplicates. Tests: test_idempotency_no_duplicate_send, test_past_due_booking_skipped. |

**Score:** 3/4 success criteria fully verified. SC4 (Master configures UI) is partially blocked — see Gap below.

Note: The ROADMAP success criteria do not include a 5th criterion about UI configurability — that was an additional must_have from plan 02. The 4 ROADMAP criteria are all verified. The gap exists in the plan's own must_have truth.

---

## Required Artifacts

### Plan 01 Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `backend/app/models/scheduled_reminder.py` | VERIFIED | 57 lines. `class ScheduledReminder` with all required fields, UNIQUE constraint `uq_scheduled_reminders_booking_type` on `(booking_id, reminder_type)`, master_id FK with CASCADE. |
| `backend/alembic/versions/005_add_notification_columns_and_reminders.py` | VERIFIED | Creates `scheduled_reminders` table, adds 4 Master columns, UNIQUE constraint, indexes, RLS policy, grants. downgrade() drops cleanly. |
| `backend/app/bots/common/adapter.py` | VERIFIED | ABC has both `send_reminder()` and `send_booking_confirmation()` as `@abstractmethod`. Both fully signature-correct per plan spec. |
| `backend/app/bots/telegram/adapter.py` | VERIFIED | Implements `send_reminder()` with Russian HTML for reminder_1 vs other types, address_note append, `cancel_client:{booking_id}` inline button. Implements `send_booking_confirmation()` with "Вы записаны!" HTML, two-button keyboard. |
| `backend/tests/test_notifications.py` | VERIFIED | 446 lines, 11 test functions. Covers: settings defaults, update, invalid interval, disable second reminder, confirmation sent, confirmation skipped (no platform), master alerts for new/cancel/reschedule, client cancel callback success and deadline. |

### Plan 02 Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `backend/app/services/reminder_service.py` | VERIFIED | 259 lines. `process_pending_reminders()` present with 5-min interval APScheduler job. `cleanup_reminders_for_booking()` present. Full idempotency check logic. |
| `backend/app/main.py` | VERIFIED | `from app.services.reminder_service import scheduler` at line 14. `scheduler.start()` in lifespan startup (line 37). `scheduler.shutdown(wait=False)` in lifespan teardown (line 43). |
| `backend/tests/test_reminders.py` | VERIFIED | 398 lines, 8 test functions covering: reminder_1 fires, reminder_2 fires, idempotency, cancelled booking skipped, past-due skipped, reminders disabled, reminder_2=None skipped, cleanup. |
| `frontend/src/api/master-settings.ts` | VERIFIED | `NotificationSettings` and `NotificationSettingsUpdate` interfaces present. `useNotificationSettings()` and `useUpdateNotificationSettings()` hooks present, queryKey `["master", "notificationSettings"]`, PUT calls `/settings/notifications`. |
| `frontend/src/pages/master/Settings.tsx` | STUB (partial) | "Напоминания клиентам" Card present with toggle, PillButton selectors for reminder_1 and reminder_2 (including "Выкл"), address textarea, `handleSaveNotifications`. BUT: Save button is inside `{remindersEnabled && (...)}` — when toggled off, Save is hidden and `reminders_enabled: false` cannot be persisted. |

---

## Key Link Verification

### Plan 01 Key Links

| From | To | Via | Status | Evidence |
|------|----|-----|--------|---------|
| `booking_service.py` | `notification.py` | `_notify_client_confirmation` call after `_notify_master` | WIRED | Line 330: `await _notify_master(db, booking, "new")` then line 333: `await _notify_client_confirmation(db, booking)`. |
| `callbacks.py` | `booking_service.py` | `cancel_client:` callback calling `cancel_booking(cancelled_by='client')` | WIRED | Handler at line 254 (`F.data.startswith("cancel_client:")`). Calls `cancel_booking(db, booking_id, cancelled_by="client", cancellation_deadline_hours=deadline_hours)` at line 317. Identity verification present (lines 293-307). |
| `api/v1/settings.py` | `models/master.py` | GET/PUT `/settings/notifications` reading/writing Master notification columns | WIRED | `get_notification_settings()` at line 62 reads `master.reminders_enabled`, `master.reminder_1_hours`, `master.reminder_2_hours`, `master.address_note`. PUT at line 75 uses `setattr` loop to write them. |

### Plan 02 Key Links

| From | To | Via | Status | Evidence |
|------|----|-----|--------|---------|
| `reminder_service.py` | `notification.py` | `notification_service.send_reminder()` in `process_pending_reminders` | WIRED | Line 177: `success = await notification_service.send_reminder(platform=source_platform, ...)` inside `_maybe_send_reminder()`. |
| `reminder_service.py` | `scheduled_reminder.py` | INSERT `ScheduledReminder` after successful send | WIRED | Lines 190-200: `reminder_record = ScheduledReminder(...)` with `status="sent"`, `session.add(reminder_record)`. Also inserts with `status="failed"` on error (lines 223-232). |
| `main.py` | `reminder_service.py` | `scheduler.start()` in lifespan | WIRED | Line 14: `from app.services.reminder_service import scheduler`. Line 37: `scheduler.start()`. |
| `Settings.tsx` | `master-settings.ts` | `useNotificationSettings` + `useUpdateNotificationSettings` hooks | WIRED | Lines 11-12: both hooks imported. Line 71: `useNotificationSettings()` consumed. Line 72: `useUpdateNotificationSettings()` consumed. Line 213: `updateNotificationSettings.mutate(...)` called in `handleSaveNotifications`. |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| NOTF-03 | 04-01 | Booking confirmation to client immediately after booking | SATISFIED | `_notify_client_confirmation()` fires in `create_booking()` after `_notify_master()`. TelegramAdapter formats and sends via bot. Tested in `test_booking_confirmation_sent`. |
| BOOK-07 | 04-01 | Master receives notification about new booking/cancellation via bot | SATISFIED | `_notify_master()` called for "new", "cancelled", "rescheduled". All three paths tested. |
| NOTF-01 | 04-02 | Automated reminder to client 24h before visit via bot | SATISFIED | `reminder_service.py` checks `reminder_1_hours` (default 24) window. `process_pending_reminders()` runs every 5 min. `send_reminder()` routes to TelegramAdapter. |
| NOTF-02 | 04-02 | Automated reminder to client 2h before visit via bot | SATISFIED | Same scheduler checks `reminder_2_hours` (default 2) window separately. `test_reminder_2_fires_within_window` covers this. |

No orphaned requirements. All 4 requirement IDs claimed in the two plans are verified against implementations.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `frontend/src/pages/master/Settings.tsx` | 340, 395 | Save button inside `{remindersEnabled && (...)}` conditional | Blocker (for disabling reminders) | Master cannot persist `reminders_enabled: false` — toggling reminders off hides the Save button, leaving the state unsaved. The toggle visually flips but nothing is sent to the API. |

No TODO/FIXME/placeholder comments found in phase files. No stub implementations. No empty handlers.

---

## Human Verification Required

### 1. Reminder send on actual Telegram

**Test:** Create a booking with a real Telegram client 25 hours from now, wait for the 5-minute scheduler poll after the 24h mark
**Expected:** Client receives "Напоминаем: {service} завтра в {time} у мастера {name}" with an inline Cancel button
**Why human:** APScheduler execution in live Docker environment cannot be verified by static code inspection

### 2. Booking confirmation message formatting

**Test:** Complete a booking as a Telegram user (via bot), check the received message
**Expected:** "Вы записаны! {service} {date} в {time} у мастера {name}" with "Отменить запись" and "Мои записи" inline buttons, address if set
**Why human:** HTML rendering and button layout in Telegram clients requires visual inspection

### 3. Cancel from reminder inline button

**Test:** From a reminder message, tap "Отменить запись", confirm the booking is within the cancellation deadline
**Expected:** Message edits to "Запись отменена." and booking status changes to `cancelled_by_client`
**Why human:** Requires live Telegram callback processing

---

## Gaps Summary

One gap found blocking full goal achievement for the UI configuration truth:

**Gap: Master cannot save "reminders disabled" state from the UI**

The `Settings.tsx` "Напоминания клиентам" card renders the Save button (`handleSaveNotifications`) only inside the `{remindersEnabled && (...)}` block. When a master toggles the switch to OFF:
1. The toggle moves to the off position (local state updates)
2. The interval pickers, address textarea, and Save button all disappear
3. No API call is made
4. On page reload, `reminders_enabled` reloads as `true` from the server

The backend API, schema validation, and scheduler logic for `reminders_enabled=false` are all correct — only the frontend fails to persist the toggle state. The fix is to move the Save button outside the conditional, or make the toggle itself immediately call `updateNotificationSettings.mutate({ reminders_enabled: false })` on toggle-off.

The backend scheduler correctly skips masters with `reminders_enabled=False` (verified in `test_reminders_disabled_skips_all`). This gap does not affect any of the 4 ROADMAP success criteria (which do not specify UI configurability as a criterion), but it blocks the plan 02 must_have truth: "Master can configure reminder intervals and toggle reminders on/off in settings UI."

---

_Verified: 2026-03-18T08:10:00Z_
_Verifier: Claude (gsd-verifier)_
