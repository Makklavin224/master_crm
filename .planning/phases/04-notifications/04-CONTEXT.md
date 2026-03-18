# Phase 4: Notifications - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Add automated booking reminders (24h and 2h before visit) and immediate booking confirmations to clients via messenger bot. Ensure master alert notifications (new booking, cancellation, reschedule) work correctly. Add background task scheduler for timed reminders. Extend master settings with notification preferences.

</domain>

<decisions>
## Implementation Decisions

### Client Reminders (24h + 2h)
- Content includes: service name + date/time, master name, inline "Отменить запись" button, address/note if master added one
- Example 24h: "Напоминаем: Маникюр завтра в 14:00 у мастера Анна. Адрес: ул. Ленина 5, кв 12. [Отменить запись]"
- Example 2h: "Через 2 часа: Маникюр в 14:00 у мастера Анна. [Отменить запись]"
- Timezone-aware: use master's timezone setting
- Idempotent: server restart doesn't cause duplicate reminders; past-due reminders skipped

### Booking Confirmation
- Sent immediately after client completes booking
- Content: service name, date/time, master name, address/note
- Inline button "Отменить запись" + "Мои записи"

### Master Alert Notifications
- Already partially implemented in Phase 2 (NotificationService + TelegramAdapter)
- Verify and extend: ensure alerts work for new booking, cancellation, reschedule
- Include inline action buttons (confirm/reschedule options)

### Master Settings for Notifications
- Toggle: reminders on/off (default: on)
- Configurable intervals: master chooses from [1h, 2h, 6h, 12h, 24h] for each reminder
- Default: first reminder 24h, second reminder 2h
- Master can disable second reminder (or set custom interval)
- Address/note field in master profile for inclusion in reminders

### Claude's Discretion
- Background task scheduler choice (ARQ, Celery Beat, or simple asyncio loop)
- Reminder scheduling strategy (polling vs event-driven)
- How to handle booking changes after reminder is sent
- Retry logic for failed notification delivery

</decisions>

<canonical_refs>
## Canonical References

### Project Specs
- `.planning/REQUIREMENTS.md` — NOTF-01, NOTF-02, NOTF-03, BOOK-07

### Existing Code
- `backend/app/bots/common/adapter.py` — MessengerAdapter ABC (send_booking_notification already exists)
- `backend/app/bots/common/notification.py` — NotificationService singleton
- `backend/app/bots/telegram/adapter.py` — TelegramAdapter with HTML + inline buttons
- `backend/app/services/booking_service.py` — Booking CRUD with notification hooks
- `backend/app/api/v1/settings.py` — Master settings API (extend with notification prefs)
- `frontend/src/pages/master/Settings.tsx` — Settings screen (extend with notification section)

### Research
- `.planning/research/STACK.md` — ARQ task queue, Redis
- `.planning/research/PITFALLS.md` — Reminder idempotency, timezone handling

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `NotificationService` singleton with `register_adapter()` and `send_booking_notification()`
- `TelegramAdapter` with HTML formatting + InlineKeyboardButton
- `MessengerAdapter` ABC — extend with `send_reminder()` method
- Master model has `timezone` column
- Settings API with payment settings pattern (extend for notifications)

### Established Patterns
- Fire-and-forget notification calls in booking_service.py
- Inline keyboard buttons for actions in TG messages
- Settings stored as columns on Master model

### Integration Points
- Add `send_reminder()` to MessengerAdapter ABC + TelegramAdapter
- Add notification settings columns to Master model (migration)
- Add background scheduler service (new Docker container or inline)
- Extend Settings screen with notification section

</code_context>

<specifics>
## Specific Ideas

No specific requirements — standard notification patterns apply.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-notifications*
*Context gathered: 2026-03-18*
