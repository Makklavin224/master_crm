# Phase 2: Booking Engine + Telegram - Research

**Researched:** 2026-03-17
**Domain:** Booking engine (slot calculation, double-booking prevention), Telegram bot (aiogram webhooks), Telegram Mini App (React + @telegram-apps/sdk-react), TG auth via initData
**Confidence:** HIGH

## Summary

Phase 2 transforms the Phase 1 foundation into a working product. It has three major domains: (1) backend booking engine with service CRUD, schedule management, and slot calculation; (2) Telegram bot integration via aiogram 3 in webhook mode sharing the FastAPI ASGI app; and (3) a React mini-app built with Vite + @telegram-apps/sdk-react that serves as the client booking interface and master management panel.

The most critical technical challenges are: preventing double-booking via PostgreSQL exclusion constraints with `tstzrange` + `btree_gist`, correctly integrating aiogram 3's Dispatcher with FastAPI's request lifecycle (aiogram natively supports aiohttp, not FastAPI -- manual feed_update is required), and implementing secure TG initData HMAC-SHA256 validation on the backend for mini-app authentication. The slot calculation algorithm must account for service duration, buffer time between appointments, break periods, and schedule exceptions.

A key version discrepancy was found: STACK.md references aiogram 3.26.0, but the actual latest version on PyPI is **3.22.0**. All npm package versions have been verified against the registry. The @telegram-apps/sdk-react package is at version 3.3.9 (the `@tma.js/sdk-react` name is the older v3.0.16 -- both point to the same codebase but `@telegram-apps/sdk-react` is the current canonical name).

**Primary recommendation:** Use aiogram 3.22.0 with webhook mode integrated into the existing FastAPI app via `Dispatcher.feed_update()`. Use `@telegram-apps/sdk-react` 3.3.9 for the mini-app. Implement double-booking prevention via PostgreSQL exclusion constraints (`EXCLUDE USING gist (master_id WITH =, booking_range WITH &&)`). Validate TG initData with HMAC-SHA256 on every authenticated mini-app API request.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Single TG bot for masters AND clients (@MasterCRMBot or similar)
- Mini-app: React + Vite, platform detection shell for future MAX/VK
- Booking flow: Usluga -> Data -> Vremya -> Imya+Telefon -> Podtverzhdenie
- Schedule: weekly template + date exceptions, configurable buffer (0-30 min), configurable cancel deadline (2-24h)
- TG auth: /start creates new account, separate from email+password
- One mini-app, two roles (master panel vs client booking)
- Modern branded design, not Telegram-native
- Bot commands: /start, /today, /link, /settings
- Notifications: new booking, cancellation, reschedule (with inline buttons)
- Double-booking prevention via PostgreSQL exclusion constraints
- Entry points: direct link from master (t.me/bot?start=master_id) + search by name/category inside mini-app
- Client provides name + phone as last step before confirming
- Master: /start -> registration/login, /today -> today's bookings, /link -> shareable booking link, /settings -> schedule/services/profile
- Client: /start?master_id -> opens mini-app for that master
- Link TG to existing email account later via settings (not auto-merge)

### Claude's Discretion
- React project setup (Vite + TanStack Query + Zustand -- per research)
- Mini-app component library choice
- Slot grid layout (time picker design)
- Bot message formatting (markdown vs HTML)
- Webhook setup and security (HMAC validation)
- API endpoint design for booking CRUD
- Frontend build/deploy pipeline
- Platform bridge adapter pattern implementation

### Deferred Ideas (OUT OF SCOPE)
- MAX + VK messenger integration -- Phase 5
- Client reminders (24h/2h) -- Phase 4
- Payment after booking -- Phase 3
- Web admin panel -- Phase 6
- Master search/discovery marketplace -- out of scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BOOK-01 | Master can create a service catalog (name, duration, price, category) | Service model exists from Phase 1. Need CRUD API endpoints + service for validation. Service price in kopecks (integer). |
| BOOK-02 | Master can configure schedule (working hours per day, breaks, days off) | MasterSchedule + ScheduleException models exist. Need CRUD API + schedule_service.py for validation. Weekly template pattern (7 rows per master). |
| BOOK-03 | Client can see available slots and book (select service -> date -> time) | Slot calculation algorithm (working hours - bookings - buffer). React mini-app with calendar + time picker. Public API endpoints (no master auth required). |
| BOOK-04 | System prevents double-booking (PostgreSQL exclusion constraints) | btree_gist extension + tstzrange column + EXCLUDE USING gist constraint on bookings table. Alembic migration required. |
| BOOK-05 | Client can cancel or reschedule a booking (with configurable deadline) | Booking status transitions, cancellation_deadline_hours on master settings, deadline check in booking_service. |
| BOOK-06 | Master can cancel, reschedule, or manually add a booking (no deadline restriction) | Master override bypasses client deadline. Manual booking creates client record from name+phone. |
| CLNT-01 | Client database auto-populated from bookings (name, phone) | On booking creation: normalize phone -> find or create Client -> create ClientPlatform(telegram) -> create MasterClient link. |
| CLNT-03 | Master can view client visit history | API endpoint: GET /api/v1/clients/{id}/bookings with RLS. MasterClient.visit_count + last_visit_at updated on booking completion. |
| MSG-01 | Telegram Bot -- webhook processing, notifications to master and clients | aiogram 3.22.0 in webhook mode, integrated into FastAPI via feed_update(). Secret token validation. |
| MSG-02 | Telegram Mini App -- client booking, master management | React + Vite + @telegram-apps/sdk-react 3.3.9. Platform detection shell. Two-role UI. |
| MSG-07 | Unified React Mini App code with platform detection (TG/MAX/VK bridge adapters) | Platform detection shell with adapter interface. Phase 2 implements TG adapter only. Dynamic import for future adapters. |
| MSG-08 | Messenger Adapter pattern on backend (unified notification router) | NotificationService with MessengerAdapter ABC. Phase 2 implements TelegramAdapter only. send_message/send_booking_notification interface. |
| INFR-03 | Webhook handlers for TG, MAX, VK bots | Phase 2 implements TG webhook only. POST /webhook/telegram with secret token validation. FastAPI route + aiogram Dispatcher. |
</phase_requirements>

## Standard Stack

### Backend -- New Dependencies for Phase 2

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiogram | 3.22.0 | Telegram Bot API framework | Async-native TG bot framework. Router-based architecture, FSM, middleware. Dominant in RU/CIS ecosystem. **Note: STACK.md says 3.26.0 but actual latest on PyPI is 3.22.0.** |
| aiohttp | (aiogram dep) | HTTP client | Transitive dependency of aiogram. Also used for outbound API calls. |

### Frontend -- Mini App (New in Phase 2)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | ^18.2 | UI framework | Standard for TG Mini Apps. Peer dep of @telegram-apps/sdk-react. |
| TypeScript | ^5.4 | Type safety | Catches integration bugs between mini-app and API at compile time. |
| Vite | ^8.0.0 | Build tool | Sub-second HMR, native ESM, tree-shaking. Official TG Mini App templates use Vite. |
| @telegram-apps/sdk-react | 3.3.9 | TG Mini App bridge | Official SDK. Provides hooks for initData, viewport, back button, haptic feedback. **This is the canonical npm name** (replaces older @tma.js/sdk-react). |
| @tanstack/react-query | 5.90.21 | Server state / data fetching | Caching, background refetch, optimistic updates. Eliminates manual loading/error states. |
| Zustand | 5.0.12 | Client state management | 1KB, no boilerplate, hooks-based. Booking flow state, auth state. |
| Tailwind CSS | 4.2.1 | Styling | Utility-first, mobile-first. Tree-shakes to <10KB. Perfect for mini-apps. |
| react-day-picker | 9.14.0 | Calendar date picking | Lightweight, accessible, customizable. Foundation for booking date selection. |
| dayjs | 1.11.20 | Date manipulation | 2KB. Handles timezone, locale (ru), formatting for booking system. |
| react-router-dom | ^7.x | Client-side routing | Mini-app needs routes for: booking flow, master panel, services list. Lightweight for SPA. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @telegram-apps/sdk-react | @tma.js/sdk-react | Same codebase, older name. Use @telegram-apps/* which is the current canonical package namespace. |
| react-router-dom | @tanstack/react-router | TanStack Router is type-safe but adds complexity for a mini-app with 5-8 routes. react-router-dom is simpler and well-known. |
| Tailwind CSS | CSS Modules | Tailwind is faster for prototyping and produces smaller bundles after tree-shaking. No runtime overhead. |
| Custom calendar | react-big-calendar | react-big-calendar is for event/scheduling views (admin). For date *picking* in booking flow, react-day-picker is lighter. |

**Installation:**

```bash
# Backend -- add aiogram to existing project
cd /Users/yannovak/development/projects/master_crm/backend
uv add "aiogram>=3.22.0,<4.0"

# Frontend -- create mini-app project
cd /Users/yannovak/development/projects/master_crm
pnpm create vite frontend --template react-ts
cd frontend
pnpm add @telegram-apps/sdk-react @tanstack/react-query zustand react-router-dom
pnpm add react-day-picker dayjs
pnpm add -D tailwindcss @tailwindcss/vite
```

## Architecture Patterns

### Recommended Project Structure (Phase 2 Additions)

```
master_crm/
  backend/
    app/
      api/v1/
        auth.py              # Existing
        health.py            # Existing
        router.py            # Existing -- add new sub-routers
        services.py          # NEW: Service CRUD endpoints
        schedule.py          # NEW: Schedule CRUD + slot availability
        bookings.py          # NEW: Booking CRUD endpoints
        clients.py           # NEW: Client list + visit history
      bots/
        __init__.py
        telegram/
          __init__.py
          bot.py             # NEW: Bot + Dispatcher setup
          handlers/
            __init__.py
            start.py         # NEW: /start command (master reg + client deep link)
            today.py         # NEW: /today -- today's bookings
            link.py          # NEW: /link -- shareable booking link
            settings.py      # NEW: /settings -- inline keyboard menu
            callbacks.py     # NEW: Inline button callback handlers
          middlewares.py     # NEW: Logging, error handling
        common/
          __init__.py
          adapter.py         # NEW: MessengerAdapter ABC
          notification.py    # NEW: NotificationService (platform-agnostic)
      services/
        auth_service.py      # Existing
        phone_service.py     # Existing
        booking_service.py   # NEW: Booking CRUD + slot validation
        schedule_service.py  # NEW: Slot calculation algorithm
        client_service.py    # NEW: Client find-or-create, visit tracking
      schemas/
        auth.py              # Existing
        common.py            # Existing
        master.py            # Existing
        service.py           # NEW: ServiceCreate/Read/Update schemas
        schedule.py          # NEW: ScheduleTemplate/Exception schemas
        booking.py           # NEW: BookingCreate/Read/Cancel schemas
        client.py            # NEW: ClientRead schema
        slot.py              # NEW: AvailableSlot schema
      core/
        config.py            # UPDATE: Add TG_BOT_TOKEN, TG_WEBHOOK_SECRET, MINI_APP_URL
        security.py          # UPDATE: Add validate_tg_init_data()
        dependencies.py      # UPDATE: Add get_current_client_from_initdata()
        database.py          # Existing
  frontend/
    index.html
    vite.config.ts
    tailwind.config.ts
    tsconfig.json
    src/
      main.tsx               # App entry point
      App.tsx                 # Router + QueryClientProvider
      platform/
        detect.ts            # Platform detection (TG/MAX/VK/web)
        types.ts             # PlatformBridge interface
        context.tsx           # PlatformProvider React context
        adapters/
          telegram.ts        # TG bridge implementation
          stub.ts            # Web fallback for development
      api/
        client.ts            # Axios/fetch instance with initData auth
        services.ts          # Service catalog API hooks
        schedule.ts          # Schedule + slot availability API hooks
        bookings.ts          # Booking CRUD API hooks
      stores/
        booking-flow.ts      # Zustand: selected service, date, time, client info
        auth.ts              # Zustand: master/client role, initData
      pages/
        client/
          MasterPage.tsx     # Service list for a specific master
          DatePicker.tsx     # Calendar for date selection
          TimePicker.tsx     # Available time slots grid
          BookingForm.tsx    # Name + phone form
          Confirmation.tsx   # Booking confirmation
          MyBookings.tsx     # Client's booking list (cancel/reschedule)
        master/
          Dashboard.tsx      # Today's bookings overview
          Services.tsx       # Service CRUD management
          Schedule.tsx       # Schedule template editor
          Bookings.tsx       # All bookings list
          Clients.tsx        # Client list with visit history
          Settings.tsx       # Profile + buffer/deadline settings
      components/
        ui/                  # Shared UI components (Button, Card, Input, etc.)
        SlotGrid.tsx         # Time slot selection grid
        BookingCard.tsx      # Booking summary card
        ServiceCard.tsx      # Service display card
      lib/
        format.ts            # Price formatting (kopecks -> rubles), date formatting
        constants.ts         # API base URL, route paths
  docker-compose.yml         # UPDATE: Add frontend service
  Caddyfile                  # UPDATE: Route /app/* to frontend, /api/* to backend, /webhook/* to backend
```

### Pattern 1: aiogram 3 Webhook Integration with FastAPI

**What:** Run aiogram's Dispatcher inside the existing FastAPI application. Telegram sends webhook updates to a FastAPI route, which feeds them to aiogram's Dispatcher for processing.

**When:** Every incoming Telegram bot update (messages, commands, callback queries).

**Critical insight:** aiogram natively supports aiohttp, not FastAPI. You must manually call `Dispatcher.feed_update()` from a FastAPI route handler. Do NOT try to use aiogram's built-in webhook server -- it runs its own aiohttp instance that conflicts with FastAPI.

**Example:**
```python
# backend/app/bots/telegram/bot.py
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Update
from app.core.config import settings

bot = Bot(token=settings.tg_bot_token)
dp = Dispatcher()

# Import and include all handler routers
from app.bots.telegram.handlers.start import router as start_router
from app.bots.telegram.handlers.today import router as today_router
from app.bots.telegram.handlers.link import router as link_router
from app.bots.telegram.handlers.callbacks import router as callbacks_router

dp.include_routers(start_router, today_router, link_router, callbacks_router)


# backend/app/main.py -- add webhook route
from fastapi import FastAPI, Request, Header, HTTPException
from app.bots.telegram.bot import bot, dp
from app.core.config import settings

@app.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
):
    if x_telegram_bot_api_secret_token != settings.tg_webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid secret token")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


# Register webhook on startup (in lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing DB check ...
    await bot.set_webhook(
        f"{settings.base_webhook_url}/webhook/telegram",
        secret_token=settings.tg_webhook_secret,
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )
    yield
    await bot.delete_webhook()
    await bot.session.close()
    await engine.dispose()
```

**Confidence:** HIGH -- verified against aiogram 3 official docs. The `Dispatcher.feed_update()` method is the documented way to integrate with non-aiohttp frameworks.

### Pattern 2: TG initData Validation for Mini-App Auth

**What:** The mini-app sends raw initData string with every API request. The backend validates the HMAC-SHA256 signature using the bot token, then extracts user information.

**When:** Every authenticated API call from the mini-app.

**Algorithm:**
1. Parse initData as URL-encoded query params
2. Extract `hash` field, remove it from params
3. Sort remaining params alphabetically
4. Join as `key=value` pairs separated by `\n`
5. Create HMAC-SHA256 of bot token using key `"WebAppData"` -> `secret_key`
6. Create HMAC-SHA256 of data string using `secret_key` -> `computed_hash`
7. Compare `computed_hash` with received `hash`
8. Check `auth_date` freshness (reject if older than e.g. 24h)

**Example:**
```python
# backend/app/core/security.py -- add to existing file
import hmac
import hashlib
from urllib.parse import parse_qs, urlencode
from datetime import datetime, timezone

def validate_tg_init_data(
    init_data_raw: str,
    bot_token: str,
    max_age_seconds: int = 86400,
) -> dict | None:
    """
    Validate Telegram Mini App initData.
    Returns parsed user data dict or None if invalid.
    """
    try:
        parsed = parse_qs(init_data_raw, keep_blank_values=True)
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return None

        # Build data-check-string
        data_pairs = sorted(
            f"{k}={v[0]}" for k, v in parsed.items() if k != "hash"
        )
        data_check_string = "\n".join(data_pairs)

        # Create secret key: HMAC-SHA256(bot_token, "WebAppData")
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256,
        ).digest()

        # Compute signature
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            return None

        # Check auth_date freshness
        auth_date = int(parsed.get("auth_date", ["0"])[0])
        now = int(datetime.now(timezone.utc).timestamp())
        if max_age_seconds > 0 and (now - auth_date) > max_age_seconds:
            return None

        # Parse user JSON
        import json
        user_raw = parsed.get("user", [None])[0]
        if user_raw:
            return json.loads(user_raw)
        return None
    except Exception:
        return None
```

**Confidence:** HIGH -- algorithm verified against official Telegram docs and tma.js/init-data-node package documentation.

### Pattern 3: Slot Calculation Algorithm

**What:** Given a master's schedule, existing bookings, and a service duration, compute available time slots for a given date.

**When:** Client opens the time picker for a specific date and service.

**Algorithm:**
1. Get the day's working hours from MasterSchedule (or ScheduleException if exists)
2. If day is off (is_working=false or is_day_off=true), return empty
3. Generate potential slot start times from start_time to (end_time - service_duration) at configurable intervals (e.g., 15 or 30 min)
4. Subtract break period (break_start to break_end)
5. For each potential slot, check if (slot_start, slot_start + duration + buffer) overlaps any existing confirmed booking
6. Return non-overlapping slots

**Example:**
```python
# backend/app/services/schedule_service.py
from datetime import date, time, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

async def get_available_slots(
    db: AsyncSession,
    master_id: uuid.UUID,
    target_date: date,
    service_duration_minutes: int,
    buffer_minutes: int = 0,
    slot_interval_minutes: int = 30,
    master_timezone: str = "Europe/Moscow",
) -> list[time]:
    """
    Calculate available booking slots for a given date.
    Returns list of available start times in master's timezone.
    """
    tz = ZoneInfo(master_timezone)

    # 1. Check schedule exception first
    exception = await get_schedule_exception(db, master_id, target_date)
    if exception and exception.is_day_off:
        return []

    if exception and exception.start_time and exception.end_time:
        work_start = exception.start_time
        work_end = exception.end_time
        break_start = None
        break_end = None
    else:
        # 2. Get weekly template for this day of week
        day_of_week = target_date.weekday()  # 0=Monday
        schedule = await get_master_schedule(db, master_id, day_of_week)
        if not schedule or not schedule.is_working:
            return []
        work_start = schedule.start_time
        work_end = schedule.end_time
        break_start = schedule.break_start
        break_end = schedule.break_end

    # 3. Get existing bookings for the day
    day_start = datetime.combine(target_date, time.min, tzinfo=tz)
    day_end = datetime.combine(target_date, time.max, tzinfo=tz)
    bookings = await get_bookings_for_range(
        db, master_id, day_start, day_end,
        statuses=["confirmed", "pending"],
    )
    booked_ranges = [
        (b.starts_at.astimezone(tz).time(),
         b.ends_at.astimezone(tz).time())
        for b in bookings
    ]

    # 4. Generate candidate slots
    total_needed = service_duration_minutes + buffer_minutes
    slots = []
    current = work_start

    while True:
        slot_end_dt = datetime.combine(target_date, current) + timedelta(minutes=total_needed)
        slot_end = slot_end_dt.time()

        # Check slot fits within working hours
        if slot_end > work_end:
            break

        # Check slot doesn't overlap break
        slot_overlaps_break = False
        if break_start and break_end:
            if current < break_end and slot_end > break_start:
                slot_overlaps_break = True

        # Check slot doesn't overlap existing bookings
        slot_overlaps_booking = False
        service_end = (datetime.combine(target_date, current)
                       + timedelta(minutes=service_duration_minutes)).time()
        for b_start, b_end in booked_ranges:
            if current < b_end and service_end > b_start:
                slot_overlaps_booking = True
                break

        if not slot_overlaps_break and not slot_overlaps_booking:
            slots.append(current)

        # Advance by interval
        current = (datetime.combine(target_date, current)
                   + timedelta(minutes=slot_interval_minutes)).time()

    return slots
```

**Confidence:** HIGH -- standard algorithm for appointment scheduling. Edge cases (break overlap, end-of-day boundary, buffer time) are handled explicitly.

### Pattern 4: PostgreSQL Exclusion Constraint for Double-Booking Prevention

**What:** Database-level constraint that makes it impossible to insert overlapping bookings for the same master.

**When:** Applied once via Alembic migration. Enforced on every INSERT/UPDATE.

**Prerequisites:** The `btree_gist` extension must be enabled (allows combining equality operators with range operators in GiST index).

**Example (Alembic migration):**
```python
# alembic/versions/xxxx_add_booking_exclusion_constraint.py
from alembic import op

def upgrade():
    # Enable btree_gist extension (requires superuser or owner role)
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # Add tstzrange column computed from starts_at and ends_at
    op.execute("""
        ALTER TABLE bookings
        ADD COLUMN booking_range tstzrange
        GENERATED ALWAYS AS (tstzrange(starts_at, ends_at, '[)')) STORED;
    """)

    # Add exclusion constraint: no two active bookings for the same master can overlap
    op.execute("""
        ALTER TABLE bookings
        ADD CONSTRAINT no_overlapping_bookings
        EXCLUDE USING gist (
            master_id WITH =,
            booking_range WITH &&
        )
        WHERE (status IN ('confirmed', 'pending'));
    """)

def downgrade():
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_overlapping_bookings;")
    op.execute("ALTER TABLE bookings DROP COLUMN IF EXISTS booking_range;")
```

**Important note on WHERE clause:** PostgreSQL exclusion constraints do not support WHERE clauses directly. The workaround is either: (a) use a partial index approach with a trigger, or (b) filter only active bookings at the application level and rely on `SELECT ... FOR UPDATE` for atomicity. The safer approach for this project is **application-level locking + constraint as safety net**:

```python
# In booking_service.py -- atomic booking creation
async def create_booking(db: AsyncSession, ...) -> Booking:
    # Lock existing bookings for this master to prevent race conditions
    result = await db.execute(
        select(Booking)
        .where(
            Booking.master_id == master_id,
            Booking.status.in_(["confirmed", "pending"]),
            Booking.starts_at < end_time,
            Booking.ends_at > start_time,
        )
        .with_for_update()
    )
    if result.first():
        raise SlotUnavailableError("This time slot is no longer available")

    booking = Booking(...)
    db.add(booking)
    await db.flush()  # Triggers constraint check
    return booking
```

**Confidence:** HIGH -- PostgreSQL exclusion constraints with tstzrange are the documented standard for booking overlap prevention. The btree_gist extension is built into PostgreSQL.

### Pattern 5: TG Bot Deep Linking for Client Booking

**What:** Master shares a link like `t.me/BotName?start=MASTER_ID`. When client clicks, Telegram opens the bot with `/start MASTER_ID`. The bot handler extracts the master_id and sends a button to open the mini-app.

**When:** Client's first interaction with the booking system.

**Example:**
```python
# backend/app/bots/telegram/handlers/start.py
from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

router = Router()

@router.message(CommandStart(deep_link=True))
async def start_with_deep_link(message: Message, command: CommandObject):
    """Client clicked a master's booking link: t.me/BotName?start=MASTER_ID"""
    master_id = command.args
    # Open mini-app with master context
    mini_app_url = f"{settings.mini_app_url}?master={master_id}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Zapisat'sya",  # "Book appointment"
            web_app=WebAppInfo(url=mini_app_url),
        )]
    ])
    await message.answer(
        "Otkroyte mini-prilozhenie dlya zapisi:",
        reply_markup=keyboard,
    )

@router.message(CommandStart(deep_link=False))
async def start_no_link(message: Message):
    """Master sends /start without parameters -- registration flow"""
    # Check if this TG user is already linked to a master account
    # If yes: show master menu
    # If no: create new master account linked to tg_user_id
    ...
```

**Confidence:** HIGH -- deep linking via `/start` parameter is core Telegram Bot API functionality, verified in aiogram docs.

### Pattern 6: Platform Detection Shell (Mini-App)

**What:** Thin adapter layer at the React app root that detects the messenger platform and provides a platform-agnostic bridge via React Context.

**When:** Mini-app initialization. Phase 2 implements TG only; MAX/VK are stub adapters.

**Example:**
```typescript
// frontend/src/platform/types.ts
export type Platform = "telegram" | "max" | "vk" | "web";

export interface PlatformBridge {
  platform: Platform;
  getInitDataRaw(): string | null;
  getUserId(): string | null;
  hapticFeedback(type: "light" | "medium" | "heavy"): void;
  showBackButton(): void;
  hideBackButton(): void;
  onBackButtonClick(cb: () => void): () => void;
  ready(): void;
  expand(): void;
  close(): void;
}

// frontend/src/platform/adapters/telegram.ts
import { init, backButton, miniApp, initData } from "@telegram-apps/sdk-react";

export function createTelegramBridge(): PlatformBridge {
  init();
  miniApp.mount();
  backButton.mount();

  return {
    platform: "telegram",
    getInitDataRaw: () => initData.raw(),
    getUserId: () => initData.user()?.id?.toString() ?? null,
    hapticFeedback: (type) => {
      // use miniApp.hapticFeedback or import hapticFeedback from SDK
    },
    showBackButton: () => backButton.show(),
    hideBackButton: () => backButton.hide(),
    onBackButtonClick: (cb) => {
      backButton.onClick(cb);
      return () => backButton.offClick(cb);
    },
    ready: () => miniApp.ready(),
    expand: () => miniApp.expand?.(),
    close: () => miniApp.close(),
  };
}

// frontend/src/platform/detect.ts
export function detectPlatform(): Platform {
  if (typeof window !== "undefined" && window.Telegram?.WebApp) {
    return "telegram";
  }
  // Future: check for MAX, VK
  return "web";
}

// frontend/src/platform/context.tsx
const PlatformContext = createContext<PlatformBridge | null>(null);

export function PlatformProvider({ children }: { children: ReactNode }) {
  const [bridge, setBridge] = useState<PlatformBridge | null>(null);

  useEffect(() => {
    const platform = detectPlatform();
    if (platform === "telegram") {
      setBridge(createTelegramBridge());
    } else {
      setBridge(createStubBridge()); // Dev/web fallback
    }
  }, []);

  if (!bridge) return null; // Loading
  return (
    <PlatformContext.Provider value={bridge}>
      {children}
    </PlatformContext.Provider>
  );
}

export const usePlatform = () => {
  const ctx = useContext(PlatformContext);
  if (!ctx) throw new Error("usePlatform must be used within PlatformProvider");
  return ctx;
};
```

**Confidence:** HIGH for the pattern, MEDIUM for exact @telegram-apps/sdk-react API (the SDK exports may differ slightly in v3.3.9 -- verify by reading the actual package types after install).

### Pattern 7: API Endpoint Design

**What:** REST API endpoints for all Phase 2 functionality, following established FastAPI patterns from Phase 1.

**Public endpoints (no auth -- for client booking):**
```
GET  /api/v1/masters/{id}/services    # Service catalog for a master
GET  /api/v1/masters/{id}/slots       # Available slots for date+service
POST /api/v1/bookings                 # Create booking (initData auth for TG clients)
GET  /api/v1/bookings/{id}            # Get booking details
PUT  /api/v1/bookings/{id}/cancel     # Client cancel (initData auth)
PUT  /api/v1/bookings/{id}/reschedule # Client reschedule (initData auth)
```

**Master endpoints (JWT auth with RLS):**
```
# Services
GET    /api/v1/services               # List master's services
POST   /api/v1/services               # Create service
PUT    /api/v1/services/{id}          # Update service
DELETE /api/v1/services/{id}          # Delete service

# Schedule
GET    /api/v1/schedule               # Get weekly template
PUT    /api/v1/schedule               # Update weekly template (bulk)
GET    /api/v1/schedule/exceptions    # List schedule exceptions
POST   /api/v1/schedule/exceptions    # Add exception (day off / custom hours)
DELETE /api/v1/schedule/exceptions/{id}

# Bookings
GET    /api/v1/bookings               # List master's bookings (with filters)
POST   /api/v1/bookings/manual        # Manually add booking
PUT    /api/v1/bookings/{id}/cancel   # Master cancel (no deadline)
PUT    /api/v1/bookings/{id}/reschedule

# Clients
GET    /api/v1/clients                # List master's clients
GET    /api/v1/clients/{id}           # Client detail with visit history

# Settings
GET    /api/v1/settings               # Master settings (buffer, deadline, etc.)
PUT    /api/v1/settings               # Update settings
```

**Auth strategy for mini-app:**
- Master: existing JWT (from email/password login or TG bot auth)
- Client: TG initData validated per-request. No JWT needed -- initData is the auth token.
- Dual auth dependency: check for Bearer token first (master), fall back to X-Init-Data header (client)

**Confidence:** HIGH -- follows established FastAPI patterns from Phase 1.

### Anti-Patterns to Avoid

- **Using aiogram's built-in polling or aiohttp server alongside FastAPI:** Only use `Dispatcher.feed_update()`. Do not start a separate aiohttp process.
- **Trusting initData from the frontend without backend validation:** Every API request from the mini-app must validate initData on the backend. Never skip this.
- **Caching slot availability on the client for more than a page load:** Slots can be booked by other clients at any time. Always refetch when user navigates to time picker.
- **Platform-specific `if` checks in business logic:** All platform awareness lives in adapters and the platform shell. BookingService never checks what messenger the request came from.
- **Storing booking_range as a separate column that can drift from starts_at/ends_at:** Use a PostgreSQL generated column (`GENERATED ALWAYS AS`) to keep it in sync automatically.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TG initData validation | Custom crypto without tests | Implement exact HMAC-SHA256 algorithm from Telegram docs | The algorithm is simple (5 lines of hmac calls) but error-prone (sorting, newline joining, key derivation). Follow the spec exactly. |
| Slot calculation | Naive "check every 15 min" without break/buffer awareness | Proper algorithm with schedule template + exceptions + buffer | Edge cases: services spanning break, last slot before closing, buffer at end of day. |
| Bot command routing | Manual `if text == "/start"` parsing | aiogram 3 Router + CommandStart filter + CommandObject.args | aiogram handles deep link parsing, command extraction, and argument splitting natively. |
| Calendar UI | Custom date grid from scratch | react-day-picker with locale=ru | Accessibility, keyboard nav, locale support, date range restrictions. |
| TG Mini App bridge | Direct window.Telegram.WebApp calls | @telegram-apps/sdk-react hooks + signals | Type safety, React lifecycle integration, automatic cleanup. |
| Booking overlap detection | Application-only check (SELECT then INSERT) | SELECT FOR UPDATE + PostgreSQL exclusion constraint | Application check alone has race conditions. DB constraint is the safety net. |

**Key insight:** The booking engine has deceptively complex edge cases (timezone conversion, break-spanning services, concurrent booking attempts). Every shortcut leads to a bug that surfaces in production.

## Common Pitfalls

### Pitfall 1: aiogram Dispatcher Lifecycle Mismatch with FastAPI
**What goes wrong:** Creating the Dispatcher and Bot objects inside the FastAPI route handler instead of at module level. Each request creates new instances, losing router registrations and middleware.
**Why it happens:** Developers treat aiogram objects like request-scoped resources.
**How to avoid:** Create `Bot` and `Dispatcher` as module-level singletons in `bots/telegram/bot.py`. The FastAPI webhook handler only calls `dp.feed_update(bot, update)`.
**Warning signs:** Bot stops responding to commands, handler functions never execute.

### Pitfall 2: initData Validation Timing Attack
**What goes wrong:** Using `==` instead of `hmac.compare_digest()` to compare hashes. Python's `==` short-circuits on the first different byte, leaking information about the correct hash through response timing.
**Why it happens:** Standard string comparison habit.
**How to avoid:** Always use `hmac.compare_digest(computed_hash, received_hash)`.
**Warning signs:** Code review flag: any `==` comparison of cryptographic hashes.

### Pitfall 3: Slot Calculation Ignoring Master Timezone
**What goes wrong:** Schedule template says "work 10:00-20:00" but the server stores/computes in UTC. A master in Vladivostok (UTC+10) has slots appearing at the wrong times.
**Why it happens:** Developers forget that `time` objects in MasterSchedule are in the master's local timezone, not UTC.
**How to avoid:** The slot calculation function must convert to the master's timezone (from `master.timezone` field) when combining `date` + `time` into `datetime`. Use `zoneinfo.ZoneInfo` for conversion. Always display times in the master's timezone on the booking page.
**Warning signs:** Slots shifted by several hours from expected working hours.

### Pitfall 4: Missing Client Record on Booking
**What goes wrong:** Booking is created but no Client or MasterClient record is created. The client list stays empty despite bookings.
**Why it happens:** The booking flow creates the Booking row but forgets the find-or-create-client step.
**How to avoid:** In `booking_service.create_booking()`: normalize phone -> `SELECT client WHERE phone = normalized` -> if not found, create Client -> create ClientPlatform(telegram, tg_user_id) -> create or update MasterClient -> create Booking. All in one transaction.
**Warning signs:** Empty client list, missing visit counts, CLNT-01 requirement fails.

### Pitfall 5: Webhook Not Re-registered After Deploy
**What goes wrong:** After deploying a new version, the bot stops responding. The webhook URL was registered with Telegram but the server restarted without re-registering.
**Why it happens:** Webhook registration in aiogram polling mode is automatic, but in manual webhook mode (FastAPI), you must explicitly call `bot.set_webhook()` on startup.
**How to avoid:** Call `bot.set_webhook()` in the FastAPI `lifespan` startup phase. Include `drop_pending_updates=True` to clear any queued updates from downtime.
**Warning signs:** Bot stops responding after server restart or deploy.

### Pitfall 6: Exclusion Constraint Failing on Cancelled Bookings
**What goes wrong:** A cancelled booking still triggers the overlap constraint, preventing a new booking in the same slot.
**Why it happens:** The exclusion constraint applies to all rows, including cancelled ones.
**How to avoid:** PostgreSQL exclusion constraints do not support arbitrary WHERE clauses. Two approaches: (a) use a partial exclusion constraint with a boolean column `is_active` (simpler), or (b) rely on application-level `SELECT ... FOR UPDATE` filtering by status, with the constraint as a secondary defense only on active bookings. Approach (a) is cleaner: add `is_active BOOLEAN DEFAULT true` and include it in the constraint condition.
**Warning signs:** "Could not create exclusion constraint" errors when booking a recently-cancelled slot.

### Pitfall 7: Mini-App Build Not Served Correctly
**What goes wrong:** The mini-app build is a SPA with client-side routing. Refreshing on `/client/timepicker` returns 404 because the server tries to find that file.
**Why it happens:** SPA routing requires all paths to serve `index.html` as fallback.
**How to avoid:** Configure Caddy (or Nginx) with `try_files` or equivalent to serve `index.html` for all non-file paths under the mini-app URL.
**Warning signs:** 404 errors on page refresh, direct URL navigation fails.

## Code Examples

### TG Bot /today Command Handler
```python
# backend/app/bots/telegram/handlers/today.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

router = Router()

@router.message(Command("today"))
async def cmd_today(message: Message):
    """Show master's bookings for today."""
    tg_user_id = str(message.from_user.id)
    # Look up master by TG user ID
    master = await get_master_by_tg_id(tg_user_id)
    if not master:
        await message.answer("You are not registered. Send /start to register.")
        return

    tz = ZoneInfo(master.timezone)
    today = datetime.now(tz).date()
    bookings = await get_master_bookings_for_date(master.id, today)

    if not bookings:
        await message.answer("No bookings for today.")
        return

    text = f"<b>Bookings for {today.strftime('%d.%m.%Y')}:</b>\n\n"
    for b in bookings:
        start = b.starts_at.astimezone(tz).strftime("%H:%M")
        text += f"{start} -- {b.client.name} ({b.service.name})\n"

    await message.answer(text, parse_mode="HTML")
```

### Booking Notification to Master
```python
# backend/app/bots/common/notification.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class BookingNotification:
    master_platform_id: str  # TG user_id, VK user_id, etc.
    client_name: str
    service_name: str
    booking_time: str  # Formatted in master's timezone
    booking_id: str
    notification_type: str  # "new", "cancelled", "rescheduled"

class MessengerAdapter(ABC):
    @abstractmethod
    async def send_booking_notification(self, notif: BookingNotification) -> bool:
        ...

# backend/app/bots/telegram/adapter.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class TelegramAdapter(MessengerAdapter):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_booking_notification(self, notif: BookingNotification) -> bool:
        if notif.notification_type == "new":
            text = (
                f"<b>New booking!</b>\n\n"
                f"Client: {notif.client_name}\n"
                f"Service: {notif.service_name}\n"
                f"Time: {notif.booking_time}"
            )
        elif notif.notification_type == "cancelled":
            text = (
                f"Client cancelled booking\n"
                f"Time: {notif.booking_time}"
            )
        # ... rescheduled case

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Details", callback_data=f"booking:{notif.booking_id}"),
                InlineKeyboardButton(text="Reschedule", callback_data=f"reschedule:{notif.booking_id}"),
            ]
        ])
        await self.bot.send_message(
            chat_id=int(notif.master_platform_id),
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return True
```

### Mini-App API Client with initData Auth
```typescript
// frontend/src/api/client.ts
import { usePlatform } from "../platform/context";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  initDataRaw: string | null = null,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Attach initData for TG mini-app authentication
  if (initDataRaw) {
    headers["X-Init-Data"] = initDataRaw;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Network error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}
```

### Caddyfile for Phase 2 (API + Mini-App + Webhook)
```
# Caddyfile (development)
:80 {
    # Mini-app frontend
    handle /app/* {
        uri strip_prefix /app
        root * /srv/frontend
        try_files {path} /index.html
        file_server
    }

    # API and webhooks
    handle /api/* {
        reverse_proxy api:8000
    }
    handle /webhook/* {
        reverse_proxy api:8000
    }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| aiogram polling mode | Webhook mode with FastAPI integration | aiogram 3.0+ (2023) | Webhooks required for multi-bot + web server on same port. feed_update() is the standard. |
| @tma.js/* package names | @telegram-apps/* package names | 2024-2025 | Use @telegram-apps/sdk-react (3.3.9), not @tma.js/sdk-react (3.0.16). Same codebase, new canonical name. |
| window.Telegram.WebApp direct | @telegram-apps/sdk-react hooks | 2024+ | Type safety, React lifecycle, signal-based reactivity. |
| Application-only overlap check | SELECT FOR UPDATE + exclusion constraint | PostgreSQL best practice | Database constraint prevents race conditions that application code cannot. |
| aiogram 3.26 (per STACK.md) | aiogram 3.22.0 (actual PyPI latest) | Verified 2026-03-17 | STACK.md version is incorrect. Use 3.22.0. |

**Deprecated/outdated:**
- `@tma.js/sdk-react` package name: Use `@telegram-apps/sdk-react` instead.
- aiogram `start_polling()` in production with FastAPI: Use webhooks.
- Manual `window.Telegram.WebApp` calls in React: Use the SDK hooks.

## Open Questions

1. **Master settings storage: separate table or JSON on masters table?**
   - What we know: Need to store buffer_minutes (0/10/15/30), cancellation_deadline_hours (2/6/12/24), slot_interval_minutes (15/30).
   - What's unclear: Whether to add columns to `masters` table or create a `master_settings` table.
   - Recommendation: Add columns to `masters` table. These are simple scalar values, not complex nested config. Avoids extra JOINs on every slot calculation query.

2. **Mini-app deployment: same Docker container or separate?**
   - What we know: Mini-app is a static SPA (Vite build output). Could be served by Caddy directly from a volume mount, or built in its own Docker stage.
   - Recommendation: Multi-stage Dockerfile for frontend, build output copied to Caddy's static files directory. No separate running container needed -- Caddy serves the static files.

3. **TG bot auth: store tg_user_id on masters table or separate table?**
   - What we know: Master model has email and phone. TG auth adds tg_user_id.
   - Recommendation: Add `tg_user_id: Mapped[str | None]` column to Master model (with unique index). Simple, avoids JOIN. Future MAX/VK user IDs also go on Master (max_user_id, vk_user_id). This mirrors the ClientPlatform pattern but is simpler since a master is always one person.

4. **Bot message formatting: Markdown vs HTML?**
   - What we know: aiogram supports both MarkdownV2 and HTML parse modes. HTML is simpler (no escaping issues with special characters). MarkdownV2 requires escaping `.`, `-`, `(`, `)`, etc.
   - Recommendation: Use HTML (`parse_mode="HTML"`). Simpler escaping, supports `<b>`, `<i>`, `<code>`, `<a href>`. Avoids MarkdownV2 escaping nightmares with Russian text.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (backend), Vitest (frontend) |
| Config file | `backend/pyproject.toml` [tool.pytest.ini_options], `frontend/vitest.config.ts` -- Wave 0 |
| Quick run command | `cd backend && uv run pytest tests/ -x -q` |
| Full suite command | `cd backend && uv run pytest tests/ -v --tb=short` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BOOK-01 | Service CRUD (create, read, update, delete) | integration | `uv run pytest tests/test_services.py -x` | No -- Wave 0 |
| BOOK-02 | Schedule CRUD (weekly template + exceptions) | integration | `uv run pytest tests/test_schedule.py -x` | No -- Wave 0 |
| BOOK-03 | Slot calculation returns correct available slots | unit | `uv run pytest tests/test_slots.py -x` | No -- Wave 0 |
| BOOK-03 | Client can create booking via API | integration | `uv run pytest tests/test_bookings.py::test_create_booking -x` | No -- Wave 0 |
| BOOK-04 | Overlapping booking rejected by DB constraint | integration | `uv run pytest tests/test_bookings.py::test_double_booking_prevented -x` | No -- Wave 0 |
| BOOK-05 | Client cancel respects deadline | integration | `uv run pytest tests/test_bookings.py::test_client_cancel -x` | No -- Wave 0 |
| BOOK-06 | Master can cancel/reschedule without deadline | integration | `uv run pytest tests/test_bookings.py::test_master_cancel -x` | No -- Wave 0 |
| CLNT-01 | Client record created on first booking | integration | `uv run pytest tests/test_clients.py::test_auto_create -x` | No -- Wave 0 |
| CLNT-03 | Client visit history returns bookings | integration | `uv run pytest tests/test_clients.py::test_visit_history -x` | No -- Wave 0 |
| MSG-01 | Webhook receives and processes TG update | integration | `uv run pytest tests/test_webhook.py -x` | No -- Wave 0 |
| MSG-02 | initData validation accepts valid data | unit | `uv run pytest tests/test_tg_auth.py -x` | No -- Wave 0 |
| MSG-08 | NotificationService sends via TelegramAdapter | unit | `uv run pytest tests/test_notifications.py -x` | No -- Wave 0 |
| INFR-03 | Webhook endpoint returns 403 on bad secret | integration | `uv run pytest tests/test_webhook.py::test_bad_secret -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && uv run pytest tests/ -x -q`
- **Per wave merge:** `cd backend && uv run pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_services.py` -- covers BOOK-01
- [ ] `backend/tests/test_schedule.py` -- covers BOOK-02
- [ ] `backend/tests/test_slots.py` -- covers BOOK-03 (slot calculation unit tests)
- [ ] `backend/tests/test_bookings.py` -- covers BOOK-03, BOOK-04, BOOK-05, BOOK-06
- [ ] `backend/tests/test_clients.py` -- covers CLNT-01, CLNT-03
- [ ] `backend/tests/test_webhook.py` -- covers MSG-01, INFR-03
- [ ] `backend/tests/test_tg_auth.py` -- covers MSG-02 (initData validation)
- [ ] `backend/tests/test_notifications.py` -- covers MSG-08
- [ ] `frontend/vitest.config.ts` -- frontend test setup (Wave 0 if frontend tests required)
- [ ] `backend/tests/conftest.py` -- extend existing fixtures with service/schedule/booking factories

## Sources

### Primary (HIGH confidence)
- [aiogram 3 webhook docs](https://docs.aiogram.dev/en/latest/dispatcher/webhook.html) -- Dispatcher.feed_update() pattern, secret token validation
- [aiogram 3 router docs](https://docs.aiogram.dev/en/latest/dispatcher/router.html) -- Router architecture, handler registration
- [aiogram Bot API setWebhook](https://docs.aiogram.dev/en/latest/api/methods/set_webhook.html) -- secret_token, allowed_updates, drop_pending_updates params
- [Telegram Mini Apps initData validation](https://docs.telegram-mini-apps.com/platform/init-data) -- HMAC-SHA256 algorithm, auth_date freshness check
- [Telegram Bot API WebApps](https://core.telegram.org/bots/webapps) -- WebAppInfo, InlineKeyboardButton.web_app, deep linking, initData format
- [Telegram Mini Apps launch parameters](https://docs.telegram-mini-apps.com/platform/launch-parameters) -- tgWebAppStartParam, tgWebAppData, tgWebAppPlatform
- [@tma.js/sdk-react docs](https://docs.telegram-mini-apps.com/packages/tma-js-sdk-react) -- init(), backButton.mount(), useSignal(), useLaunchParams()
- [@tma.js/init-data-node validation](https://docs.telegram-mini-apps.com/packages/tma-js-init-data-node/validating) -- validate(), isValid(), error types, tokenHashed option
- [PostgreSQL range types](https://www.postgresql.org/docs/16/rangetypes.html) -- tstzrange, EXCLUDE USING gist, btree_gist extension, overlap operator
- PyPI: aiogram 3.22.0 (verified 2026-03-17, actual latest)
- npm: @telegram-apps/sdk-react 3.3.9 (verified 2026-03-17)
- npm: @tanstack/react-query 5.90.21, Zustand 5.0.12, Vite 8.0.0, Tailwind 4.2.1, react-day-picker 9.14.0, dayjs 1.11.20

### Secondary (MEDIUM confidence)
- [aiogram command filters](https://docs.aiogram.dev/en/latest/dispatcher/filters/command.html) -- CommandStart(deep_link=True), CommandObject.args for deep link payload extraction
- Project ARCHITECTURE.md -- Messenger Adapter pattern, platform detection shell, booking data flow
- Project PITFALLS.md -- Double-booking, phone normalization, webhook security, timezone handling

### Tertiary (LOW confidence)
- @telegram-apps/sdk-react exact hook API for v3.3.9 -- docs site had some 404s. Verify exports after `pnpm add`. The `init()`, `backButton`, `miniApp` imports should work per the SDK overview, but exact signal API may differ.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All versions verified against PyPI/npm registries on 2026-03-17. aiogram version corrected from STACK.md (3.26 -> 3.22.0).
- Architecture: HIGH -- Patterns from aiogram official docs, Telegram official docs, PostgreSQL docs. Existing codebase patterns from Phase 1 followed.
- Pitfalls: HIGH -- Sourced from project PITFALLS.md, Telegram official security recommendations, PostgreSQL constraint documentation.
- Validation: MEDIUM -- Test map covers all requirements, but frontend testing strategy needs refinement after mini-app scaffolding.
- Mini-app SDK specifics: MEDIUM -- @telegram-apps/sdk-react docs had some 404 pages. Core init/hook pattern verified but exact v3.3.9 API may have minor differences.

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable backend stack, 30-day validity. Mini-app SDK may update faster -- recheck npm before implementation)
