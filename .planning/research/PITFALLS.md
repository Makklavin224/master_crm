# Domain Pitfalls

**Domain:** Multi-messenger CRM with booking/payments for self-employed professionals (Russia)
**Researched:** 2026-03-17

---

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or legal/financial consequences.

---

### Pitfall 1: Double Booking via Race Conditions

**What goes wrong:** Two clients simultaneously select the same time slot. Both see it as "available" and both submit bookings. Without proper concurrency control, the system creates two bookings for the same slot. The master shows up to find two clients expecting service at the same time.

**Why it happens:** The classic check-then-act race condition. The naive flow is: (1) read available slots, (2) check if slot is free, (3) insert booking. Between steps 2 and 3, another request can insert a booking for the same slot. This is especially likely during high-demand periods (e.g., a popular master shares their booking link and 50 people open it simultaneously).

**Consequences:**
- Two clients booked for the same time, one must be turned away
- Loss of trust, negative reviews
- If payment was collected from both, refund headaches and potential legal issues
- Stale cache on the frontend compounds the problem: the mini-app shows "available" slots that were booked seconds ago

**Prevention:**
- Use PostgreSQL `SELECT ... FOR UPDATE` within a transaction when creating a booking. Lock the time slot row before checking availability and inserting.
- Add a UNIQUE constraint on `(master_id, slot_start)` or use exclusion constraints with `tstzrange` for overlapping time ranges: `EXCLUDE USING gist (master_id WITH =, time_range WITH &&)`.
- For the API layer: return 409 Conflict if the slot was taken between showing availability and submitting the booking. The frontend must handle this gracefully ("Sorry, this slot was just taken. Please pick another").
- Never cache slot availability on the client for more than a few seconds. Every booking submission must re-verify against the database.
- Consider advisory locks (`pg_advisory_xact_lock(master_id)`) for the booking transaction to serialize all booking attempts per master.

**Detection:**
- Two bookings with the same `master_id` and overlapping time ranges in the database
- Customer complaints about double-booking
- Missing database constraints on time slot uniqueness

**Phase:** Must be addressed in the very first booking implementation (Phase 1/2). Retrofitting concurrency controls after launch is painful because existing bad data must be cleaned up.

---

### Pitfall 2: Robokassa Callback Mishandling (Lost Payments, Duplicate Processing)

**What goes wrong:** Robokassa sends a POST to your ResultURL after payment. If your server does not respond with `OK{InvId}` quickly and correctly, Robokassa retries delivery. This leads to: (a) payment recorded in Robokassa but not in your system (lost payment), or (b) payment processed multiple times (duplicate receipts, double tax reporting).

**Why it happens:**
- ResultURL handler does heavy processing (sending messages, updating multiple tables) before returning 200
- Server is temporarily down, so callbacks are missed entirely
- Signature validation fails silently (wrong password, wrong hash algorithm, parameter ordering error)
- Test mode uses different passwords than production; switching without updating all endpoints breaks validation
- Robokassa sends to port 80/443 only -- if your FastAPI runs on a non-standard port behind a reverse proxy, the callback never arrives

**Consequences:**
- Client paid but booking not confirmed: worst UX possible
- Duplicate processing means duplicate tax receipts in "Moi Nalog", which triggers FNS scrutiny
- Robokassa password case sensitivity: uppercase letters in Password1/Password2 cause signature mismatch errors that are hard to debug
- Switching from test to production mode without updating passwords breaks all payment flows

**Prevention:**
- Return `OK{InvId}` immediately, then process asynchronously (queue the payment event)
- Implement idempotency: store `InvId` as unique key. If you receive the same `InvId` twice, skip processing and return OK.
- Validate signatures strictly: use the exact hash algorithm configured in Robokassa dashboard (MD5 by default, recommend SHA-256). Password1 for payment initiation, Password2 for ResultURL verification. Never mix them up.
- Store both test and production passwords in environment variables. Use a feature flag to switch, not code changes.
- Keep passwords lowercase (Robokassa has known case-sensitivity issues with signatures).
- Log every callback with full payload for debugging. Alert on signature validation failures.
- Test the full payment flow end-to-end in test mode before going live. Robokassa provides `IsTest=1` parameter.

**Detection:**
- Payments in Robokassa dashboard that are not reflected in your database
- Signature validation errors in logs
- Multiple bookings marked as "paid" for the same InvId
- Client complaints: "I paid but my booking shows unpaid"

**Phase:** Payment integration phase. Build the callback handler with idempotency from day one. Never "add it later."

---

### Pitfall 3: Tax Receipt Cancellation on Refund/No-Show

**What goes wrong:** A receipt is auto-generated in "Moi Nalog" via Robochecks upon payment. When the client cancels, doesn't show up, or requests a refund, the receipt must be cancelled (annulled) in "Moi Nalog" as well. If it is not, the master pays tax on income they didn't actually receive.

**Why it happens:**
- Developers implement the "happy path" (payment -> receipt) but forget the unhappy paths (refund, cancellation, no-show)
- SBP payments are irrevocable at the bank level -- refunds require the master to manually transfer money back, and separately cancel the receipt
- Robokassa supports partial refunds where the sum of refunds must not exceed the original payment amount, but the receipt cancellation logic is separate
- Receipt cancellation in "Moi Nalog" requires specifying a reason: either "return of funds" or "receipt formed in error" -- using the wrong reason can trigger FNS attention
- Tax recalculation for cancelled receipts only happens between the 9th and 12th of the following month

**Consequences:**
- Master pays 4-6% tax on money they refunded (and may not realize until the next month's tax bill)
- Cancelling a receipt without actually returning the money is considered tax evasion
- No automated flow means the master must manually cancel receipts in the "Moi Nalog" app for every refund/cancellation -- defeats the purpose of automation
- FNS penalties for systematic receipt manipulation

**Prevention:**
- Design the refund/cancellation flow as a first-class feature, not an afterthought
- When a booking is cancelled with a refund: (1) initiate Robokassa refund, (2) upon refund confirmation, cancel the corresponding receipt via Robochecks API with reason "return of funds", (3) notify the master
- For no-shows without refund: do NOT auto-cancel the receipt (the service was offered, the master earned the money)
- Track receipt status in your database: `receipt_status` enum (pending, issued, cancelled) linked to each payment
- Build admin tools for the master to manually trigger receipt cancellation with proper reason selection
- Document the monthly tax recalculation lag (9th-12th) so masters understand delayed tax adjustments

**Detection:**
- Refunded payments with receipts still active in "Moi Nalog"
- Master complaints about incorrect tax amounts
- Missing `receipt_status` tracking in the data model

**Phase:** Must be designed alongside the payment phase. Even if refund UI is deferred, the data model and API contracts must account for it from the start.

---

### Pitfall 4: Phone Number Normalization Chaos

**What goes wrong:** The same client books through Telegram as "+79111234567", through VK as "89111234567", and through MAX as "9111234567". The system creates three separate client records. The master sees three "different" clients with different visit histories. Cross-platform client identification -- the core promise of the CRM -- is broken.

**Why it happens:**
- Russia uses country code +7, but domestically people write numbers starting with 8 (trunk prefix). Both +7911... and 8911... are the same number.
- Kazakhstan shares country code +7 but uses different area codes (6xx, 7xx)
- Different messengers provide phone numbers in different formats: MAX provides phone automatically on first interaction, Telegram requires the user to share their contact (and may include country code or not), VK may not provide phone at all without explicit user permission
- Spaces, dashes, parentheses: "+7 (911) 123-45-67" vs "+79111234567"
- Leading zeros, missing country codes, accidental double country code: "+7+79111234567"

**Consequences:**
- Fragmented client base: the same person appears multiple times
- Incorrect visit history: "new client" is actually a returning client
- Notification spam: same person gets reminders on all three messengers for the same booking
- Analytics are wrong: client count inflated, visit frequency understated
- Merging records after the fact is error-prone and may lose data

**Prevention:**
- Normalize ALL phone numbers to E.164 format (+79111234567) at the point of entry, before storing
- Build a normalization function that handles Russian-specific quirks:
  - Strip all non-digit characters
  - If starts with 8 and has 11 digits: replace leading 8 with +7
  - If starts with 7 and has 11 digits: prepend +
  - If has 10 digits (no prefix): prepend +7
  - Reject anything that doesn't result in +7XXXXXXXXXX (11 digits total)
- Use the normalized phone number as the unique client identifier in the database (UNIQUE constraint)
- When a client interacts from a new messenger, look up by normalized phone -> link the messenger account to the existing client record
- Store messenger-specific IDs (tg_user_id, vk_user_id, max_user_id) as separate fields on the client record, not as the primary identifier
- Handle the "no phone yet" case: TG and VK don't give phone numbers automatically. Create a "pending identification" state and prompt for phone number on first booking.

**Detection:**
- Multiple client records with phone numbers that normalize to the same E.164 value
- Client says "I've been here before" but system shows them as new
- master sees duplicate names in client list

**Phase:** Must be in the data model from Phase 1. The phone normalization function and unique constraint are foundational. Adding normalization later means migrating and deduplicating existing data.

---

### Pitfall 5: Mini-App SDK Abstraction That Leaks or Bloats

**What goes wrong:** Building "one React app for three platforms" sounds clean, but the three mini-app SDKs (Telegram @tma.js/sdk, VK vk-bridge, MAX SDK) have fundamentally different APIs for authentication, payments, UI feedback, and data access. Developers either: (a) build a thick abstraction that tries to normalize everything, becoming a maintenance nightmare, or (b) scatter platform-specific `if (platform === 'tg')` checks throughout the codebase.

**Why it happens:**
- Authorization is completely different: TG uses HMAC-SHA256 on initData with bot token, VK uses HMAC-SHA256 on signParams with app secret, MAX has its own mechanism
- Available capabilities differ: TG has haptic feedback, back button control, main button, theme params. VK has its own set of bridge methods. MAX is newest with the most limited SDK.
- Payment flows differ: TG has Telegram Stars (not useful here), VK has VK Pay, none of them support Robokassa natively -- you redirect to an external payment page regardless
- UI components: VK provides VKUI component library, TG has no official React components (community libraries exist), MAX has its own UI kit
- Each platform has different moderation requirements and review processes

**Consequences:**
- Abstraction layer becomes the bottleneck: every new platform feature requires updating the abstraction
- Platform-specific bugs are hard to reproduce and debug
- Performance overhead from unused platform code in the bundle
- Moderation rejection: VK may reject apps that don't use VKUI patterns, MAX requires compliance with Russian law and platform rules

**Prevention:**
- Use a thin adapter pattern, not a thick abstraction. Define a minimal interface:
  ```typescript
  interface PlatformBridge {
    init(): Promise<void>
    getUserData(): Promise<UserData>
    getInitParams(): string  // raw init data for backend validation
    showAlert(msg: string): void
    close(): void
    getPlatform(): 'tg' | 'vk' | 'max'
  }
  ```
- Implement one adapter per platform. Keep adapters under 100 lines each.
- Business logic (booking, payments, calendar) is 100% platform-agnostic and calls the bridge interface
- Authentication: all three platforms send signed init data to your backend. The backend has three validation functions (one per platform). The frontend just passes raw init data.
- Payments: all three platforms redirect to the same Robokassa payment page. No platform-specific payment logic needed.
- Use dynamic imports to load only the relevant platform's adapter based on the entry point URL or environment variable
- Accept that some UI will differ per platform. Don't fight platform conventions.

**Detection:**
- Growing number of `if/else` blocks checking platform type in business logic components
- Abstraction layer file exceeding 500 lines
- Bugs that only reproduce on one platform
- Bundle size including all three SDKs regardless of which platform is running

**Phase:** Architecture decision in Phase 1. The adapter interface must be defined before writing any platform-specific code. Refactoring later means touching every component.

---

### Pitfall 6: Webhook/Callback Security Vulnerabilities

**What goes wrong:** The system has multiple incoming webhook endpoints: Robokassa ResultURL, Telegram bot webhook, VK callback API, MAX bot webhook. Each requires different signature validation. Missing or incorrect validation on any of these allows attackers to: forge payment confirmations, impersonate users, or inject malicious bot commands.

**Why it happens:**
- Each webhook has a different signing mechanism:
  - Robokassa: MD5/SHA256 hash with Password2
  - Telegram: HMAC-SHA256 with bot token
  - VK: confirmation string + secret key verification
  - MAX: its own signature scheme
- Developers validate one correctly but skip or weaken others
- initData from mini-apps is not validated on the backend (trusting the frontend)
- HTTPS not enforced, allowing MITM interception of webhook payloads
- Webhook URLs are discoverable (predictable paths like /api/webhook/telegram)

**Consequences:**
- Forged payment callbacks: attacker sends fake "payment successful" to ResultURL, booking is confirmed without actual payment
- User impersonation: without initData validation, anyone can claim to be any user
- Bot command injection: fake webhook updates can trigger bot actions
- Data exfiltration through manipulated callback URLs

**Prevention:**
- Validate EVERY incoming webhook with its platform-specific signature verification. No exceptions.
- For Robokassa: verify MD5/SHA256 signature using Password2 on every ResultURL callback
- For Telegram initData: use `@tma.js/init-data-node` validate() on the backend for every authenticated request, not just login
- For VK: verify the secret key hash on every callback
- Use HTTPS everywhere (Traefik + Let's Encrypt in Docker)
- Add random tokens to webhook URLs: `/api/webhook/tg/{random_token}` instead of `/api/webhook/telegram`
- Rate-limit webhook endpoints
- Whitelist Robokassa IP addresses if they publish them
- Never trust client-side data without server-side validation. The mini-app sends initData; the server MUST verify it before processing any request.
- Log all webhook validation failures with full payload for security monitoring

**Detection:**
- Bookings marked as paid without corresponding Robokassa transaction
- Webhook endpoints accessible without signature verification in code review
- Missing HMAC validation on mini-app API requests
- Unencrypted HTTP traffic to webhook endpoints

**Phase:** Security must be baked into the first implementation of each integration. Specifically: backend auth middleware in Phase 1, payment signature validation in the payment phase, bot webhook validation when bots are set up.

---

## Moderate Pitfalls

---

### Pitfall 7: Timezone Mishandling Across Russia's 11 Time Zones

**What goes wrong:** A master in Vladivostok (UTC+10) sets working hours 9:00-18:00. A client in Moscow (UTC+3) sees the booking page. If the system stores times in UTC but displays them without converting to the master's timezone, the client sees slots at 2:00 AM - 11:00 AM. Or worse: the reminder "your appointment is in 2 hours" fires at 3 AM Moscow time because the system calculated based on Vladivostok time but sent to a client in Moscow.

**Why it happens:**
- Developers store times as naive timestamps (without timezone) or assume Moscow time for everyone
- Russia has 11 time zones spanning UTC+2 to UTC+12
- Fortunately, Russia does NOT observe DST (abolished in 2014), so offsets are fixed -- but developers coming from other ecosystems may add unnecessary DST logic
- The master's timezone and the client's timezone may differ
- Messenger bots have no built-in timezone detection -- you must ask or infer

**Prevention:**
- Store all times in UTC in the database (use `TIMESTAMPTZ` in PostgreSQL, never `TIMESTAMP`)
- Require the master to set their timezone during onboarding (dropdown of Russian timezone names, not UTC offsets)
- Display times in the MASTER's timezone on the booking page (the appointment is at the master's location)
- For reminders: convert to the CLIENT's timezone if known, otherwise use the master's timezone
- Use `pytz` or `zoneinfo` (Python 3.9+) with IANA timezone names (e.g., `Europe/Moscow`, `Asia/Vladivostok`), never manual UTC offset arithmetic
- Add timezone to the booking confirmation message: "Your appointment: 15:00 (Moscow time)"

**Detection:**
- Booking times that don't match what the client selected
- Reminders arriving at wrong times
- Masters complaining their schedule shows wrong hours
- Missing timezone field on the master profile

**Phase:** Data model (Phase 1) must include timezone on master profile and use TIMESTAMPTZ. Display logic in the mini-app booking phase.

---

### Pitfall 8: Multi-Messenger Bot Instance Conflicts

**What goes wrong:** Running Telegram, MAX, and VK bots on the same FastAPI server with aiogram (for TG) and platform-specific libraries for the others. Common errors: (a) Telegram's `TerminatedByOtherGetUpdates` when two processes poll the same bot token, (b) webhook URLs collide or overwrite each other, (c) one bot's error handler crashes the entire server.

**Why it happens:**
- aiogram polling mode (`start_polling`) blocks the event loop -- can't run two polling bots in the same process
- Deploying multiple server instances (e.g., Docker scaling) without switching to webhooks causes the "terminated by other getUpdates" error
- Each messenger has different webhook setup mechanisms and different retry behaviors
- Error in one bot's handler (e.g., VK rate limit) can raise an unhandled exception that kills the FastAPI process

**Prevention:**
- Use webhooks for ALL three bots, not polling. Webhooks are the only way to reliably run multiple bots on one server.
- Each bot gets its own webhook path: `/webhook/tg`, `/webhook/vk`, `/webhook/max`
- Use separate routers in FastAPI for each bot's webhook handler
- Wrap each bot's message handler in try/except to prevent cross-bot failures
- For aiogram 3.x: use `Dispatcher.feed_webhook_update()` to process webhook updates without polling
- If you must scale to multiple server instances, use a load balancer that routes bot webhooks to a single instance, or use a message queue

**Detection:**
- `TerminatedByOtherGetUpdates` errors in logs
- Bot stops responding after server restart or deployment
- One bot's downtime correlates with another bot's error
- Webhook registration fails silently

**Phase:** Bot setup phase. Decide on webhooks from the start. Do not prototype with polling and "switch to webhooks later" -- the handler architecture is different.

---

### Pitfall 9: SBP Refund Complexity

**What goes wrong:** Client wants a refund. Developer assumes they can "reverse" the SBP payment programmatically. But SBP payments are irrevocable at the banking level. Refunds require the merchant (master) to initiate a separate transfer back, and the sum of refunds cannot exceed the original payment. This is fundamentally different from card payment reversals.

**Why it happens:**
- Developers familiar with Stripe/PayPal expect a simple `refund(payment_id)` API call
- Robokassa supports refunds via API, but the flow is merchant-initiated and asynchronous
- The refund must go through Robokassa (not directly from master's bank account), and Robokassa deducts from the merchant's balance
- Partial refunds are supported but the accounting is complex: original commission is not refunded
- Receipt cancellation (Pitfall 3) must be triggered separately

**Prevention:**
- Design the refund flow as: (1) master approves refund in panel, (2) backend calls Robokassa refund API, (3) on refund confirmation, cancel receipt in "Moi Nalog", (4) update booking status
- Maintain a `payment_events` table tracking: payment, refund_requested, refund_confirmed, receipt_cancelled
- Display clear refund policy to clients at booking time
- Handle the edge case where Robokassa refund fails (insufficient merchant balance): notify master, hold booking in "refund pending" state
- Factor in that Robokassa commission (2.9-3.5%) is not refunded on refund -- the master loses the commission amount. Display this clearly.
- Never let the automated system initiate refunds without master approval

**Detection:**
- Refund requests that sit in "pending" state indefinitely
- Receipts not cancelled after refund completion
- Master's Robokassa balance going negative
- Missing refund event tracking in database

**Phase:** Payment phase (can be a later iteration within the phase, but the data model must support it from the start).

---

### Pitfall 10: VK and MAX Platform Moderation Rejection

**What goes wrong:** The mini-app works perfectly in development, but gets rejected during VK or MAX platform moderation. This can delay launch by weeks.

**Why it happens:**
- VK requires apps to follow specific UI guidelines (VKUI patterns)
- MAX requires compliance with Russian law and platform-specific rules, and every mini-app must pass moderation before going live
- Payment-related apps may face additional scrutiny
- VK may require specific privacy policy disclosures and user consent flows
- MAX is a newer platform with less documented moderation criteria and potentially stricter/more unpredictable review

**Prevention:**
- Read and follow each platform's developer guidelines before building, not after
- For VK: consider using VKUI components or at least matching VK's visual patterns
- For MAX: use the MAX UI component kit where possible
- Include privacy policy, terms of service, and data handling disclosures
- Test on actual devices within the messenger (not just mobile browsers)
- Submit for moderation early with a minimal version to learn the process and requirements
- Keep platform-specific compliance requirements in a checklist
- Budget 2-4 weeks for moderation per platform in the launch timeline

**Detection:**
- Moderation rejection emails with specific violation descriptions
- App published on one platform but blocked on others
- Missing privacy policy or terms pages

**Phase:** Pre-launch checklist, but awareness needed from the design phase. Build privacy/terms pages early.

---

### Pitfall 11: Reminder Delivery Failures Across Messengers

**What goes wrong:** Automated reminders (24h and 2h before appointment) are a core feature. But delivery is not guaranteed across three messenger platforms. A client booked via Telegram but blocked the bot. A VK user has notifications disabled. The reminder for MAX fails because the API token expired.

**Why it happens:**
- Telegram bots can only message users who have interacted with the bot first. If the client booked via mini-app but never messaged the bot, the bot cannot initiate a DM.
- VK has strict anti-spam policies: bots can only send messages to users who have allowed messages from the community
- Each platform has different rate limits for outgoing messages
- Reminder scheduling across timezones (see Pitfall 7) can cause reminders to fire at wrong times
- Cron jobs for reminders can drift, miss executions, or run duplicate on server restart

**Prevention:**
- After booking, explicitly prompt the client to "start" the bot (send /start or equivalent) to enable future messaging
- Track `can_receive_messages` boolean per client per platform
- Implement a reminder queue (Redis + worker, or PostgreSQL-based job queue) with at-least-once delivery and deduplication
- If messenger delivery fails, fall back to... nothing (no SMS in scope), but log the failure and show it in the master's panel
- For scheduling: use a proper job scheduler (APScheduler, Celery beat, or pg_cron) rather than naive `asyncio.sleep()` loops
- Process reminders in batches with rate limiting per platform API limits
- Idempotency: each reminder has a unique ID. If the worker restarts and re-processes, skip already-sent reminders.

**Detection:**
- Clients saying "I didn't get a reminder"
- Reminder delivery logs showing high failure rates on specific platforms
- Duplicate reminders received by clients
- Reminders arriving at wrong times

**Phase:** Notification system phase. But the "can this client receive messages" tracking must be built into client onboarding from Phase 1.

---

### Pitfall 12: Multi-Tenant Data Isolation (Master-to-Master)

**What goes wrong:** Master A can see Master B's clients, bookings, or revenue through an API vulnerability or missing WHERE clause. Even in a shared-database multi-tenant architecture, every query must be scoped to the current master.

**Why it happens:**
- Missing `master_id` filter on database queries (a single missed WHERE clause)
- API endpoints that accept `booking_id` without verifying the booking belongs to the requesting master
- Shared caching (Redis key without master_id prefix) leaking data across tenants
- Admin/debug endpoints accidentally left accessible

**Prevention:**
- Add `master_id` to EVERY table that contains master-specific data
- Create a middleware/dependency in FastAPI that extracts `master_id` from the authenticated session and injects it into all repository queries
- Use PostgreSQL Row-Level Security (RLS) as a defense-in-depth layer: even if application code misses a filter, the database enforces it
- API endpoint pattern: never accept raw `booking_id` in URL -- always verify `SELECT ... WHERE id = $1 AND master_id = $2`
- Write integration tests that create data for Master A and verify Master B cannot access it

**Detection:**
- Any API endpoint that queries by ID without also filtering by master_id
- Missing master_id column on a table that should have it
- Client data visible in another master's panel
- Code review flag: any raw SQL or ORM query without master_id filter

**Phase:** Data model and API middleware from Phase 1. RLS can be added as a hardening step later, but the master_id scoping pattern must be established from the first migration.

---

## Minor Pitfalls

---

### Pitfall 13: Bundle Size Bloat from Three Platform SDKs

**What goes wrong:** The React mini-app includes all three platform SDKs (@tma.js/sdk, vk-bridge, max-sdk) in every build. The bundle grows, loading time increases, and users on slow mobile connections in the messenger WebView experience lag.

**Prevention:**
- Use dynamic imports and code splitting: load only the relevant platform SDK based on the entry point
- Three entry points (tg.html, vk.html, max.html) that each lazy-load only their platform adapter
- Measure bundle size per platform build. Target under 200KB gzipped for the initial load.
- WebView in messengers has limited memory; large bundles can cause crashes on older devices

**Phase:** Build configuration in the frontend setup phase.

---

### Pitfall 14: Robokassa InvId Collision in Multi-Master System

**What goes wrong:** Robokassa uses `InvId` (invoice ID) to identify payments. If two masters generate invoices independently with auto-incrementing IDs, they may collide within the same Robokassa merchant account.

**Prevention:**
- Use a globally unique invoice ID strategy: UUID or `{master_id}_{booking_id}` composite
- Store the mapping between your internal booking ID and the Robokassa InvId
- If using a single Robokassa merchant account for all masters, ensure InvId uniqueness across the entire system
- Consider using Robokassa's `Shp_` (custom) parameters to pass additional metadata (master_id, booking_id) alongside the InvId

**Phase:** Payment integration phase.

---

### Pitfall 15: Master Schedule Edge Cases

**What goes wrong:** The master sets working hours 9:00-18:00 with 1-hour slots. A service takes 90 minutes. The system either: (a) only shows the service in 1-hour slots (client books 60 min, session runs over into next slot), or (b) doesn't account for buffer time between appointments (master has no break).

**Prevention:**
- Slot availability must be calculated based on service duration, not fixed grid intervals
- Add configurable buffer time between appointments (default: 15 min)
- When checking availability, block the entire duration: service_duration + buffer_time
- Handle services that span across a break time (don't allow booking if service would overlap with a break)
- Edge case: last slot of the day must end before closing time, not start before closing time

**Phase:** Booking/calendar implementation phase.

---

### Pitfall 16: Messenger Platform API Rate Limits

**What goes wrong:** A popular master with 500 clients triggers 500 reminder messages at once. The Telegram Bot API rate-limits the bot, messages are delayed or dropped, and some clients don't receive reminders.

**Prevention:**
- Telegram: max 30 messages/second to different chats, 20 messages/minute to the same chat
- VK: check current rate limits in VK API docs (typically 3-5 requests/second)
- MAX: rate limits not well documented yet; start conservatively (10 msg/sec) and adjust
- Implement a message queue with per-platform rate limiting
- Stagger reminder delivery: send 24h reminders gradually over a 1-hour window, not all at once

**Phase:** Notification system implementation.

---

### Pitfall 17: "Мой Налог" Integration Downtime

**What goes wrong:** The "Moi Nalog" / FNS API is occasionally unavailable (maintenance, overload during tax periods). If receipt generation fails, the master's payment flow breaks.

**Prevention:**
- Robochecks handles the FNS integration, so direct API downtime is Robokassa's problem, not yours
- However, receipt generation may be delayed during FNS maintenance
- Design the system so that payment confirmation is not blocked by receipt generation. Payment confirmed -> booking confirmed -> receipt generated asynchronously
- Track receipt status: "pending", "issued", "failed"
- If receipt generation fails after 24 hours, alert the master to manually generate the receipt

**Phase:** Payment integration phase, async receipt tracking.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Data model / DB schema | Phone normalization (4), missing master_id (12), naive timestamps (7) | E.164 normalization function, master_id on all tables, TIMESTAMPTZ everywhere |
| Mini-app frontend | SDK abstraction bloat (5), bundle size (13), platform differences | Thin adapter pattern, dynamic imports, three entry points |
| Booking/calendar | Double booking (1), schedule edge cases (15) | SELECT FOR UPDATE + exclusion constraints, duration-aware slot calculation |
| Payment integration | Robokassa callback (2), InvId collision (14), SBP refunds (9) | Idempotent handler, globally unique InvId, async refund flow |
| Tax receipts | Receipt cancellation on refund (3), FNS downtime (17) | First-class refund flow, async receipt generation with status tracking |
| Bot infrastructure | Instance conflicts (8), rate limits (16) | Webhooks only, per-platform rate-limited message queues |
| Notifications | Reminder failures (11), timezone errors (7) | Delivery tracking, proper job scheduler, timezone-aware scheduling |
| Security | Webhook vulnerabilities (6) | Platform-specific signature validation on every endpoint, HTTPS, random webhook paths |
| Platform launch | Moderation rejection (10) | Early submission, platform-specific compliance checklists |

---

## Sources

- [PostgreSQL Explicit Locking (FOR UPDATE, Advisory Locks)](https://www.postgresql.org/docs/current/explicit-locking.html) -- HIGH confidence
- [Robokassa API Integration Guide](https://robokassa.com/blog/articles/podklyuchenie-robokassa-k-vashey-platforme/) -- HIGH confidence
- [Robokassa Robochecks for Self-Employed](https://robokassa.com/online-check/robocheck-smz/) -- HIGH confidence
- [Telegram Mini Apps Official Docs](https://core.telegram.org/bots/webapps) -- HIGH confidence
- [Migrating Mini Apps from VK to Telegram (SDK comparison)](https://docs.telegram-mini-apps.com/platform/migrating-from-vk) -- HIGH confidence
- [Telegram Bot Webhook Guide](https://core.telegram.org/bots/webhooks) -- HIGH confidence
- [Telegram initData Validation](https://docs.telegram-mini-apps.com/platform/init-data) -- HIGH confidence
- [VK Bridge GitHub Repository](https://github.com/VKCOM/vk-bridge) -- HIGH confidence
- [MAX Messenger GitHub Organization](https://github.com/max-messenger) -- MEDIUM confidence (young ecosystem, docs evolving)
- [Russia Telephone Number Formats (Wikipedia)](https://en.wikipedia.org/wiki/Telephone_numbers_in_Russia) -- HIGH confidence
- [Time in Russia (Wikipedia)](https://en.wikipedia.org/wiki/Time_in_Russia) -- HIGH confidence
- [SBP Faster Payment System (Bank of Russia)](https://www.cbr.ru/eng/psystem/sfp/) -- HIGH confidence
- [aiogram Multiple Bots Discussion](https://github.com/aiogram/aiogram/discussions/578) -- MEDIUM confidence
- [Robokassa Node.js Integration (password pitfalls)](https://github.com/betsol/node-robokassa) -- MEDIUM confidence
- [Receipt Cancellation Rules for Self-Employed (qugo.ru)](https://qugo.ru/blog/kak-annulirovat-chek-samozanyatomu-v-prilozhenii-moj-nalog) -- MEDIUM confidence
- [Multi-Channel Conversation Framework Pattern](https://dev.to/quintana/i-built-a-multi-channel-conversation-framework-in-python-heres-why-5fi9) -- LOW confidence (single source pattern)
- [CRM Deduplication Guide 2025](https://www.rtdynamic.com/blog/crm-deduplication-guide-2025/) -- MEDIUM confidence
- [MAX Messenger Overview (umnico.com)](https://umnico.com/blog/max-messenger/) -- MEDIUM confidence
