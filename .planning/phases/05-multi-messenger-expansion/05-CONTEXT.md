# Phase 5: Multi-Messenger Expansion - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Add MAX and VK messenger support — both bot adapters (backend) and platform bridge adapters (frontend). Implement cross-messenger client identity (same phone = same client across TG/MAX/VK). Both platforms implemented simultaneously, following the existing TG adapter patterns.

</domain>

<decisions>
## Implementation Decisions

### Execution Order
- MAX and VK implemented simultaneously (parallel plans), not sequentially
- Adapter pattern from Phase 2 makes this feasible — both follow the same interface

### Bot Commands
- Same functions as TG bot but adapted to each platform's API capabilities
- Claude will research MAX Bot API and VK Bot API to determine exact capabilities (inline buttons, deep linking, webhooks)
- If a platform doesn't support inline buttons → use text-based alternatives
- Core functions: registration, today's bookings, booking link sharing, settings, notifications

### Cross-Messenger Identity
- Phone number (E.164) is the universal identifier
- Client who books via TG and later opens VK should see their existing history
- client_platforms table already exists (Phase 1) — stores platform + platform_user_id per client
- MAX provides phone number automatically — easiest platform for identity

### Frontend Platform Adapters
- PlatformBridge interface + StubAdapter already exist (Phase 2)
- Add MaxAdapter and VkAdapter implementing the same interface
- Platform detection: check `window.Telegram`, MAX WebView indicators, VK Bridge
- Same React mini-app, same booking flow, same master panel — just different bridge

### Backend Messenger Adapters
- MessengerAdapter ABC already has send_booking_notification, send_reminder, send_booking_confirmation, send_payment_link, send_payment_requisites
- Add MaxAdapter and VkAdapter implementing all abstract methods
- NotificationService already supports multiple registered adapters
- Each platform's adapter handles its own message formatting (HTML for TG, platform-specific for MAX/VK)

### Claude's Discretion
- MAX Bot API integration details (maxapi library or raw HTTP)
- VK Bot API integration (vkbottle or raw HTTP)
- MAX WebView bridge specifics (research needed — docs sparse)
- VK Bridge integration (@vkontakte/vk-bridge)
- Webhook security per platform
- Message formatting differences
- Deep linking patterns per platform

</decisions>

<canonical_refs>
## Canonical References

### Project Specs
- `.planning/REQUIREMENTS.md` — MSG-03, MSG-04, MSG-05, MSG-06, CLNT-04

### Research (project-level)
- `.planning/research/STACK.md` — maxapi 0.9.16, vkbottle 4.7.0, @vkontakte/vk-bridge
- `.planning/research/ARCHITECTURE.md` — Messenger Adapter pattern, platform detection shell
- `.planning/research/PITFALLS.md` — MAX bridge API sparse docs, VK payment redirect policies

### Existing Code (to extend)
- `backend/app/bots/common/adapter.py` — MessengerAdapter ABC (6 abstract methods)
- `backend/app/bots/common/notification.py` — NotificationService (register_adapter, route to all)
- `backend/app/bots/telegram/` — Reference implementation (adapter, bot, handlers)
- `frontend/src/platform/` — PlatformBridge interface, TelegramAdapter, StubAdapter
- `frontend/src/api/client.ts` — X-Init-Data header auth pattern
- `backend/app/models/client.py` — ClientPlatform model (platform + platform_user_id)
- `backend/app/core/security.py` — validate_tg_init_data (pattern for MAX/VK validation)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MessengerAdapter` ABC — 6 methods to implement per platform
- `NotificationService` — register new adapters alongside TG
- TG handlers pattern — /start, /today, /link, /settings, callbacks
- PlatformBridge interface — 4 methods to implement per platform
- client_platforms table — ready for MAX/VK entries
- validate_tg_init_data — pattern for platform-specific auth validation

### Established Patterns
- Backend: adapter ABC → platform-specific implementation → registered with NotificationService
- Frontend: PlatformBridge interface → platform-specific adapter → detected at app root
- Webhook: platform-specific route in main.py → feed to platform's update handler
- Auth: platform initData → validate → find/create master → issue JWT

### Integration Points
- Register MaxAdapter + VkAdapter with NotificationService in main.py lifespan
- Add MAX/VK webhook routes in main.py
- Add MAX/VK platform detection in frontend PlatformProvider
- Add auth/max and auth/vk endpoints alongside auth/tg
- Add MAX/VK bot tokens to .env and config

</code_context>

<specifics>
## Specific Ideas

- MAX is the strategic priority (100M users, first mover window) but both ship together
- MAX WebView bridge docs are sparse — research phase should investigate thoroughly
- VK has mature SDK (@vkontakte/vk-bridge, VKUI) — more straightforward

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-multi-messenger-expansion*
*Context gathered: 2026-03-18*
