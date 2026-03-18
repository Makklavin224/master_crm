# Phase 5: Multi-Messenger Expansion (MAX + VK) - Research

**Researched:** 2026-03-18
**Domain:** MAX Bot API, MAX Mini App Bridge, VK Bot API, VK Mini App Bridge, cross-messenger identity
**Confidence:** MEDIUM (MAX ecosystem is young with sparse docs; VK ecosystem is mature and well-documented)

## Summary

Phase 5 adds MAX and VK messenger support to the existing Telegram-only CRM. The project already has well-defined adapter patterns on both backend (MessengerAdapter ABC with 6 abstract methods) and frontend (PlatformBridge interface with 11 methods). The task is to implement concrete adapters for each new platform following the established TelegramAdapter and createTelegramBridge() patterns.

MAX (formerly TamTam, VK-owned) has a Bot API at `platform-api.max.ru` with inline keyboards, webhooks, and a WebView Bridge API (`window.WebApp`) that closely mirrors Telegram's interface. The mini-app validation uses identical HMAC-SHA256 with "WebAppData" + bot token -- the same algorithm as Telegram. However, MAX has significant differences: no `expand()` method, no MainButton, and publication requires a verified Russian legal entity. The maxapi Python library (0.9.16) provides Bot + Dispatcher with aiogram-like patterns.

VK has a mature Callback API for bots, the vkbottle framework (4.6.2) for async bot development, and @vkontakte/vk-bridge (2.15.11) for mini-apps. VK's launch parameter validation uses HMAC-SHA256 with the app secret on sorted `vk_*` parameters, encoded as URL-safe base64. VK bots operate through community pages and use a confirmation-token handshake for webhooks. VK inline keyboards support callback buttons with payload but the interaction model differs from TG/MAX.

**Primary recommendation:** Implement both platforms in parallel by following existing adapter patterns exactly. MAX adapter is higher risk due to sparse docs and legal entity requirement. VK adapter is lower risk due to mature ecosystem. Use maxapi for MAX bot (aiogram-like API), raw VK API calls through vkbottle for VK bot. Frontend adapters are thin wrappers: MAX Bridge mirrors TG WebApp closely; VK Bridge uses `@vkontakte/vk-bridge` send() pattern.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- MAX and VK implemented simultaneously (parallel plans), not sequentially
- Adapter pattern from Phase 2 makes this feasible -- both follow the same interface
- Same functions as TG bot but adapted to each platform's API capabilities
- If a platform doesn't support inline buttons, use text-based alternatives
- Core functions: registration, today's bookings, booking link sharing, settings, notifications
- Phone number (E.164) is the universal identifier for cross-messenger identity
- client_platforms table already exists (Phase 1) -- stores platform + platform_user_id per client
- PlatformBridge interface + StubAdapter already exist (Phase 2)
- MessengerAdapter ABC already has 6 abstract methods
- NotificationService already supports multiple registered adapters
- Each platform's adapter handles its own message formatting

### Claude's Discretion
- MAX Bot API integration details (maxapi library or raw HTTP)
- VK Bot API integration (vkbottle or raw HTTP)
- MAX WebView bridge specifics (research needed -- docs sparse)
- VK Bridge integration (@vkontakte/vk-bridge)
- Webhook security per platform
- Message formatting differences
- Deep linking patterns per platform

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MSG-03 | MAX Bot -- webhook processing, notifications | MAX Bot API at platform-api.max.ru; maxapi 0.9.16 for bot framework; webhook subscription via POST /subscriptions with secret header; update types: message_created, message_callback, bot_started |
| MSG-04 | MAX Mini App -- same functionality as TG Mini App | MAX Bridge (max-web-app.js) provides window.WebApp with initData, BackButton, HapticFeedback; validation identical to TG (HMAC-SHA256); deep link format: max.ru/<botName>?startapp=<payload>; requestContact() for phone |
| MSG-05 | VK Bot -- webhook processing, notifications | VK Callback API with confirmation token handshake; vkbottle 4.6.2 for bot framework; process_event() for webhook integration with FastAPI; message_new and message_event event types |
| MSG-06 | VK Mini App -- same functionality as TG Mini App | @vkontakte/vk-bridge 2.15.11 for bridge; VKWebAppGetUserInfo for user data; launch parameters with vk_user_id; sign validation via HMAC-SHA256 on sorted vk_* params |
| CLNT-04 | Client from different messengers recognized as one person by phone | E.164 normalization already implemented (Phase 1); client_platforms table ready; MAX provides phone via requestContact(); VK provides phone via VKWebAppGetPhoneNumber; lookup by normalized phone -> link platform entry |
</phase_requirements>

## Standard Stack

### Core (Backend -- New Adapters)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| maxapi | 0.9.16 | MAX Bot API framework | Official-community Python library for MAX bots. Supports polling + webhook modes. Dispatcher pattern mirrors aiogram. Published Mar 2026, actively maintained. |
| vkbottle | 4.6.2 | VK Bot API framework | Standard async VK API framework. Router-based, middleware, labeler pattern. Mature ecosystem, well-documented. |

### Core (Frontend -- New Adapters)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| max-web-app.js | (CDN script) | MAX Mini App Bridge | Official MAX Bridge library. Provides window.WebApp object. Loaded via `<script src="https://st.max.ru/js/max-web-app.js">`. Not an npm package -- included via script tag. |
| @vkontakte/vk-bridge | 2.15.11 | VK Mini App Bridge | Official VK bridge package. Provides send()-based API for all VK Mini App features. 4.5k dependents, actively maintained. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @maxhub/max-ui | 0.1.13 | MAX UI React components | Optional. Use if MAX moderation requires MAX-styled UI. Project uses Tailwind so likely not needed for MVP. |
| @vkontakte/vk-mini-apps-api | latest | VK Mini Apps higher-level API | Optional wrapper over vk-bridge. Provides getUserInfo(), getPhoneNumber() as methods. Can use raw vk-bridge send() instead. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| maxapi | Raw HTTP to platform-api.max.ru | Raw HTTP is simpler (no framework dependency) but loses Dispatcher, keyboard builders, type safety. maxapi's aiogram-like patterns match existing TG code style. |
| vkbottle | vk_api (sync) | vk_api is sync-only, incompatible with async FastAPI. vkbottle is async-native. |
| max-web-app.js (CDN) | npm package (none exists) | No npm package available for MAX Bridge. CDN script is the only option. Can create a thin TypeScript wrapper. |

**Installation:**

```bash
# Backend
uv add maxapi vkbottle

# Frontend (VK bridge only -- MAX bridge is a CDN script)
pnpm add @vkontakte/vk-bridge
```

**Version verification:**
- maxapi 0.9.16: verified via PyPI (published 2026-03-06)
- vkbottle 4.6.2: verified via `pip install vkbottle==999` (latest in version list)
- @vkontakte/vk-bridge 2.15.11: verified via `npm view` (latest tag)
- @maxhub/max-ui 0.1.13: verified via `npm view`

## Architecture Patterns

### Recommended Project Structure (New Files)

```
backend/
  app/
    bots/
      max/
        __init__.py
        bot.py              # MAX Bot + event routing (like telegram/bot.py)
        adapter.py           # MaxAdapter(MessengerAdapter) -- 6 methods
        handlers/
          __init__.py
          start.py           # bot_started event handler
          today.py           # /today command
          link.py            # /link command
          settings.py        # /settings command
          callbacks.py       # message_callback handler
      vk/
        __init__.py
        bot.py              # VK Bot + process_event setup (like telegram/bot.py)
        adapter.py           # VkAdapter(MessengerAdapter) -- 6 methods
        handlers/
          __init__.py
          start.py           # /start command handler
          today.py           # /today command
          link.py            # /link command
          settings.py        # /settings command
          callbacks.py       # message_event (callback button) handler
    core/
      security.py           # Add validate_max_init_data(), validate_vk_launch_params()
      config.py             # Add max_bot_token, vk_group_token, vk_app_secret, etc.
    api/v1/
      auth.py               # Add /auth/max and /auth/vk endpoints

frontend/
  src/
    platform/
      detect.ts             # Add MAX and VK detection
      context.tsx            # Add MAX and VK bridge creation
      adapters/
        max.ts              # createMaxBridge(): PlatformBridge
        vk.ts               # createVkBridge(): PlatformBridge
  index.html               # Add MAX Bridge script tag (conditional)
```

### Pattern 1: MAX Bot Adapter (mirrors TelegramAdapter exactly)

**What:** MaxAdapter implements all 6 MessengerAdapter abstract methods using maxapi Bot or raw HTTP to platform-api.max.ru.
**When to use:** All MAX bot messaging.

```python
# backend/app/bots/max/adapter.py
import logging
import httpx
from app.bots.common.adapter import BookingNotification, MessengerAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)

class MaxAdapter(MessengerAdapter):
    """Sends notifications via MAX Bot API."""

    def __init__(self, token: str) -> None:
        self._token = token
        self._base_url = "https://platform-api.max.ru"
        self._headers = {"Authorization": token}

    async def send_message(
        self, platform_user_id: str, text: str
    ) -> bool:
        """Send a plain text message via MAX Bot API."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._base_url}/messages",
                    headers=self._headers,
                    params={"chat_id": platform_user_id},
                    json={
                        "text": text,
                        "format": "html",
                    },
                )
                return resp.status_code == 200
        except Exception:
            logger.exception("Failed to send MAX message to %s", platform_user_id)
            return False

    async def send_booking_notification(self, notif: BookingNotification) -> bool:
        # Format text + build inline keyboard with callback buttons
        # Use InlineKeyboardAttachment format:
        # {"type": "inline_keyboard", "payload": {"buttons": [[...]]}}
        ...

    # ... other 4 methods follow same pattern
```

**Confidence:** HIGH for the pattern, MEDIUM for exact MAX API request format (verified from official docs at dev.max.ru/docs-api).

### Pattern 2: VK Bot Adapter (uses vkbottle API object)

**What:** VkAdapter implements all 6 MessengerAdapter methods using VK API messages.send with keyboard parameter.
**When to use:** All VK bot messaging.

```python
# backend/app/bots/vk/adapter.py
import logging
from vkbottle import Keyboard, Callback, Text
from app.bots.common.adapter import BookingNotification, MessengerAdapter

logger = logging.getLogger(__name__)

class VkAdapter(MessengerAdapter):
    """Sends notifications via VK Bot API."""

    def __init__(self, api) -> None:
        self._api = api  # vkbottle API instance

    async def send_message(
        self, platform_user_id: str, text: str
    ) -> bool:
        try:
            await self._api.messages.send(
                user_id=int(platform_user_id),
                message=text,
                random_id=0,
            )
            return True
        except Exception:
            logger.exception("Failed to send VK message to %s", platform_user_id)
            return False

    async def send_booking_notification(self, notif: BookingNotification) -> bool:
        # Build keyboard with Keyboard(inline=True) + Callback buttons
        keyboard = (
            Keyboard(inline=True)
            .add(Callback("Details", payload={"cmd": f"booking:{notif.booking_id}"}))
            .add(Callback("Schedule", payload={"cmd": "today"}))
        ).get_json()
        text = self._format_notification(notif)
        # messages.send with keyboard param
        ...
```

**Confidence:** HIGH -- vkbottle API pattern is well-established.

### Pattern 3: MAX initData Validation (identical to Telegram)

**What:** Validate MAX Mini App initData using HMAC-SHA256 with bot token.
**When to use:** /auth/max endpoint.

```python
# backend/app/core/security.py -- add alongside validate_tg_init_data

def validate_max_init_data(
    init_data_raw: str,
    bot_token: str,
    max_age_seconds: int = 86400,
) -> dict | None:
    """
    Validate MAX Mini App initData.
    Algorithm is IDENTICAL to Telegram:
    1. Parse URL-encoded params
    2. Extract and remove 'hash'
    3. Sort remaining params alphabetically
    4. Build data_check_string: "key=value\n" joined
    5. secret_key = HMAC-SHA256("WebAppData", bot_token)
    6. computed_hash = HMAC-SHA256(secret_key, data_check_string)
    7. Compare computed_hash with received hash
    """
    # Implementation is the same as validate_tg_init_data()
    # Can extract shared logic or just duplicate with different function name
    return validate_tg_init_data(init_data_raw, bot_token, max_age_seconds)
```

**Confidence:** HIGH -- verified from official MAX docs at dev.max.ru/docs/webapps/validation. The algorithm is explicitly documented as using "WebAppData" key + bot token, sorted params, HMAC-SHA256.

### Pattern 4: VK Launch Params Validation

**What:** Validate VK Mini App sign parameter using HMAC-SHA256 on sorted vk_* params.
**When to use:** /auth/vk endpoint.

```python
# backend/app/core/security.py

import base64
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlencode, parse_qs

def validate_vk_launch_params(
    query_string: str,
    app_secret: str,
) -> dict | None:
    """
    Validate VK Mini App launch parameters.
    Algorithm (from official VK example):
    1. Parse all query params
    2. Extract 'sign' param
    3. Filter params starting with 'vk_'
    4. Sort alphabetically by key
    5. URL-encode sorted params
    6. HMAC-SHA256(app_secret, encoded_string)
    7. base64-encode, remove trailing '=', replace +/- with -/_
    8. Compare with received sign
    """
    parsed = parse_qs(query_string, keep_blank_values=True)
    # Flatten to single values
    flat = {k: v[0] for k, v in parsed.items()}

    received_sign = flat.get("sign")
    if not received_sign:
        return None

    # Filter and sort vk_* params
    vk_params = sorted(
        ((k, v) for k, v in flat.items() if k.startswith("vk_")),
        key=lambda x: x[0],
    )

    if not vk_params:
        return None

    # URL-encode
    encoded = urlencode(OrderedDict(vk_params), doseq=True)

    # HMAC-SHA256
    computed = HMAC(
        app_secret.encode(), encoded.encode(), sha256
    ).digest()

    # Base64 URL-safe encoding
    b64 = base64.b64encode(computed).decode("utf-8")
    b64 = b64.rstrip("=").replace("+", "-").replace("/", "_")

    if b64 != received_sign:
        return None

    return flat  # Contains vk_user_id, vk_app_id, etc.
```

**Confidence:** HIGH -- verified from official VK GitHub example (VKCOM/vk-apps-launch-params/examples/python3.py).

### Pattern 5: MAX Frontend Bridge Adapter

**What:** Thin wrapper around window.WebApp (MAX Bridge).
**When to use:** MAX mini-app context.

```typescript
// frontend/src/platform/adapters/max.ts
import type { PlatformBridge } from "../types.ts";

export function createMaxBridge(): PlatformBridge {
  const webApp = (window as any).WebApp;

  return {
    platform: "max",

    getInitDataRaw(): string | null {
      return webApp?.initData ?? null;
    },

    getUserId(): string | null {
      return webApp?.initDataUnsafe?.user?.id?.toString() ?? null;
    },

    hapticFeedback(type: "light" | "medium" | "heavy"): void {
      try { webApp?.HapticFeedback?.impactOccurred(type); } catch {}
    },

    showBackButton(): void {
      try { webApp?.BackButton?.show(); } catch {}
    },

    hideBackButton(): void {
      try { webApp?.BackButton?.hide(); } catch {}
    },

    onBackButtonClick(cb: () => void): () => void {
      try {
        webApp?.BackButton?.onClick(cb);
        return () => { try { webApp?.BackButton?.offClick(cb); } catch {} };
      } catch { return () => {}; }
    },

    ready(): void {
      try { webApp?.ready(); } catch {}
    },

    expand(): void {
      // MAX Bridge has NO expand() method -- no-op
    },

    close(): void {
      try { webApp?.close(); } catch {}
    },
  };
}
```

**Confidence:** HIGH -- verified from dev.max.ru/docs/webapps/bridge. MAX WebApp mirrors TG WebApp closely but lacks expand(), MainButton, showAlert(), showConfirm().

### Pattern 6: VK Frontend Bridge Adapter

**What:** Wrapper around @vkontakte/vk-bridge send() API.
**When to use:** VK mini-app context.

```typescript
// frontend/src/platform/adapters/vk.ts
import bridge from "@vkontakte/vk-bridge";
import type { PlatformBridge } from "../types.ts";

export function createVkBridge(): PlatformBridge {
  // Initialize VK Bridge
  bridge.send("VKWebAppInit");

  // Cache launch params from URL
  const urlParams = new URLSearchParams(window.location.search);
  const vkUserId = urlParams.get("vk_user_id");

  return {
    platform: "vk",

    getInitDataRaw(): string | null {
      // VK uses URL query string as launch params (not body like TG)
      return window.location.search.slice(1) || null;
    },

    getUserId(): string | null {
      return vkUserId;
    },

    hapticFeedback(type: "light" | "medium" | "heavy"): void {
      try {
        bridge.send("VKWebAppTapticImpactOccurred", {
          style: type,
        });
      } catch {}
    },

    showBackButton(): void {
      // VK has no native back button API -- handled by browser/app
    },

    hideBackButton(): void {
      // No-op for VK
    },

    onBackButtonClick(): () => void {
      // VK does not expose back button events
      return () => {};
    },

    ready(): void {
      // VKWebAppInit already called
    },

    expand(): void {
      // VK Mini Apps auto-expand; no separate call needed
    },

    close(): void {
      try { bridge.send("VKWebAppClose", { status: "success" }); } catch {}
    },
  };
}
```

**Confidence:** MEDIUM -- VK Bridge methods verified from official docs, but some method names (VKWebAppTapticImpactOccurred) need validation against current API.

### Pattern 7: Platform Detection Update

**What:** Update detect.ts to recognize MAX and VK WebView environments.

```typescript
// frontend/src/platform/detect.ts
export function detectPlatform(): Platform {
  if (typeof window === "undefined") return "web";

  // Check Telegram first (existing)
  if (window.Telegram?.WebApp) return "telegram";

  // Check MAX -- WebApp object injected by max-web-app.js
  if ((window as any).WebApp?.initData !== undefined) return "max";

  // Check VK -- launch params in URL
  const params = new URLSearchParams(window.location.search);
  if (params.has("vk_user_id") && params.has("sign")) return "vk";

  return "web";
}
```

**Confidence:** MEDIUM -- MAX detection needs testing. VK detection via URL params is reliable.

### Pattern 8: Webhook Routes in main.py

**What:** Add MAX and VK webhook endpoints alongside existing TG webhook.

```python
# MAX webhook
@application.post("/webhook/max")
async def max_webhook(
    request: Request,
    x_max_bot_api_secret: str | None = Header(None),
):
    if x_max_bot_api_secret != settings.max_webhook_secret:
        raise HTTPException(status_code=403)
    body = await request.json()
    # Process via MaxBot handlers
    await max_bot.process_update(body)
    return {"ok": True}

# VK webhook
@application.post("/webhook/vk")
async def vk_webhook(request: Request):
    body = await request.json()
    # VK confirmation handshake
    if body.get("type") == "confirmation":
        return PlainTextResponse(settings.vk_confirmation_token)
    # Verify secret
    if body.get("secret") != settings.vk_secret_key:
        raise HTTPException(status_code=403)
    # Process in background to avoid timeout
    await vk_bot.process_event(body)
    return PlainTextResponse("ok")
```

**Confidence:** HIGH -- both patterns verified from official docs.

### Anti-Patterns to Avoid

- **Platform checks in business logic:** Never `if platform == "max"` in BookingService. All platform logic stays in adapters.
- **Coupling to maxapi Dispatcher in FastAPI:** maxapi's `dp.handle_webhook()` starts its own server. Instead, feed raw updates into handlers manually within FastAPI routes.
- **Using vkbottle's run_forever() in FastAPI:** This starts a separate event loop. Use `bot.process_event(data)` pattern for webhook integration.
- **Loading all 3 Bridge SDKs in frontend:** Use dynamic imports / conditional script loading. Only load the relevant platform's bridge.
- **Trusting client-side platform detection for auth:** Always validate initData/sign on the backend. Platform detection is for UX only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MAX Bot messaging | Raw HTTP to platform-api.max.ru | maxapi Bot class for message sending, InlineKeyboardBuilder for keyboards | Handles auth headers, response parsing, keyboard serialization, error handling |
| VK Bot messaging | Raw VK API HTTP calls | vkbottle API.messages.send() | Handles token management, rate limiting, serialization |
| VK launch param validation | Custom HMAC implementation | Adapt official VK Python example verbatim | Edge cases in base64 URL-safe encoding, parameter ordering |
| MAX initData validation | New implementation | Reuse validate_tg_init_data() -- algorithm is identical | Verified from official MAX docs -- same HMAC-SHA256 with "WebAppData" |
| VK keyboard construction | Raw JSON keyboard objects | vkbottle Keyboard class with Callback/Text actions | Handles color, payload serialization, row management |
| MAX keyboard construction | Raw JSON attachments | maxapi InlineKeyboardBuilder | Handles button types, row limits, serialization to attachment format |

**Key insight:** MAX's validation mechanism being identical to Telegram's means the existing `validate_tg_init_data()` function can be reused directly. This is the single most important finding -- it halves the auth implementation work.

## Common Pitfalls

### Pitfall 1: MAX Requires Legal Entity for Bot Publication
**What goes wrong:** You build the MAX bot and mini-app, but cannot publish because MAX requires a verified Russian legal entity (OOO, IP) as of August 2025.
**Why it happens:** MAX changed their rules to require organizational accounts. Individual developers, self-employed, and non-residents cannot publish.
**How to avoid:** Verify legal entity registration on MAX Partners platform before development. If no entity exists, this blocks the entire MAX deployment.
**Warning signs:** Cannot access MAX Partners platform -> Organization Profile -> Chatbots.

### Pitfall 2: maxapi Dispatcher Conflict with FastAPI
**What goes wrong:** Using `dp.handle_webhook()` from maxapi starts uvicorn on a separate port, conflicting with the existing FastAPI application.
**Why it happens:** maxapi's webhook mode is designed for standalone bot servers, not integration with existing web frameworks.
**How to avoid:** Do NOT use `dp.handle_webhook()`. Instead, use maxapi Bot directly for sending messages, and handle incoming webhooks through FastAPI route -> manual event parsing. Use maxapi's SubscribeWebhook to register webhook URL, then process raw JSON in FastAPI endpoint.
**Warning signs:** Port conflicts, two uvicorn processes, events not reaching handlers.

### Pitfall 3: VK Confirmation Handshake
**What goes wrong:** VK sends a `{"type": "confirmation"}` event as the first request to your webhook URL. If you don't respond with the exact confirmation token string (not JSON, not with headers -- just the raw string), VK never activates the webhook.
**Why it happens:** VK's Callback API has a unique handshake that differs from TG and MAX. The response must be a plain text response containing only the confirmation code.
**How to avoid:** Handle the confirmation type first in the VK webhook handler. Return `PlainTextResponse(confirmation_token)`. All subsequent events must return `"ok"` as plain text.
**Warning signs:** VK community settings show webhook as "not confirmed", no events received.

### Pitfall 4: VK Bot Requires Community (Group), Not Personal Account
**What goes wrong:** Developer tries to create a VK bot with a personal token. VK bots operate through community pages, requiring a group access token.
**Why it happens:** VK's bot architecture is fundamentally different from TG/MAX. Bots are not standalone entities -- they are features of community pages.
**How to avoid:** Create a VK community -> Settings -> Messages (enable) -> Callback API -> Get group access token with required permissions (messages, manage).
**Warning signs:** API returns "Permission denied" or "Invalid token type".

### Pitfall 5: MAX Bridge Script Loading Order
**What goes wrong:** Frontend code tries to access `window.WebApp` before the MAX Bridge script has loaded. Results in undefined errors.
**Why it happens:** MAX Bridge is loaded via CDN script tag, not npm package. If the script tag is placed after your app bundle or loads slowly, the bridge isn't ready.
**How to avoid:** Place the MAX Bridge script tag in `<head>` before the app bundle. The bridge should be available synchronously by the time React mounts. Alternatively, use a polling wait: check for `window.WebApp` existence with a short timeout.
**Warning signs:** `window.WebApp is undefined` errors only in MAX WebView.

### Pitfall 6: VK Phone Number Requires Explicit User Permission
**What goes wrong:** Calling VKWebAppGetPhoneNumber prompts the user with a permission dialog. If denied, you have no phone number for cross-messenger identity matching.
**Why it happens:** VK respects user privacy. Unlike MAX (which provides phone automatically via requestContact flow), VK requires explicit opt-in.
**How to avoid:** Design the booking flow so phone number is collected during the booking form (text input fallback). Use VKWebAppGetPhoneNumber as a convenience pre-fill, not a hard requirement. The backend already handles "no phone yet" cases via the existing booking flow.
**Warning signs:** CLNT-04 cross-messenger matching fails for VK clients who denied phone permission.

### Pitfall 7: MAX Has No expand() Method
**What goes wrong:** The existing TelegramAdapter calls `expandViewport()` on ready. If the MaxAdapter does the same, it throws an error because MAX Bridge has no expand() method.
**Why it happens:** MAX Bridge API is a subset of Telegram's. It lacks: expand(), MainButton, SecondaryButton, SettingsButton, showPopup(), showAlert(), showConfirm(), CloudStorage.
**How to avoid:** The MaxAdapter.expand() should be a no-op. Review all PlatformBridge methods for MAX compatibility.
**Warning signs:** Runtime errors in MAX WebView for methods that exist in TG but not MAX.

### Pitfall 8: VK message_event vs message_new
**What goes wrong:** Inline keyboard callback clicks in VK trigger `message_event`, not `message_new`. If you only listen for `message_new`, button clicks are silently ignored.
**Why it happens:** VK separates text messages (message_new) from button callbacks (message_event). This is different from TG (callback_query) and MAX (message_callback).
**How to avoid:** Enable `message_event` in VK community Callback API settings. Handle it separately in the VK bot handler. Respond with `messages.sendMessageEventAnswer` to acknowledge the callback.
**Warning signs:** Bot receives text messages but inline button clicks do nothing.

## Code Examples

### MAX Bot Module Setup (bot.py pattern)

```python
# backend/app/bots/max/bot.py
import logging
from maxapi import Bot
from app.core.config import settings
from app.bots.common.notification import notification_service
from app.bots.max.adapter import MaxAdapter

logger = logging.getLogger(__name__)

bot: Bot | None = None

if settings.max_bot_token:
    bot = Bot(token=settings.max_bot_token)

    # Register MaxAdapter with NotificationService
    notification_service.register_adapter("max", MaxAdapter(settings.max_bot_token))
    logger.info("MAX bot configured and adapter registered")
else:
    logger.warning("MAX_BOT_TOKEN not set -- MAX bot is disabled")
```

### VK Bot Module Setup with Callback API

```python
# backend/app/bots/vk/bot.py
import logging
from vkbottle import Bot, API
from vkbottle.callback import BotCallback
from app.core.config import settings
from app.bots.common.notification import notification_service
from app.bots.vk.adapter import VkAdapter

logger = logging.getLogger(__name__)

bot: Bot | None = None
api: API | None = None

if settings.vk_group_token:
    api = API(token=settings.vk_group_token)
    # Setup callback handler for webhook integration
    callback = BotCallback(
        url=f"{settings.base_webhook_url}/webhook/vk",
        title="master-crm",
    )
    bot = Bot(token=settings.vk_group_token, callback=callback)

    # Register VkAdapter with NotificationService
    notification_service.register_adapter("vk", VkAdapter(api))
    logger.info("VK bot configured and adapter registered")
else:
    logger.warning("VK_GROUP_TOKEN not set -- VK bot is disabled")
```

### Config Settings Extensions

```python
# backend/app/core/config.py -- new settings to add
class Settings(BaseSettings):
    # ... existing settings ...

    # MAX
    max_bot_token: str = ""
    max_webhook_secret: str = ""  # X-Max-Bot-Api-Secret header value

    # VK
    vk_group_token: str = ""       # Community bot access token
    vk_app_id: str = ""            # VK Mini App application ID
    vk_app_secret: str = ""        # VK Mini App secret key (for sign validation)
    vk_confirmation_token: str = "" # VK Callback API confirmation string
    vk_secret_key: str = ""        # VK Callback API secret key
```

### Auth Endpoints for MAX and VK

```python
# backend/app/api/v1/auth.py -- new endpoints

@router.post("/max", response_model=TokenResponse)
async def max_auth(
    data: MaxAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Exchange valid MAX initData for a JWT."""
    # Reuse TG validation -- algorithm is identical
    user_data = validate_tg_init_data(data.init_data, settings.max_bot_token)
    if user_data is None:
        raise HTTPException(status_code=401, detail="Invalid MAX auth data")

    max_user_id = str(user_data.get("id", ""))
    # Lookup master by platform-specific ID
    # Similar to TG auth but uses a different platform column
    ...

@router.post("/vk", response_model=TokenResponse)
async def vk_auth(
    data: VkAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Exchange valid VK launch params for a JWT."""
    params = validate_vk_launch_params(data.launch_params, settings.vk_app_secret)
    if params is None:
        raise HTTPException(status_code=401, detail="Invalid VK auth data")

    vk_user_id = params.get("vk_user_id", "")
    # Lookup master by platform-specific ID
    ...
```

### MAX Inline Keyboard with open_app Button

```python
# MAX: send booking mini-app button (equivalent of TG WebAppInfo)
async def send_mini_app_button(self, chat_id: str, master_id: str):
    """Send inline keyboard with open_app button to open mini-app."""
    mini_app_url = f"{settings.mini_app_url}?master={master_id}"
    payload = {
        "text": "Open mini-app for booking:",
        "format": "html",
        "attachments": [{
            "type": "inline_keyboard",
            "payload": {
                "buttons": [[{
                    "type": "open_app",
                    "text": "Book appointment",
                    "url": mini_app_url,
                }]]
            }
        }],
    }
    # POST to /messages with chat_id
```

### VK Inline Keyboard with Callback

```python
# VK: send keyboard with callback buttons
async def send_booking_notification(self, notif: BookingNotification) -> bool:
    keyboard = (
        Keyboard(inline=True)
        .add(Callback("Details", payload={"cmd": f"booking:{notif.booking_id}"}))
        .add(Callback("Schedule", payload={"cmd": "today"}))
    ).get_json()

    text = self._format_notification(notif)
    await self._api.messages.send(
        user_id=int(notif.master_platform_id),
        message=text,
        keyboard=keyboard,
        random_id=0,
    )
```

### Deep Link Formats

```python
# Telegram: t.me/botusername?start=MASTER_UUID
tg_deep_link = f"https://t.me/{settings.tg_bot_username}?start={master_id}"

# MAX: max.ru/botusername?startapp=MASTER_UUID
max_deep_link = f"https://max.ru/{settings.max_bot_username}?startapp={master_id}"

# VK: vk.com/app{APP_ID}#master={MASTER_UUID} (via community)
# Or mini-app URL with query params
vk_deep_link = f"https://vk.com/app{settings.vk_app_id}#master={master_id}"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| MAX API at botapi.max.ru | platform-api.max.ru | Aug 2025 | Old base URL deprecated. New URL requires Authorization header (not query param). |
| MAX bots by individual developers | Verified legal entity required | Aug 2025 | Individual developers cannot publish MAX bots. Must have OOO/IP. |
| vkbottle 4.7.0 (per STACK.md) | vkbottle 4.6.2 (actual latest) | Current | STACK.md had incorrect version. Latest PyPI release is 4.6.2. |
| VK Mini Apps separate auth | Launch params with sign verification | Current | HMAC-SHA256 on vk_* params with URL-safe base64 encoding. |

**Deprecated/outdated:**
- `botapi.max.ru` -- old MAX API base URL, replaced by `platform-api.max.ru`
- Token via query parameter in MAX API -- now requires `Authorization` header
- vkbottle 4.7.0 -- does not exist; latest is 4.6.2

## Open Questions

1. **MAX Bot Handler Integration with FastAPI**
   - What we know: maxapi has a Dispatcher with decorators. It also has a `handle_webhook()` that starts its own server.
   - What's unclear: How to feed raw webhook JSON into maxapi's dispatcher without using handle_webhook(). The library may support `dp.process_update()` or similar.
   - Recommendation: If maxapi does not expose a process_update method, bypass the dispatcher entirely and use the Bot class directly for sending. Handle incoming events with raw JSON parsing in the FastAPI route. The TG bot handlers are simple enough (5 commands + callbacks) that reimplementing them without a dispatcher is trivial.

2. **VK Mini App Registration Process**
   - What we know: VK Mini Apps are registered through VK developer portal. Need a VK community.
   - What's unclear: Exact moderation timeline and requirements for a booking/CRM mini-app.
   - Recommendation: Submit VK Mini App for moderation early with minimal functionality. VK moderation is typically faster than MAX (1-3 business days vs 2 business days for MAX).

3. **MAX requestContact() User Experience**
   - What we know: MAX Bridge provides `requestContact()` which shows a native dialog for phone sharing.
   - What's unclear: Whether the phone is returned immediately or via an event callback. Whether the user can decline.
   - Recommendation: Handle both cases (phone provided and phone declined). Fall back to manual phone entry in the booking form, matching the existing VK fallback pattern.

4. **VK message_event Callback Answer**
   - What we know: VK callback button clicks trigger `message_event`. The bot should respond with `messages.sendMessageEventAnswer`.
   - What's unclear: Whether vkbottle handles this automatically or requires manual implementation.
   - Recommendation: Check vkbottle raw_event handler for message_event type. If not auto-handled, add manual handler using `api.messages.send_message_event_answer()`.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (backend), vitest (frontend) |
| Config file | None -- Wave 0 setup needed |
| Quick run command | `cd backend && python -m pytest tests/ -x --timeout=10` |
| Full suite command | `cd backend && python -m pytest tests/ -v && cd ../frontend && pnpm test` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MSG-03 | MAX Bot webhook receives and processes updates | integration | `pytest tests/test_max_webhook.py -x` | Wave 0 |
| MSG-03 | MaxAdapter sends notifications via MAX API | unit | `pytest tests/test_max_adapter.py -x` | Wave 0 |
| MSG-04 | MAX initData validation (HMAC-SHA256) | unit | `pytest tests/test_max_auth.py -x` | Wave 0 |
| MSG-04 | MaxBridge adapter returns correct initData | unit | `vitest run src/platform/adapters/max.test.ts` | Wave 0 |
| MSG-05 | VK webhook handles confirmation + events | integration | `pytest tests/test_vk_webhook.py -x` | Wave 0 |
| MSG-05 | VkAdapter sends messages with keyboards | unit | `pytest tests/test_vk_adapter.py -x` | Wave 0 |
| MSG-06 | VK launch params sign validation | unit | `pytest tests/test_vk_auth.py -x` | Wave 0 |
| MSG-06 | VkBridge adapter returns correct launch params | unit | `vitest run src/platform/adapters/vk.test.ts` | Wave 0 |
| CLNT-04 | Phone-based identity linking across platforms | integration | `pytest tests/test_cross_platform_identity.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x --timeout=10`
- **Per wave merge:** Full backend + frontend suite
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/conftest.py` -- shared fixtures (async DB session, mock adapters)
- [ ] `backend/tests/test_max_webhook.py` -- MAX webhook integration
- [ ] `backend/tests/test_max_adapter.py` -- MaxAdapter unit tests
- [ ] `backend/tests/test_max_auth.py` -- MAX initData validation
- [ ] `backend/tests/test_vk_webhook.py` -- VK webhook with confirmation
- [ ] `backend/tests/test_vk_adapter.py` -- VkAdapter unit tests
- [ ] `backend/tests/test_vk_auth.py` -- VK sign validation
- [ ] `backend/tests/test_cross_platform_identity.py` -- phone-based identity
- [ ] `frontend/src/platform/adapters/max.test.ts` -- MAX bridge adapter
- [ ] `frontend/src/platform/adapters/vk.test.ts` -- VK bridge adapter
- [ ] Framework install: `uv add --dev pytest pytest-asyncio` (backend), `pnpm add -D vitest` (frontend)

## Sources

### Primary (HIGH confidence)
- [MAX Bridge API docs](https://dev.max.ru/docs/webapps/bridge) -- WebApp object, BackButton, HapticFeedback, all methods/properties
- [MAX initData validation](https://dev.max.ru/docs/webapps/validation) -- HMAC-SHA256 algorithm, identical to Telegram
- [MAX Bot API](https://dev.max.ru/docs-api) -- Base URL, auth header, inline keyboard JSON, message format, rate limits (30 req/s)
- [MAX Mini App introduction](https://dev.max.ru/docs/webapps/introduction) -- Deep linking (startapp), publication requirements, URL format
- [VK vk-apps-launch-params](https://github.com/VKCOM/vk-apps-launch-params) -- Sign validation algorithm (HMAC-SHA256 + base64 URL-safe)
- [VK vk-bridge core](https://github.com/VKCOM/vk-bridge) -- Bridge send() API, initialization, environment detection
- [vkbottle GitHub](https://github.com/vkbottle/vkbottle) -- Bot framework, handlers, keyboard builder, Callback API integration
- [vkbottle Callback API example](https://github.com/vkbottle/vkbottle/blob/master/examples/high-level/callback_api/app.py) -- FastAPI integration pattern

### Secondary (MEDIUM confidence)
- [maxapi PyPI](https://pypi.org/project/maxapi/) -- Version 0.9.16, Python >=3.10, webhook extras
- [maxapi GitHub](https://github.com/love-apples/maxapi) -- Bot + Dispatcher pattern, handler decorators, polling/webhook modes
- [maxapi docs](https://love-apples.github.io/maxapi/) -- SubscribeWebhook class, InlineKeyboardBuilder, button types
- [VK keyboard docs](https://vkbottle.readthedocs.io/ru/latest/tools/keyboard/) -- Keyboard class, Callback/Text actions, inline mode
- [MAX publication rules change (Habr)](https://habr.com/ru/articles/951326/) -- Legal entity requirement, API migration, bot card requirements
- [VK Mini Apps API](https://github.com/VKCOM/vk-mini-apps-api) -- getUserInfo(), getPhoneNumber() with sign verification

### Tertiary (LOW confidence)
- [@maxhub/max-ui npm](https://www.npmjs.com/package/@maxhub/max-ui) -- MAX UI React components v0.1.13, limited docs
- VK message_event handling pattern -- inferred from VK API docs, not directly tested with vkbottle

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All packages verified on PyPI/npm with current versions
- Architecture (backend adapters): HIGH -- Follows established MessengerAdapter ABC pattern identically
- Architecture (frontend adapters): HIGH for VK (mature SDK), MEDIUM for MAX (CDN script, no npm package)
- MAX Bot API specifics: MEDIUM -- Official docs verified but ecosystem is young
- VK Bot API specifics: HIGH -- Mature ecosystem with extensive documentation
- MAX publication requirements: HIGH -- Verified from Habr article and official docs
- Cross-messenger identity: HIGH -- Existing client_platforms table + phone normalization already implemented
- Validation algorithms: HIGH -- Both verified from official sources with code examples
- Pitfalls: HIGH -- Based on verified API limitations and official docs

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (30 days -- MAX ecosystem evolving rapidly, recheck before implementation if delayed)
