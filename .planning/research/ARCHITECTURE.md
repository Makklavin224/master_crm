# Architecture Patterns

**Domain:** Multi-messenger CRM/booking system for self-employed professionals
**Researched:** 2026-03-17

## Recommended Architecture

A modular monolith deployed via Docker Compose. Not microservices -- this is a solo-developer product serving self-employed individuals, not a distributed team building for millions on day one. The monolith is structured with clean internal boundaries so individual components can be extracted later if needed, but the deployment unit is a single FastAPI application with clearly separated routers, services, and adapters.

```
                         +------------------+
                         |    Nginx (TLS)   |
                         |  Reverse Proxy   |
                         +--------+---------+
                                  |
                    +-------------+-------------+
                    |             |             |
              /api/*        /webhook/*     /admin/*
                    |             |             |
         +------------------------------------------+
         |            FastAPI Application            |
         |                                           |
         |  +----------+  +-----------+  +---------+ |
         |  | REST API |  | Webhook   |  | Admin   | |
         |  | (Mini    |  | Handlers  |  | API     | |
         |  |  Apps)   |  | (Bots)    |  | (Panel) | |
         |  +----+-----+  +-----+-----+  +----+----+ |
         |       |               |              |      |
         |  +----+---------------+--------------+----+ |
         |  |           Service Layer                | |
         |  |                                        | |
         |  |  BookingService  PaymentService        | |
         |  |  ScheduleService ClientService         | |
         |  |  NotificationService ReminderService   | |
         |  +----+---------------+--------------+----+ |
         |       |               |              |      |
         |  +----+-----+  +-----+-----+  +----+----+ |
         |  | Messenger |  | Payment   |  | Data    | |
         |  | Adapters  |  | Adapters  |  | Access  | |
         |  | (TG/MAX/  |  | (Robo-    |  | (SQLAlc | |
         |  |  VK)      |  |  kassa)   |  |  hemy)  | |
         |  +-----------+  +-----------+  +---------+ |
         +------------------------------------------+
                              |
                    +---------+---------+
                    |    PostgreSQL     |
                    |  (Single DB,     |
                    |   RLS per master)|
                    +------------------+
```

### Component Boundaries

| Component | Responsibility | Communicates With | Protocol |
|-----------|---------------|-------------------|----------|
| **Nginx** | TLS termination, static file serving, reverse proxy, rate limiting | FastAPI (upstream) | HTTP/HTTPS |
| **FastAPI App** | Request routing, auth, validation, response formatting | All internal services | In-process |
| **REST API Router** | Client-facing endpoints for mini-apps (booking, services, schedule) | Service Layer | In-process |
| **Webhook Router** | Receives updates from TG/MAX/VK bots and Robokassa callbacks | Messenger Adapters, Payment Adapter | In-process |
| **Admin API Router** | Master-facing endpoints for the web panel (CRUD, analytics, settings) | Service Layer | In-process |
| **Service Layer** | Core business logic (booking flow, payment processing, scheduling) | Data Access, Adapters | In-process |
| **Messenger Adapters** | Translate between platform-specific bot APIs and internal event format | TG API, MAX API, VK API | HTTPS (outbound) |
| **Payment Adapter** | Robokassa payment link generation, callback validation, receipt handling | Robokassa API | HTTPS (outbound) |
| **Data Access** | SQLAlchemy models, repositories, query logic | PostgreSQL | TCP (asyncpg) |
| **PostgreSQL** | Persistent storage with Row-Level Security per master (tenant) | Data Access Layer | TCP |
| **React Mini App** | Client booking interface (single codebase, 3 messenger deployments) | REST API | HTTPS |
| **React Admin Panel** | Master management interface (web-based, desktop-first) | Admin API | HTTPS |

### Data Flow

**Booking Flow (Client books appointment):**
```
Client opens Mini App in TG/MAX/VK
  --> Mini App loads master's services via REST API (GET /api/masters/{id}/services)
  --> Client picks service + time slot
  --> Mini App sends booking request (POST /api/bookings)
  --> BookingService validates slot availability (SELECT FOR UPDATE -- prevents double-booking)
  --> BookingService creates booking with status "pending"
  --> NotificationService sends confirmation to client via Messenger Adapter
  --> NotificationService sends new-booking alert to master via Messenger Adapter
  --> Response returned to Mini App with booking confirmation
```

**Payment Flow (After service is completed):**
```
Master taps "Complete" in Mini App or Admin Panel
  --> Admin API calls PaymentService.initiate_payment(booking_id)
  --> PaymentService calls Robokassa Adapter to generate SBP payment link
      (POST to auth.robokassa.ru/Merchant/Payment/Index with MerchantLogin, OutSum,
       InvId, SignatureValue signed with Password #1)
  --> Payment link sent to client via Messenger Adapter (bot message with inline button)
  --> Client pays via SBP
  --> Robokassa sends callback to ResultURL (POST /webhook/robokassa/result)
  --> PaymentService validates signature (Password #2), marks booking as "paid"
  --> Robokassa automatically generates receipt via Robochecks --> FNS "Moy Nalog"
  --> Client redirected to SuccessURL
  --> NotificationService confirms payment to both master and client via bots
```

**Reminder Flow (Automated):**
```
Scheduler (APScheduler or cron-based) runs every 15 minutes
  --> Queries bookings where:
      - status = "confirmed"
      - start_time is 24h away (not yet reminded_24h)
      - OR start_time is 2h away (not yet reminded_2h)
  --> For each, calls NotificationService
  --> NotificationService resolves client's messenger platform
  --> Sends reminder via appropriate Messenger Adapter
  --> Marks reminder as sent in DB
```

**Bot Message Flow (Incoming bot command/callback):**
```
User sends message or taps button in TG/MAX/VK
  --> Messenger platform sends update to webhook endpoint
      - TG: POST /webhook/telegram (validated by secret token)
      - MAX: POST /webhook/max (validated by token)
      - VK: POST /webhook/vk (validated by VK confirmation + secret)
  --> Webhook Router dispatches to appropriate Messenger Adapter
  --> Adapter normalizes update into internal IncomingEvent format
  --> EventHandler routes by event type (command, callback, text)
  --> Business logic executes via Service Layer
  --> Response formatted as OutgoingMessage (platform-agnostic)
  --> Messenger Adapter translates to platform-specific API call
  --> Sends response to user
```

## Patterns to Follow

### Pattern 1: Messenger Adapter (Strategy Pattern)

The single most important architectural pattern. All three messenger platforms speak different protocols, have different payload formats, and different capabilities. The adapter pattern isolates this complexity.

**What:** Abstract base class defining the messenger interface. Concrete implementations for TG, MAX, VK.

**When:** Every time the system sends or receives messages from any messenger.

**Example:**
```python
# adapters/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class MessengerPlatform(str, Enum):
    TELEGRAM = "telegram"
    MAX = "max"
    VK = "vk"

@dataclass
class IncomingEvent:
    """Platform-agnostic representation of an incoming message/callback."""
    platform: MessengerPlatform
    user_platform_id: str  # platform-specific user ID
    phone: str | None      # if available (MAX gives it, TG/VK may not)
    text: str | None
    callback_data: str | None
    raw: dict              # original payload for debugging

@dataclass
class OutgoingMessage:
    """Platform-agnostic representation of an outbound message."""
    text: str
    inline_buttons: list[dict] | None = None  # [{text, callback_data}]
    link_buttons: list[dict] | None = None     # [{text, url}]

class MessengerAdapter(ABC):
    @abstractmethod
    async def parse_update(self, raw_body: dict) -> IncomingEvent:
        """Normalize platform update into IncomingEvent."""
        ...

    @abstractmethod
    async def send_message(self, user_id: str, message: OutgoingMessage) -> None:
        """Send a message to a user on this platform."""
        ...

    @abstractmethod
    async def send_mini_app_button(self, user_id: str, text: str, url: str) -> None:
        """Send a button that opens the mini-app."""
        ...

# adapters/telegram.py
class TelegramAdapter(MessengerAdapter):
    """Uses aiogram's Bot object for sending. Parses aiogram Update for receiving."""

    async def parse_update(self, raw_body: dict) -> IncomingEvent:
        from aiogram.types import Update
        update = Update.model_validate(raw_body)
        # Extract message or callback_query
        ...

    async def send_message(self, user_id: str, message: OutgoingMessage) -> None:
        # Build InlineKeyboardMarkup from message.inline_buttons
        # Use self.bot.send_message()
        ...

# adapters/max_messenger.py
class MaxAdapter(MessengerAdapter):
    """Uses MAX Bot API via HTTPS requests to platform-api.max.ru."""
    ...

# adapters/vk.py
class VKAdapter(MessengerAdapter):
    """Uses VK Bot API for community bot messaging."""
    ...
```

**Confidence:** HIGH -- This is a well-established pattern for multi-platform bots. The key insight: aiogram handles TG natively, but MAX and VK need custom HTTP-based adapters since there are no mature Python frameworks equivalent to aiogram for those platforms.

### Pattern 2: Shared Database with Row-Level Security (Multi-Tenant Isolation)

**What:** Single PostgreSQL database, all masters' data in the same tables, isolated by `master_id` column with PostgreSQL RLS policies.

**When:** Every data access operation. The application sets the current tenant context, and PostgreSQL enforces row filtering automatically.

**Why not separate schemas/databases:** Each "master" (self-employed professional) is a lightweight tenant with tiny data volumes (dozens of clients, not millions). Schema-per-tenant would be massive operational overhead for zero benefit. Shared schema + RLS is the correct approach for this scale.

**Example:**
```sql
-- Enable RLS on bookings table
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;

-- Policy: masters can only see their own bookings
CREATE POLICY master_isolation ON bookings
    USING (master_id = current_setting('app.current_master_id')::uuid);

-- Set context in application before any query
SET LOCAL app.current_master_id = 'uuid-of-master';
```

```python
# middleware or dependency
async def set_tenant_context(
    db: AsyncSession = Depends(get_db),
    current_master: Master = Depends(get_current_master),
):
    await db.execute(
        text(f"SET LOCAL app.current_master_id = '{current_master.id}'")
    )
    return db
```

**Confidence:** HIGH -- PostgreSQL RLS is production-proven for this exact use case (AWS, Supabase, and others recommend it for multi-tenant SaaS).

### Pattern 3: Platform-Aware Mini App Shell

**What:** A thin platform detection layer at the React app root that detects which messenger opened the mini-app and provides platform-specific bridge methods via React Context.

**When:** App initialization. The mini-app must detect whether it runs inside TG WebApp, MAX WebView, or VK Mini App, then load the correct bridge SDK.

**Why this matters:** Each platform has its own initialization, user data access, and native UI capabilities. The mini-app shares 95% of its code across platforms -- only the "shell" differs.

**Example:**
```typescript
// platform/detect.ts
export type Platform = 'telegram' | 'max' | 'vk' | 'web';

export function detectPlatform(): Platform {
  if (window.Telegram?.WebApp) return 'telegram';
  if (window.MaxWebView) return 'max';  // MAX injects its bridge
  if (window.vkBridge) return 'vk';
  return 'web'; // fallback for direct browser access
}

// platform/context.tsx
interface PlatformBridge {
  platform: Platform;
  getUserData(): Promise<{ phone?: string; name?: string; avatarUrl?: string }>;
  hapticFeedback(type: 'light' | 'medium'): void;
  close(): void;
  expandView(): void;
}

// platform/bridges/telegram.ts
const telegramBridge: PlatformBridge = {
  platform: 'telegram',
  async getUserData() {
    const user = window.Telegram.WebApp.initDataUnsafe.user;
    return { name: `${user.first_name} ${user.last_name}`, phone: undefined };
  },
  hapticFeedback(type) {
    window.Telegram.WebApp.HapticFeedback.impactOccurred(type);
  },
  // ...
};
```

**Confidence:** MEDIUM -- The TG and VK patterns are well-documented. MAX mini-app bridge API specifics are less documented publicly (LOW confidence on MAX-specific APIs), but the architectural pattern is the same across all three.

### Pattern 4: Optimistic Slot Locking for Bookings

**What:** Use PostgreSQL `SELECT ... FOR UPDATE SKIP LOCKED` to prevent double-booking without Redis or external lock managers.

**When:** When a client attempts to book a time slot.

**Why not Redis locks:** Overkill for a solo-master CRM. A master has maybe 5-15 bookings per day. PostgreSQL row-level locks are perfectly sufficient and simpler to deploy.

**Example:**
```python
async def book_slot(
    db: AsyncSession,
    master_id: uuid.UUID,
    service_id: uuid.UUID,
    start_time: datetime,
) -> Booking | None:
    # Calculate end_time from service duration
    service = await db.get(Service, service_id)
    end_time = start_time + timedelta(minutes=service.duration_minutes)

    # Check for overlapping bookings with row lock
    result = await db.execute(
        select(Booking)
        .where(
            Booking.master_id == master_id,
            Booking.status.in_(["confirmed", "pending"]),
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
        .with_for_update(skip_locked=True)
    )

    if result.first():
        return None  # Slot is taken

    # Create booking
    booking = Booking(
        master_id=master_id,
        service_id=service_id,
        start_time=start_time,
        end_time=end_time,
        status="pending",
    )
    db.add(booking)
    await db.commit()
    return booking
```

**Confidence:** HIGH -- PostgreSQL row locking is the standard approach for booking systems at this scale.

### Pattern 5: Webhook Security Per Platform

**What:** Each messenger platform has its own webhook security mechanism. These must be validated before processing any update.

**When:** Every incoming webhook request.

**Example:**
```python
# Telegram: Validate secret token (set when registering webhook)
@router.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(...),
):
    if x_telegram_bot_api_secret_token != settings.TG_WEBHOOK_SECRET:
        raise HTTPException(403)
    body = await request.json()
    await telegram_adapter.handle_update(body)

# MAX: Validate token in request
@router.post("/webhook/max")
async def max_webhook(request: Request):
    body = await request.json()
    # MAX sends token that must match your bot token
    # Validate per MAX Bot API docs
    await max_adapter.handle_update(body)

# VK: Confirmation challenge + secret key validation
@router.post("/webhook/vk")
async def vk_webhook(request: Request):
    body = await request.json()
    if body.get("type") == "confirmation":
        return PlainTextResponse(settings.VK_CONFIRMATION_TOKEN)
    # Validate secret key
    if body.get("secret") != settings.VK_SECRET:
        raise HTTPException(403)
    await vk_adapter.handle_update(body)
    return PlainTextResponse("ok")

# Robokassa: Validate signature with Password #2
@router.post("/webhook/robokassa/result")
async def robokassa_result(request: Request):
    data = await request.form()
    # Verify: MD5(OutSum:InvId:Password#2:Shp_params)
    expected_sig = md5(f"{data['OutSum']}:{data['InvId']}:{settings.ROBOKASSA_PASS2}")
    if data["SignatureValue"].upper() != expected_sig.upper():
        raise HTTPException(403)
    await payment_service.handle_payment_callback(data)
    return PlainTextResponse(f"OK{data['InvId']}")
```

**Confidence:** HIGH for TG and Robokassa (well-documented). MEDIUM for MAX and VK (patterns are standard, specific details need verification against current docs).

## Anti-Patterns to Avoid

### Anti-Pattern 1: Platform Logic in Business Layer
**What:** Checking `if platform == 'telegram'` inside BookingService, PaymentService, etc.
**Why bad:** Creates spaghetti as platforms grow. Every new platform means touching core business logic. Testing becomes platform-dependent.
**Instead:** All platform-specific behavior lives in adapters. Business logic operates on platform-agnostic data structures (IncomingEvent, OutgoingMessage, Client, Booking).

### Anti-Pattern 2: Separate Backend Per Messenger
**What:** Running three separate FastAPI servers, one per platform.
**Why bad:** Triples deployment complexity. Code duplication. Database drift between instances. Nightmare to maintain for a solo developer.
**Instead:** Single FastAPI application with three webhook routes and a shared service layer.

### Anti-Pattern 3: Direct Bot Framework Integration in API Layer
**What:** Using aiogram's Router/Dispatcher directly inside FastAPI route handlers. Tightly coupling aiogram's update processing with your HTTP framework.
**Why bad:** Aiogram is designed for Telegram only. You cannot reuse its dispatcher for MAX or VK. If you build your Telegram bot deeply integrated with aiogram's middleware chain, you will have to build completely separate architectures for MAX and VK.
**Instead:** Use aiogram only for its `Bot` class (sending messages, managing webhooks) and `Update.model_validate()` for parsing. Feed raw updates into your own adapter layer, not aiogram's dispatcher. This way all three platforms use the same routing/handling architecture.

### Anti-Pattern 4: Microservices From Day One
**What:** Splitting BookingService, PaymentService, NotificationService into separate deployable services with message queues between them.
**Why bad:** A solo developer managing 5+ containers, message broker, service discovery, distributed tracing -- for a product that serves solo-master professionals with 10-50 clients each. Operational overhead kills velocity.
**Instead:** Modular monolith with clean internal boundaries. If BookingService needs NotificationService, it is a direct function call, not an HTTP request through a service mesh.

### Anti-Pattern 5: Client-Side Booking Validation Only
**What:** Checking slot availability only in the React mini-app before sending the booking request.
**Why bad:** Race condition. Two clients can see the same slot as "available" and both submit bookings. The server must be the single source of truth.
**Instead:** Client-side checks are optimistic UX only. The server performs atomic slot validation with `SELECT FOR UPDATE` before confirming any booking.

## Key Database Tables (Logical Schema)

```
masters
  id (PK, UUID)
  phone (unique, indexed)
  name
  business_name
  timezone
  subscription_tier
  robokassa_merchant_login  -- per-master Robokassa config (or shared with our account)
  created_at

master_schedules
  id (PK)
  master_id (FK -> masters)
  day_of_week (0-6)
  start_time (TIME)
  end_time (TIME)
  is_working (BOOL)
  break_start (TIME, nullable)
  break_end (TIME, nullable)

schedule_exceptions
  id (PK)
  master_id (FK -> masters)
  date (DATE)
  is_day_off (BOOL)
  custom_start (TIME, nullable)
  custom_end (TIME, nullable)
  reason (TEXT, nullable)

services
  id (PK)
  master_id (FK -> masters)
  name
  duration_minutes
  price_rub (DECIMAL)
  is_active (BOOL)
  sort_order

clients
  id (PK, UUID)
  phone (indexed, used for cross-platform identity)
  name
  created_at

client_platforms
  id (PK)
  client_id (FK -> clients)
  platform (ENUM: telegram, max, vk)
  platform_user_id (platform-specific ID)
  -- Composite unique: (platform, platform_user_id)

master_clients
  master_id (FK -> masters)
  client_id (FK -> clients)
  first_visit_at
  last_visit_at
  visit_count
  notes (nullable)
  -- Composite PK: (master_id, client_id)

bookings
  id (PK, UUID)
  master_id (FK -> masters, indexed, RLS column)
  client_id (FK -> clients)
  service_id (FK -> services)
  start_time (TIMESTAMPTZ, indexed)
  end_time (TIMESTAMPTZ)
  status (ENUM: pending, confirmed, completed, cancelled, no_show)
  source_platform (ENUM: telegram, max, vk, web)
  created_at
  -- Index: (master_id, start_time, status) for slot availability queries

payments
  id (PK, UUID)
  booking_id (FK -> bookings)
  master_id (FK -> masters, RLS column)
  amount_rub (DECIMAL)
  robokassa_inv_id (unique, indexed)
  status (ENUM: pending, paid, failed, refunded)
  payment_url (TEXT)
  paid_at (TIMESTAMPTZ, nullable)
  receipt_url (TEXT, nullable)  -- Robochecks receipt link
  created_at

reminders
  id (PK)
  booking_id (FK -> bookings)
  type (ENUM: 24h_before, 2h_before, custom)
  scheduled_at (TIMESTAMPTZ)
  sent_at (TIMESTAMPTZ, nullable)
  platform (ENUM: telegram, max, vk)  -- which platform to send via
```

**Key design decisions:**
- `clients.phone` is the cross-platform identity anchor. A client booking via TG and later via MAX is the same person if their phone matches.
- `client_platforms` is a separate table because one client may use multiple messengers.
- `master_clients` is the relationship table capturing per-master view of a client (visit history, notes).
- RLS is enforced on `bookings`, `payments`, `services`, `master_clients` via `master_id`.
- All timestamps are TIMESTAMPTZ because masters may be in different timezones.

## Scalability Considerations

| Concern | At 100 masters | At 10K masters | At 100K masters |
|---------|----------------|----------------|-----------------|
| **Database** | Single PostgreSQL, no tuning needed | Add read replicas, connection pooling (PgBouncer) | Consider partitioning bookings by date range |
| **Webhooks** | Single FastAPI process handles all | Gunicorn with 4-8 workers | Separate webhook receivers per platform, load balancer |
| **Bot sending** | Direct API calls | Rate limiting becomes important (TG: 30 msg/sec) | Message queue (Redis + Celery) for outbound messages |
| **Mini App** | Static files from Nginx | CDN (Cloudflare) | CDN + edge caching |
| **Payments** | Sequential Robokassa calls | Still fine (payment volume is low per master) | Robokassa handles scale on their end |
| **Background tasks** | APScheduler in-process | Still fine | Celery + Redis for distributed task execution |

**At MVP scale (target: first 100 masters):** A single VPS with Docker Compose (FastAPI + PostgreSQL + Nginx) handles everything comfortably. No Redis, no Celery, no message queues needed.

## Build Order (Dependencies)

The architecture implies a strict build order based on component dependencies:

```
Phase 1: Foundation
  [PostgreSQL schema + SQLAlchemy models]
  [FastAPI project structure with routers]
  [Auth system (master registration/login)]
  --> Everything depends on this

Phase 2: Core Business Logic
  [Service Layer: BookingService, ScheduleService, ServiceCatalog]
  [REST API endpoints for mini-app consumption]
  --> Depends on Phase 1

Phase 3: Mini App (Client-Facing)
  [React mini-app with platform detection shell]
  [Service catalog view, calendar/slot picker, booking flow]
  --> Depends on Phase 2 (needs API to talk to)

Phase 4: First Messenger (Telegram)
  [TG bot with aiogram (webhook mode)]
  [TelegramAdapter]
  [Mini-app launched via bot button]
  [Booking notifications via bot]
  --> Depends on Phase 2 + 3

Phase 5: Payments
  [Robokassa integration + Robochecks]
  [Payment flow: generate link -> callback -> receipt]
  [SBP payment via bot message]
  --> Depends on Phase 4 (needs working booking flow to test end-to-end)

Phase 6: Reminders
  [APScheduler for background tasks]
  [24h and 2h reminders via bot]
  --> Depends on Phase 4 (needs bot sending capability)

Phase 7: Admin Panel (Web)
  [React admin panel (separate app, same API)]
  [Schedule management, client list, booking management, payment history]
  --> Depends on Phase 2 (needs API), can start in parallel with Phase 4-6

Phase 8: Additional Messengers
  [MAX bot + MaxAdapter]
  [VK bot + VKAdapter]
  [Mini-app deployed to MAX and VK platforms]
  --> Depends on Phase 4 (reuses adapter pattern established for TG)
```

**Critical path:** Phase 1 -> 2 -> 3 -> 4 -> 5 is the minimum viable product.

**Parallel work:** Phase 7 (admin panel) can be developed in parallel with Phases 4-6 since it shares the same API.

**Phase 8 ordering rationale:** MAX and VK come last because (a) the adapter pattern is proven with TG first, (b) TG has the largest user base for initial validation, and (c) MAX/VK mini-app APIs have less community documentation, so having a working TG reference implementation reduces risk.

## Infrastructure Layout (Docker Compose)

```yaml
# docker-compose.yml (production)
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./certbot/conf:/etc/letsencrypt       # TLS certs
      - ./frontend/dist:/var/www/miniapp       # Mini-app static files
      - ./admin/dist:/var/www/admin            # Admin panel static files
    depends_on:
      - api

  api:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/mastercrm
      - TG_BOT_TOKEN=...
      - MAX_BOT_TOKEN=...
      - VK_TOKEN=...
      - ROBOKASSA_LOGIN=...
      - ROBOKASSA_PASS1=...
      - ROBOKASSA_PASS2=...
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=mastercrm
      - POSTGRES_USER=...
      - POSTGRES_PASSWORD=...
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      retries: 5

volumes:
  pgdata:
```

**Key decisions:**
- Nginx serves both mini-app and admin panel as static files (no separate frontend servers).
- Single `api` container runs FastAPI with Gunicorn + Uvicorn workers.
- PostgreSQL 16 for latest RLS improvements and performance.
- No Redis or message broker at MVP -- added when scale demands it.
- TLS via Certbot/Let's Encrypt mounted into Nginx.

## Sources

- [Aiogram webhook documentation](https://docs.aiogram.dev/en/latest/dispatcher/webhook.html) -- HIGH confidence
- [MAX Bot API documentation](https://dev.max.ru/docs-api) -- MEDIUM confidence (verified API structure)
- [MAX UI component library](https://dev.max.ru/ui) -- HIGH confidence (verified React component kit exists)
- [VK Bridge SDK](https://github.com/VKCOM/vk-bridge) -- HIGH confidence
- [VKUI Component Library](https://github.com/VKCOM/VKUI) -- HIGH confidence
- [tma.js SDK for Telegram Mini Apps](https://github.com/Telegram-Mini-Apps/telegram-apps) -- HIGH confidence
- [Robokassa API documentation](https://docs.robokassa.ru/) -- HIGH confidence
- [Robokassa Robochecks for self-employed](https://robokassa.com/online-check/robocheck-smz/) -- HIGH confidence
- [PostgreSQL RLS for multi-tenant isolation](https://www.crunchydata.com/blog/row-level-security-for-tenants-in-postgres) -- HIGH confidence
- [AWS multi-tenant RLS guide](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/) -- HIGH confidence
- [FastAPI Docker deployment guide](https://fastapi.tiangolo.com/deployment/docker/) -- HIGH confidence
- [Multi-channel bot abstraction patterns](https://dev.to/quintana/i-built-a-multi-channel-conversation-framework-in-python-heres-why-5fi9) -- MEDIUM confidence
- [Booking system concurrency patterns](https://medium.com/@abhishekranjandev/concurrency-conundrum-in-booking-systems-2e53dc717e8c) -- MEDIUM confidence
- [Vertabelo appointment scheduling schema](https://vertabelo.com/blog/a-database-model-to-manage-appointments-and-organize-schedules/) -- MEDIUM confidence
