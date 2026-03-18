---
phase: 05-multi-messenger-expansion
verified: 2026-03-18T13:30:00Z
status: passed
score: 18/18 must-haves verified
re_verification: false
---

# Phase 5: Multi-Messenger Expansion Verification Report

**Phase Goal:** The same booking, payment, and notification experience works in MAX and VK messengers; clients from different messengers are recognized as the same person by phone number
**Verified:** 2026-03-18T13:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                       | Status     | Evidence                                                                                                                         |
|----|---------------------------------------------------------------------------------------------|------------|----------------------------------------------------------------------------------------------------------------------------------|
| 1  | Config accepts MAX_BOT_TOKEN, MAX_WEBHOOK_SECRET, VK_GROUP_TOKEN, VK_APP_ID, VK_APP_SECRET, VK_CONFIRMATION_TOKEN, VK_SECRET_KEY | VERIFIED | All 8 fields present in `config.py` lines 41-50 with empty string defaults |
| 2  | validate_max_init_data reuses TG validation algorithm (HMAC-SHA256 with WebAppData key)    | VERIFIED   | `security.py` line 114-118: `validate_max_init_data` delegates directly to `validate_tg_init_data`, zero duplication            |
| 3  | validate_vk_launch_params uses HMAC-SHA256 on sorted vk_* params with URL-safe base64      | VERIFIED   | `security.py` lines 121-178: OrderedDict sort, hmac.new SHA256, base64+rstrip+replace, hmac.compare_digest timing-safe          |
| 4  | POST /api/v1/auth/max exchanges valid MAX initData for JWT                                 | VERIFIED   | `auth.py` lines 95-134: validates via validate_max_init_data, looks up Master.max_user_id, returns TokenResponse                |
| 5  | POST /api/v1/auth/vk exchanges valid VK launch params for JWT                              | VERIFIED   | `auth.py` lines 137-178: validates via validate_vk_launch_params, extracts vk_user_id, looks up Master.vk_user_id, returns JWT  |
| 6  | Masters table has max_user_id and vk_user_id columns                                       | VERIFIED   | `master.py` lines 37-42: both columns nullable String(100) unique+indexed; migration 006 adds them with ix_masters_*_user_id    |
| 7  | MAX bot receives webhook updates and processes them                                         | VERIFIED   | `main.py` lines 182-207: POST /webhook/max validates X-Max-Bot-Api-Secret, calls process_max_update with DB session             |
| 8  | MaxAdapter sends all 6 notification types to MAX users                                     | VERIFIED   | `adapter.py`: all 6 methods implemented (send_booking_notification, send_message, send_payment_link, send_payment_requisites, send_reminder, send_booking_confirmation) via httpx |
| 9  | Master can register via MAX bot /start command and get linked max_user_id                  | VERIFIED   | `handlers/start.py` lines 100-130: creates Master(max_user_id=max_user_id) on new user, db.flush()                             |
| 10 | VK webhook handles confirmation handshake (returns plain text token on type=confirmation)  | VERIFIED   | `main.py` lines 216-217: if body.get("type") == "confirmation": return PlainTextResponse(settings.vk_confirmation_token)       |
| 11 | VkAdapter sends all 6 notification types to VK users                                       | VERIFIED   | `adapter.py`: all 6 methods implemented via httpx POST to messages.send with VK JSON keyboard format                           |
| 12 | Master can register via VK bot /start and get linked vk_user_id                           | VERIFIED   | `handlers/start.py` lines 69-93: creates Master(vk_user_id=from_id), fetches name via users.get, db.flush()                   |
| 13 | Frontend detects MAX platform                                                               | VERIFIED   | `detect.ts` lines 17-21: checks window.WebApp?.initData !== undefined after Telegram check                                      |
| 14 | Frontend detects VK platform via URL params                                                 | VERIFIED   | `detect.ts` lines 24-30: checks params.has("vk_user_id") && params.has("sign")                                                 |
| 15 | MAX mini-app initData is passed to backend for auth (createMaxBridge)                      | VERIFIED   | `adapters/max.ts`: createMaxBridge() returns platform="max", getInitDataRaw()=webApp?.initData, getUserId()=user.id             |
| 16 | VK mini-app launch params are passed to backend for auth (createVkBridge)                 | VERIFIED   | `adapters/vk.ts`: createVkBridge() returns platform="vk", getInitDataRaw()=window.location.search, getUserId()=vk_user_id      |
| 17 | Client booking via any platform creates ClientPlatform entry (CLNT-04)                    | VERIFIED   | `BookingForm.tsx` line 129-130: source_platform=platform.platform, platform_user_id=getUserId(); `client_service.py` lines 42-59: find_or_create_client upserts ClientPlatform |
| 18 | Clients from different messengers recognized as same person by phone                       | VERIFIED   | `client_service.py` lines 26-34: find_or_create_client looks up by normalized phone first (E.164 via normalize_phone), then links platform if provided |

**Score:** 18/18 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/core/config.py` | MAX and VK settings fields | VERIFIED | 8 new fields present lines 41-50 |
| `backend/app/core/security.py` | validate_max_init_data, validate_vk_launch_params | VERIFIED | Both functions present, HMAC correctly implemented |
| `backend/app/models/master.py` | max_user_id, vk_user_id columns | VERIFIED | Lines 37-42, nullable unique indexed String(100) |
| `backend/app/schemas/auth.py` | MaxAuthRequest, VkAuthRequest schemas | VERIFIED | Both present with correct fields |
| `backend/app/api/v1/auth.py` | /auth/max and /auth/vk endpoints | VERIFIED | Both endpoints fully implemented, 401/404 guards present |
| `backend/alembic/versions/006_add_max_vk_master_columns.py` | Migration adding both columns | VERIFIED | Adds max_user_id, vk_user_id with unique indexes; down_revision chains to 005 |
| `backend/app/bots/max/adapter.py` | MaxAdapter (all 6 methods, min_lines:100) | VERIFIED | 280 lines, all 6 abstract methods implemented |
| `backend/app/bots/max/bot.py` | Adapter registration with NotificationService | VERIFIED | register_adapter("max", MaxAdapter(bot_token)) guarded by token presence |
| `backend/app/bots/max/handlers/start.py` | bot_started + deep link handling (min_lines:40) | VERIFIED | 254 lines; handles bot_started, /start with deep link, master creation |
| `backend/app/main.py` | /webhook/max and /webhook/vk endpoints | VERIFIED | Both endpoints present (lines 182-238), correct secret validation, DB session with commit/rollback |
| `frontend/src/platform/adapters/max.ts` | createMaxBridge() implementing PlatformBridge | VERIFIED | All 9 interface methods implemented; expand() is no-op as required |
| `frontend/src/platform/detect.ts` | MAX and VK platform detection | VERIFIED | MAX: window.WebApp.initData check; VK: vk_user_id+sign URL params |
| `frontend/src/platform/context.tsx` | MAX and VK cases in PlatformProvider switch | VERIFIED | case "max": createMaxBridge(); case "vk": createVkBridge() |
| `backend/app/schemas/booking.py` | platform_user_id field (not tg_user_id) | VERIFIED | Line 14: platform_user_id: str | None = None |
| `frontend/src/api/bookings.ts` | platform_user_id in BookingCreate | VERIFIED | Line 12: platform_user_id?: string |
| `backend/app/bots/vk/adapter.py` | VkAdapter (all 6 methods, min_lines:100) | VERIFIED | 280 lines, all 6 abstract methods, plain text messages, VK keyboard format |
| `backend/app/bots/vk/bot.py` | VK adapter registration | VERIFIED | register_adapter("vk", VkAdapter(vk_token)) guarded by token |
| `frontend/src/platform/adapters/vk.ts` | createVkBridge() with @vkontakte/vk-bridge | VERIFIED | VKWebAppInit called, all 9 interface methods, getUserId() returns vk_user_id |
| `frontend/index.html` | max-web-app.js CDN script in head | VERIFIED | Line 10: `<script src="https://st.max.ru/js/max-web-app.js"></script>` |
| `frontend/package.json` | @vkontakte/vk-bridge installed | VERIFIED | "@vkontakte/vk-bridge": "^2.15.11" |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/api/v1/auth.py` | `backend/app/core/security.py` | validate_max_init_data, validate_vk_launch_params imports | WIRED | Lines 11-13: explicit imports of both functions |
| `backend/app/api/v1/auth.py` | `backend/app/core/config.py` | settings.max_bot_token, settings.vk_app_secret | WIRED | Lines 106, 149: both settings fields read |
| `backend/app/bots/max/bot.py` | `backend/app/bots/common/notification.py` | register_adapter("max", MaxAdapter(...)) | WIRED | Lines 24-27: conditional import + registration |
| `backend/app/main.py` | `backend/app/bots/max/bot.py` | import bot_token and process_max_update | WIRED | Line 11: import bot_token; line 197: import process_max_update |
| `frontend/src/platform/context.tsx` | `frontend/src/platform/adapters/max.ts` | import createMaxBridge | WIRED | Line 5: import createMaxBridge; line 22: case "max" usage |
| `frontend/src/platform/adapters/max.ts` | booking via platform_user_id | getUserId() value passed as platform_user_id | WIRED | `BookingForm.tsx` line 119: const userId = platform.getUserId(); line 130: platform_user_id: userId |
| `frontend/src/pages/client/BookingForm.tsx` | `backend/app/services/booking_service.py` | source_platform + platform_user_id -> ClientPlatform upsert | WIRED | BookingForm sends platform.platform + getUserId(); service calls find_or_create_client(platform=source_platform, platform_user_id=platform_user_id) |
| `backend/app/bots/vk/bot.py` | `backend/app/bots/common/notification.py` | register_adapter("vk", VkAdapter(...)) | WIRED | Lines 22-25: conditional import + registration |
| `backend/app/main.py` | `backend/app/bots/vk/bot.py` | import vk_token and process_vk_event | WIRED | Line 13: import vk_token; line 227: import process_vk_event |
| `frontend/src/platform/context.tsx` | `frontend/src/platform/adapters/vk.ts` | import createVkBridge | WIRED | Line 6: import createVkBridge; line 24: case "vk" usage |
| Multi-platform master notification fan-out | booking_service._notify_master | collects tg/max/vk platform IDs, sends to all | WIRED | Lines 49-54: iterates master.tg_user_id, max_user_id, vk_user_id and appends to platform_ids list |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MSG-03 | 05-01, 05-02 | MAX Bot -- webhook processing, notifications | SATISFIED | /webhook/max endpoint + MaxAdapter 6 notification methods verified in codebase |
| MSG-04 | 05-01, 05-02 | MAX Mini App -- same functionality as TG Mini App | SATISFIED | createMaxBridge() wraps window.WebApp; MAX detection in detectPlatform(); max-web-app.js in index.html; auth via /auth/max |
| MSG-05 | 05-01, 05-03 | VK Bot -- webhook processing, notifications | SATISFIED | /webhook/vk endpoint with confirmation handshake + VkAdapter 6 notification methods verified |
| MSG-06 | 05-01, 05-03 | VK Mini App -- same functionality as TG Mini App | SATISFIED | createVkBridge() with @vkontakte/vk-bridge; VK detection in detectPlatform(); auth via /auth/vk |
| CLNT-04 | 05-02, 05-03 | Client from different messengers recognized as one person by phone | SATISFIED | find_or_create_client() looks up by normalized phone first; ClientPlatform row links platform identity to unified Client; BookingForm sends platform.platform + getUserId() generically |

No orphaned requirements found. All 5 Phase 5 requirements are accounted for.

---

### Anti-Patterns Found

No blockers or warnings found.

- No TODO/FIXME/PLACEHOLDER comments in any of the phase 5 files.
- No empty implementations (all 6 adapter methods are substantive in both MaxAdapter and VkAdapter).
- No return null/return {}/return [] stubs.
- All handler functions contain real logic (DB queries, API calls, master creation).
- No console.log-only implementations.

---

### Human Verification Required

The following behaviors cannot be verified programmatically and require live environment testing:

#### 1. MAX Webhook Registration on Startup

**Test:** Start the backend with MAX_BOT_TOKEN and BASE_WEBHOOK_URL configured. Check server logs.
**Expected:** Log line "MAX webhook registered: {url}" and MAX platform-api.max.ru returns 200/201.
**Why human:** Requires real MAX partner credentials and live MAX platform API; cannot verify network call without running the app.

#### 2. VK Confirmation Handshake Round-Trip

**Test:** Configure VK community Callback API URL to point at /webhook/vk. Click "Confirm" in VK settings.
**Expected:** VK sends {"type": "confirmation"} and receives the raw confirmation token as plain text; VK marks webhook as active.
**Why human:** Requires live VK community account and dashboard access; cannot simulate VK's confirmation request.

#### 3. MAX Mini-App initData Authentication

**Test:** Open the mini-app from within the MAX client. Attempt to access a protected endpoint (e.g., /api/v1/auth/max).
**Expected:** Request returns JWT; subsequent API calls with that JWT succeed.
**Why human:** Requires MAX client app + registered MAX Mini App; window.WebApp is only injected inside real MAX WebView.

#### 4. VK Mini-App Launch Params Authentication

**Test:** Open the mini-app from a VK Mini App context. URL should contain vk_user_id, sign, and other vk_* params.
**Expected:** detectPlatform() returns "vk"; getInitDataRaw() returns the query string; /auth/vk validates and returns JWT.
**Why human:** Requires registered VK Mini App and VK client to inject launch params into URL.

#### 5. Cross-Messenger Client Unification

**Test:** Book as a client via Telegram with phone +79001234567. Then book via MAX with the same phone number.
**Expected:** Both bookings link to the same Client record in the database; master sees single client in client history.
**Why human:** Requires live environment with both TG and MAX bots configured and a real booking flow end-to-end.

---

### Gaps Summary

No gaps found. All automated checks pass.

**Plan 01 (shared infrastructure):** All 6 artifacts verified. Config has all 8 MAX/VK fields. validate_max_init_data delegates correctly (zero duplication). validate_vk_launch_params implements the full VK algorithm with URL-safe base64 and timing-safe comparison. Master model has both new columns. Migration 006 chains correctly from 005 and adds both columns with unique indexes. Auth endpoints for /auth/max and /auth/vk are fully implemented with 401/404 guards.

**Plan 02 (MAX integration):** All MAX bot module files exist and are substantive. MaxAdapter implements all 6 MessengerAdapter abstract methods (over 280 lines). /webhook/max validates the secret header and uses a DB session with commit/rollback. MAX webhook subscription registered in lifespan. Frontend MAX bridge wraps window.WebApp correctly with expand() as a no-op. MAX platform detection is correctly ordered after Telegram. Booking flow correctly generalized: tg_user_id renamed to platform_user_id across all 5 layers (schema, service, API, frontend interface, BookingForm). Multi-platform master notification fan-out is implemented in _notify_master.

**Plan 03 (VK integration):** All VK bot module files exist and are substantive. VkAdapter implements all 6 methods with plain text messages (correct for VK) and VK JSON keyboard format. /webhook/vk correctly handles the confirmation handshake before any secret check (order matters). VK webhook returns PlainTextResponse("ok") as required. @vkontakte/vk-bridge 2.15.11 installed. Frontend VkBridge calls VKWebAppInit on creation.

**Cross-phase goal (client unification):** find_or_create_client() in client_service.py correctly identifies clients by normalized phone number first, then links platform identity via ClientPlatform. This means a client who books via Telegram, MAX, and VK using the same phone number will always map to the same Client row with multiple ClientPlatform entries.

---

_Verified: 2026-03-18T13:30:00Z_
_Verifier: Claude (gsd-verifier)_
