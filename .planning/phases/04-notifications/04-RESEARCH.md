# Phase 4: Notifications - Research

**Researched:** 2026-03-18
**Domain:** Background task scheduling, automated reminders, booking confirmations, notification infrastructure
**Confidence:** HIGH

## Summary

Phase 4 adds automated client-facing notifications (booking confirmations, 24h/2h reminders with configurable intervals) and verifies master alert notifications already partially built in Phase 2. The existing `NotificationService` singleton + `MessengerAdapter` ABC + `TelegramAdapter` provide a solid foundation. The main new work is: (1) a background scheduler for timed reminders, (2) extending the adapter interface for client-facing messages, (3) notification settings on the Master model, (4) a `scheduled_reminders` table for idempotency tracking, and (5) frontend settings UI for notification preferences.

The project currently has no Redis service in docker-compose and no task queue installed. ARQ (the originally planned task queue) is now in maintenance-only mode. For this project's modest task volume (reminders for solo masters), **APScheduler 3.11 with AsyncIOScheduler** running inside the FastAPI process is the simplest, most reliable approach. It avoids adding Redis as a dependency, runs in-process with the existing event loop, and handles cron-like polling with database-backed job state via a `scheduled_reminders` table.

**Primary recommendation:** Use APScheduler 3.11 AsyncIOScheduler with a polling cron job (runs every 5 minutes) that queries upcoming bookings and sends due reminders. Track sent reminders in a `scheduled_reminders` PostgreSQL table for idempotency. No Redis needed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Client reminders include: service name + date/time, master name, inline "Отменить запись" button, address/note if master added one
- Example 24h: "Напоминаем: Маникюр завтра в 14:00 у мастера Анна. Адрес: ул. Ленина 5, кв 12. [Отменить запись]"
- Example 2h: "Через 2 часа: Маникюр в 14:00 у мастера Анна. [Отменить запись]"
- Timezone-aware: use master's timezone setting
- Idempotent: server restart doesn't cause duplicate reminders; past-due reminders skipped
- Booking confirmation sent immediately after client completes booking
- Confirmation content: service name, date/time, master name, address/note, inline "Отменить запись" + "Мои записи" buttons
- Master alerts already partially in Phase 2 -- verify and extend for new booking, cancellation, reschedule
- Master alerts include inline action buttons (confirm/reschedule options)
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

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NOTF-01 | Automated reminder to client 24h before visit via bot | APScheduler cron job polls bookings, sends via TelegramAdapter.send_reminder(), idempotency via scheduled_reminders table |
| NOTF-02 | Automated reminder to client 2h before visit via bot | Same mechanism as NOTF-01, configurable intervals on Master model |
| NOTF-03 | Booking confirmation to client immediately after booking | Extend booking_service.create_booking() to call send_booking_confirmation() after master notification |
| BOOK-07 | Master receives notification about new booking/cancellation via bot | Already partially working (_notify_master in booking_service.py). Verify, add inline action buttons, ensure reschedule notifications work |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| APScheduler | 3.11.2 | Cron-like job scheduling | Stable, production-ready, AsyncIOScheduler runs in-process with FastAPI event loop. No Redis needed. 15M+ downloads/month. |
| aiogram | 3.20+ (already installed) | Telegram bot messaging | Already in stack, InlineKeyboardButton for reminder action buttons |
| SQLAlchemy | 2.0+ (already installed) | scheduled_reminders table | Already in stack, Alembic migration for new table |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| zoneinfo | stdlib (3.12+) | Timezone conversion | Already used in codebase (callbacks.py), for master timezone-aware reminder timing |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| APScheduler in-process | ARQ + Redis | ARQ is in maintenance-only mode (since issue #510). Adds Redis dependency. More complex. Better for high-volume distributed workers. |
| APScheduler in-process | Celery Beat | Massive overkill. Sync-first, requires dedicated worker + broker. Wrong tool for solo-master CRM. |
| APScheduler in-process | Pure asyncio loop | Simpler but no persistence, no missed-job recovery, fragile to process restarts. |
| PostgreSQL idempotency table | Redis deduplication | Adds Redis dependency for a simple boolean check. PostgreSQL is already in stack. |

**Installation:**
```bash
cd backend && uv add apscheduler>=3.11.0
```

**Version verification:** APScheduler 3.11.2 released 2025-12-22, stable (Production/Stable). Python >=3.8. Note: APScheduler 4.x is still alpha (4.0.0a6) -- do NOT use it.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── services/
│   └── reminder_service.py     # Reminder scheduling + sending logic
├── bots/
│   └── common/
│       ├── adapter.py           # Extended: add send_reminder(), send_booking_confirmation()
│       └── notification.py      # Extended: add send_reminder(), send_booking_confirmation()
│   └── telegram/
│       ├── adapter.py           # Extended: implement send_reminder(), send_booking_confirmation()
│       └── handlers/
│           └── callbacks.py     # Extended: handle cancel_client:{booking_id} callback
├── models/
│   └── scheduled_reminder.py   # New: ScheduledReminder model
├── schemas/
│   └── settings.py             # Extended: NotificationSettings schema
├── api/v1/
│   └── settings.py             # Extended: notification settings endpoints
└── main.py                      # Extended: start/stop APScheduler in lifespan
```

### Pattern 1: Polling Cron with Idempotency Table
**What:** APScheduler runs a cron job every 5 minutes. The job queries all confirmed bookings with `starts_at` within the relevant reminder windows, checks the `scheduled_reminders` table for already-sent reminders, and sends only unsent ones.
**When to use:** Always -- this is the core reminder mechanism.
**Example:**
```python
# reminder_service.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_
from app.core.database import async_session_factory
from app.models.booking import Booking
from app.models.master import Master
from app.models.scheduled_reminder import ScheduledReminder

scheduler = AsyncIOScheduler(timezone="UTC")

async def process_pending_reminders():
    """Poll for bookings needing reminders. Runs every 5 minutes."""
    async with async_session_factory() as session:
        now = datetime.now(timezone.utc)

        # Find all masters with reminders enabled
        # For each master, check their configured intervals
        # Find bookings where starts_at - interval <= now
        # Skip if ScheduledReminder already exists for (booking_id, interval)
        # Send reminder, insert ScheduledReminder row
        # Commit
        ...

scheduler.add_job(
    process_pending_reminders,
    "interval",
    minutes=5,
    id="reminder_poll",
    replace_existing=True,
)
```

### Pattern 2: Immediate Booking Confirmation (Event-Driven)
**What:** When a booking is created, immediately send a confirmation message to the client via their platform.
**When to use:** In `booking_service.create_booking()`, after the existing `_notify_master()` call.
**Example:**
```python
# In booking_service.py, after _notify_master():
await _notify_client_confirmation(db, booking)

async def _notify_client_confirmation(db: AsyncSession, booking: Booking) -> None:
    """Send booking confirmation to client. Fire-and-forget."""
    try:
        # Load client platforms to find their messenger
        # Load master for name + address
        # Load service for name + time
        # Call notification_service.send_booking_confirmation(...)
    except Exception:
        logger.exception("Failed to send confirmation for booking %s", booking.id)
```

### Pattern 3: Notification Settings as Master Model Columns
**What:** Add notification preference columns directly to the Master model (same pattern as booking settings and payment settings).
**When to use:** Always -- consistent with existing settings pattern.
**Example:**
```python
# On Master model:
reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
reminder_1_hours: Mapped[int] = mapped_column(Integer, default=24, server_default=text("24"))
reminder_2_hours: Mapped[int | None] = mapped_column(Integer, nullable=True, default=2, server_default=text("2"))
address_note: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### Anti-Patterns to Avoid
- **Scheduling individual jobs per booking:** Do NOT create an APScheduler job for each booking. This doesn't scale and loses state on restart. Use the polling pattern instead.
- **Naive datetime comparison:** Always convert to master's timezone using `zoneinfo.ZoneInfo` before checking if "24 hours before" has passed. The master's `starts_at` is stored as UTC.
- **Blocking the event loop in the scheduler job:** The reminder job runs in the FastAPI event loop. Use `async_session_factory()` (already established pattern) and keep DB queries efficient.
- **Sending reminders without checking booking status:** Always verify `booking.status == "confirmed"` before sending. A cancelled booking should NOT trigger a reminder.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cron-like scheduling | Custom asyncio sleep loop | APScheduler AsyncIOScheduler | Handles missed executions, timezone awareness, job replacement on restart |
| Duplicate reminder prevention | In-memory set / Redis key | PostgreSQL `scheduled_reminders` table with UNIQUE constraint | Survives restarts, queryable, auditable |
| Timezone conversion | Manual UTC offset math | `zoneinfo.ZoneInfo(master.timezone)` | Already used in codebase (callbacks.py), handles all 11 Russian timezones correctly |
| Message formatting with buttons | Raw string concatenation per use | Dedicated format methods on TelegramAdapter | Consistent formatting, reusable across reminder types |

**Key insight:** The biggest temptation is to over-engineer the scheduler. This is a solo-master CRM -- there will be at most hundreds of bookings per day across all masters. A simple 5-minute polling loop with a PostgreSQL idempotency table is the correct solution. No Redis, no Celery, no distributed workers.

## Common Pitfalls

### Pitfall 1: Duplicate Reminders on Server Restart
**What goes wrong:** Server restarts and the scheduler re-runs the polling job. Without idempotency tracking, clients receive the same reminder twice.
**Why it happens:** In-memory tracking of "already sent" is lost on restart.
**How to avoid:** `scheduled_reminders` table with `UNIQUE(booking_id, reminder_type)` constraint. Before sending, check if row exists. INSERT on send. If INSERT fails (duplicate), skip silently.
**Warning signs:** Clients complaining about duplicate messages.

### Pitfall 2: Timezone Mismatch in Reminder Timing
**What goes wrong:** A master in Vladivostok (UTC+10) has a booking at 14:00 local time. The system calculates "24 hours before" using UTC, sending the reminder at 04:00 UTC (14:00 Vladivostok) minus 24h = 04:00 UTC previous day = 14:00 Vladivostok previous day. This is correct. But the 2-hour reminder: 04:00 UTC - 2h = 02:00 UTC = 12:00 Vladivostok. If the code mistakenly uses Moscow time, it sends at 05:00 Vladivostok.
**Why it happens:** Mixing timezone-naive and timezone-aware datetimes, or hardcoding Moscow time.
**How to avoid:** All `starts_at` values are already stored as UTC (`TIMESTAMPTZ`). Compare `now_utc` against `starts_at - timedelta(hours=interval)` directly in UTC. No timezone conversion needed for the comparison itself. Only convert to master's local timezone when formatting the display time in the message.
**Warning signs:** Reminders arriving at wrong times for non-Moscow masters.

### Pitfall 3: Sending Reminders for Cancelled Bookings
**What goes wrong:** A booking is cancelled after the 24h reminder was sent but before the 2h reminder. The 2h reminder fires for a cancelled booking.
**Why it happens:** Reminder job doesn't re-check booking status.
**How to avoid:** In the polling query, always filter `WHERE status = 'confirmed'`. Additionally, when a booking is cancelled or rescheduled, delete its pending `scheduled_reminders` rows (or mark them cancelled).
**Warning signs:** Clients getting "Your appointment in 2 hours" for a cancelled booking.

### Pitfall 4: Client Cannot Receive Bot Messages
**What goes wrong:** Reminder send fails because the client has never interacted with the bot directly (only used the mini-app). Telegram bots can only initiate messages to users who have sent `/start` or interacted with the bot.
**Why it happens:** Mini-app users may not have explicitly started a chat with the bot.
**How to avoid:** Track `can_receive_messages` per client platform. When the booking is created, if the client came through the mini-app (which requires bot interaction), they should be reachable. Log failures and don't retry endlessly -- mark the reminder as `failed` after 1 attempt.
**Warning signs:** High failure rate on reminder sends, `Forbidden: bot was blocked by the user` errors.

### Pitfall 5: APScheduler Job Not Starting
**What goes wrong:** The scheduler is created but `scheduler.start()` is never called, or it's called before the event loop is running.
**Why it happens:** Incorrect placement in FastAPI lifespan.
**How to avoid:** Start the scheduler in the `lifespan` async context manager, after DB verification. Shut it down in the yield cleanup.
**Warning signs:** No reminder jobs running, no logs from the scheduler.

## Code Examples

### Scheduled Reminder Model
```python
# models/scheduled_reminder.py
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class ScheduledReminder(Base):
    __tablename__ = "scheduled_reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        index=True,
    )
    reminder_type: Mapped[str] = mapped_column(
        String(20)
    )  # "reminder_24h", "reminder_2h", "confirmation", etc.
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, sent, failed, cancelled
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        UniqueConstraint(
            "booking_id", "reminder_type",
            name="uq_scheduled_reminders_booking_type"
        ),
    )
```

### MessengerAdapter Extension
```python
# Add to adapter.py MessengerAdapter ABC:
@abstractmethod
async def send_reminder(
    self,
    platform_user_id: str,
    service_name: str,
    booking_date: str,
    booking_time: str,
    master_name: str,
    address_note: str | None,
    booking_id: str,
    reminder_type: str,  # "24h", "2h", etc.
) -> bool:
    """Send a booking reminder to a client. Returns True on success."""
    ...

@abstractmethod
async def send_booking_confirmation(
    self,
    platform_user_id: str,
    service_name: str,
    booking_date: str,
    booking_time: str,
    master_name: str,
    address_note: str | None,
    booking_id: str,
    master_id: str,
) -> bool:
    """Send a booking confirmation to a client. Returns True on success."""
    ...
```

### TelegramAdapter Reminder Implementation
```python
# In telegram/adapter.py:
async def send_reminder(
    self,
    platform_user_id: str,
    service_name: str,
    booking_date: str,
    booking_time: str,
    master_name: str,
    address_note: str | None,
    booking_id: str,
    reminder_type: str,
) -> bool:
    if reminder_type == "24h":
        text = f"Напоминаем: <b>{service_name}</b> завтра в {booking_time} у мастера {master_name}."
    else:
        text = f"Через {reminder_type}: <b>{service_name}</b> в {booking_time} у мастера {master_name}."

    if address_note:
        text += f"\nАдрес: {address_note}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Отменить запись",
            callback_data=f"cancel_client:{booking_id}",
        )]
    ])

    try:
        await self._bot.send_message(
            chat_id=platform_user_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return True
    except Exception:
        logger.exception("Failed to send reminder to %s", platform_user_id)
        return False
```

### APScheduler in FastAPI Lifespan
```python
# In main.py lifespan:
from app.services.reminder_service import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing DB check and webhook registration ...

    # Start reminder scheduler
    scheduler.start()
    logger.info("Reminder scheduler started")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    # ... existing cleanup ...
```

### Master Model Notification Columns
```python
# Add to Master model:
# Phase 4: Notification settings
reminders_enabled: Mapped[bool] = mapped_column(
    Boolean, default=True, server_default=text("true")
)
reminder_1_hours: Mapped[int] = mapped_column(
    Integer, default=24, server_default=text("24")
)
reminder_2_hours: Mapped[int | None] = mapped_column(
    Integer, nullable=True, default=2, server_default=text("2")
)
address_note: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### Notification Settings Schema
```python
# In schemas/settings.py:
class NotificationSettings(BaseModel):
    reminders_enabled: bool
    reminder_1_hours: int
    reminder_2_hours: int | None
    address_note: str | None

    model_config = {"from_attributes": True}

class NotificationSettingsUpdate(BaseModel):
    reminders_enabled: bool | None = None
    reminder_1_hours: int | None = Field(default=None)
    reminder_2_hours: int | None = Field(default=None)
    address_note: str | None = None

    @field_validator("reminder_1_hours", "reminder_2_hours")
    @classmethod
    def validate_interval(cls, v: int | None) -> int | None:
        if v is not None and v not in (1, 2, 6, 12, 24):
            raise ValueError("Reminder interval must be 1, 2, 6, 12, or 24 hours")
        return v
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ARQ for async task queue | APScheduler 3.11 for in-process scheduling | ARQ entered maintenance mode (2025) | No Redis dependency needed for simple reminder polling |
| Celery for background tasks | APScheduler / asyncio-native solutions | 2024+ | Celery is overkill for async Python apps with modest task volume |
| Manual UTC offset math | `zoneinfo` stdlib module | Python 3.9+ | No pytz dependency, cleaner API, IANA timezone names |

**Deprecated/outdated:**
- ARQ: In maintenance-only mode per GitHub issue #510. Still works but no new features or active development.
- APScheduler 4.x: Still alpha (4.0.0a6 as of April 2025). Do NOT use for production. Stick with 3.11.x.
- pytz: Superseded by `zoneinfo` in Python 3.9+. This project already uses `zoneinfo`.

## Open Questions

1. **Client cancellation via reminder button**
   - What we know: The reminder message includes an "Отменить запись" inline button with `callback_data=f"cancel_client:{booking_id}"`
   - What's unclear: The existing `cancel:{id}` callback handler cancels as master (no deadline). For client cancellation via reminder, we need a separate handler that enforces the cancellation deadline.
   - Recommendation: Add a `cancel_client:{booking_id}` callback handler that calls `cancel_booking(cancelled_by="client")` with the master's deadline. This requires knowing the client's identity from the callback -- use the booking's client record to verify the caller is the client.

2. **Booking changes after reminder sent**
   - What we know: If a booking is rescheduled after the 24h reminder, the old reminder is stale.
   - What's unclear: Should we send a "Your booking has been rescheduled" notification? Should we delete old reminders and create new ones?
   - Recommendation: When a booking is rescheduled, delete all `scheduled_reminders` rows for that booking (they'll be re-evaluated by the next polling cycle with the new `starts_at`). Also send a reschedule notification to the client immediately.

3. **Retry logic for failed sends**
   - What we know: Telegram API can fail temporarily (rate limits, network issues).
   - What's unclear: How many retries? What interval?
   - Recommendation: Mark as `failed` on first failure. The next polling cycle (5 minutes later) will re-attempt if the reminder window hasn't passed. No explicit retry queue needed. After the booking time passes, skip it.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | `backend/pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `cd backend && uv run pytest tests/test_notifications.py -x` |
| Full suite command | `cd backend && uv run pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NOTF-01 | 24h reminder sent for confirmed booking | unit | `cd backend && uv run pytest tests/test_notifications.py::test_reminder_24h_sent -x` | No -- Wave 0 |
| NOTF-02 | 2h reminder sent for confirmed booking | unit | `cd backend && uv run pytest tests/test_notifications.py::test_reminder_2h_sent -x` | No -- Wave 0 |
| NOTF-01/02 | Duplicate reminders not sent (idempotency) | unit | `cd backend && uv run pytest tests/test_notifications.py::test_reminder_idempotent -x` | No -- Wave 0 |
| NOTF-01/02 | Reminders skipped for cancelled bookings | unit | `cd backend && uv run pytest tests/test_notifications.py::test_reminder_skipped_cancelled -x` | No -- Wave 0 |
| NOTF-01/02 | Past-due reminders not sent | unit | `cd backend && uv run pytest tests/test_notifications.py::test_reminder_past_due_skipped -x` | No -- Wave 0 |
| NOTF-03 | Confirmation sent immediately after booking | unit | `cd backend && uv run pytest tests/test_notifications.py::test_booking_confirmation_sent -x` | No -- Wave 0 |
| BOOK-07 | Master notified on new/cancel/reschedule | unit | `cd backend && uv run pytest tests/test_notifications.py::test_master_notification -x` | No -- Wave 0 |
| NOTF-01/02 | Timezone-aware scheduling | unit | `cd backend && uv run pytest tests/test_notifications.py::test_reminder_timezone -x` | No -- Wave 0 |
| Settings | Notification settings GET/PUT | integration | `cd backend && uv run pytest tests/test_settings.py -x` | Yes (extend) |

### Sampling Rate
- **Per task commit:** `cd backend && uv run pytest tests/test_notifications.py -x`
- **Per wave merge:** `cd backend && uv run pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_notifications.py` -- covers NOTF-01, NOTF-02, NOTF-03, BOOK-07
- [ ] Mock for `TelegramAdapter.send_reminder()` and `send_booking_confirmation()` in conftest
- [ ] Framework install: `uv add apscheduler>=3.11.0` -- APScheduler not yet installed

## Sources

### Primary (HIGH confidence)
- [APScheduler 3.11.2 PyPI](https://pypi.org/project/APScheduler/) -- verified version 3.11.2, released 2025-12-22, production/stable
- [APScheduler AsyncIOScheduler docs](https://apscheduler.readthedocs.io/en/3.x/modules/schedulers/asyncio.html) -- async integration pattern
- [ARQ v0.27.0 docs](https://arq-docs.helpmanual.io/) -- job_id uniqueness, defer_until API, cron_jobs
- [ARQ GitHub](https://github.com/python-arq/arq) -- maintenance-only mode confirmed (issue #510)
- [ARQ PyPI](https://pypi.org/project/arq/) -- v0.27.0 released 2026-02-02, maintenance-only

### Secondary (MEDIUM confidence)
- [APScheduler + FastAPI integration pattern](https://www.nashruddinamin.com/blog/running-scheduled-jobs-in-fastapi/) -- lifespan integration verified across multiple sources
- [FastAPI BackgroundTasks vs ARQ](https://davidmuraya.com/blog/fastapi-background-tasks-arq-vs-built-in/) -- comparison of approaches

### Tertiary (LOW confidence)
- None -- all critical claims verified with official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- APScheduler 3.11 is well-documented, stable, widely used. Decision to avoid ARQ backed by official maintenance-mode status.
- Architecture: HIGH -- Polling pattern with idempotency table is a well-established approach. Existing codebase patterns (settings columns, adapter ABC, fire-and-forget notifications) provide clear extension points.
- Pitfalls: HIGH -- Drawn from PITFALLS.md (Pitfall 7 timezone, Pitfall 11 reminder delivery) and verified against actual codebase patterns.

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable libraries, patterns won't change)
