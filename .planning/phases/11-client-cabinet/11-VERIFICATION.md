---
phase: 11-client-cabinet
verified: 2026-03-21T06:00:00Z
status: gaps_found
score: 3/4 success criteria verified
re_verification: false
gaps:
  - truth: "Client enters phone at /my and receives a 6-digit OTP via messenger bot; web-booked clients without a bot connection receive OTP via SMS fallback"
    status: partial
    reason: "OTP delivery via messenger is fully implemented (telegram > max > vk priority). However, the SMS fallback for web-booked clients without a messenger platform is explicitly not implemented — the endpoint returns a message stating 'SMS-отправка пока не подключена. Код не доставлен.' with success=True, effectively silently failing delivery for this client cohort. CCAB-02 requires SMS fallback."
    artifacts:
      - path: "backend/app/api/v1/client_auth.py"
        issue: "Lines 136-146: when no platform found (or all delivery attempts fail), returns OTPResponse with success=True but message='SMS-отправка пока не подключена. Код не доставлен.' No SMS is actually sent."
    missing:
      - "SMS delivery integration (~2 rub/SMS as noted in ROADMAP) or at minimum a clear 503/501 error response instead of a success=True with silent failure"
human_verification:
  - test: "Visit /my in a browser, enter a valid client phone number, confirm OTP form transitions to 6-digit input with 60-second countdown, enter the received code, and verify redirect to /my/bookings"
    expected: "Two-phase login flow works end-to-end; OTP arrives via Telegram/MAX/VK; bookings list renders for the authenticated client"
    why_human: "Requires a live bot connection, a seeded client with a messenger platform, and actual OTP delivery — cannot verify programmatically"
  - test: "On /my/bookings, click 'Записаться снова' on a past completed booking and verify navigation to /m/{username}/book?service={service_id} with the correct service pre-selected"
    expected: "Service step shows the correct service pre-selected from the query param"
    why_human: "Requires a live bookings dataset and cross-page navigation flow verification"
  - test: "Click 'Оставить отзыв' on a completed past booking, select a star rating, add text, submit, and verify the review is submitted and the form shows success feedback"
    expected: "Review form submits to backend, shows 'Спасибо за отзыв!', form closes, bookings query invalidates"
    why_human: "Requires live authenticated session and a completed booking in the database"
---

# Phase 11: Client Cabinet Verification Report

**Phase Goal:** Clients can log in to a personal cabinet at /my, see all their bookings across masters, rebook past services, and leave reviews after completed visits
**Verified:** 2026-03-21T06:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Client enters phone at /my, receives 6-digit OTP via messenger bot; web-booked clients without bot connection receive OTP via SMS fallback | PARTIAL | Messenger delivery (TG/MAX/VK) is fully implemented. SMS fallback is not — returns success=True with a "not connected" message, silently failing delivery for web-booked clients without a messenger platform |
| 2 | OTP expires after 5 min, max 3 attempts, 60-sec cooldown; session persists 7 days via cookie | VERIFIED | `OTP_EXPIRY_MINUTES=5`, `MAX_OTP_ATTEMPTS=3`, `COOLDOWN_SECONDS=60`, `SESSION_EXPIRY_DAYS=7` all defined and enforced; SHA256 hashing; httpOnly cookie set on verify |
| 3 | Client sees upcoming bookings with cancel/reschedule, past visits with "Zapisatsya snova" and "Ostavit otzyv" | VERIFIED | BookingsPage splits into upcoming/past sections; BookingCard renders cancel+reschedule for upcoming confirmed, rebook+review for past completed; reschedule is an MVP placeholder (alert) which aligns with plan intent |
| 4 | Client who visits multiple masters sees all bookings in one list; clicking master name navigates to their public page | VERIFIED | GET /client/bookings queries by client.id without master_id filter — cross-master by design; BookingCard.handleMasterClick() navigates to `/m/${booking.master_username}` |

**Score:** 3/4 success criteria verified (1 partial due to CCAB-02 SMS fallback)

### Required Artifacts

#### Plan 11-01 Artifacts (Backend API)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/api/v1/client_auth.py` | OTP request/verify endpoints | VERIFIED | 218 lines; both endpoints fully implemented with SHA256 hashing, cooldown, attempt tracking, messenger delivery, httpOnly cookie |
| `backend/app/api/v1/client_cabinet.py` | Bookings and reviews endpoints | VERIFIED | 148 lines; GET /bookings with cross-master query, POST /reviews with full validation chain |
| `backend/app/core/dependencies.py` | get_current_client dependency | VERIFIED | Lines 135-164: reads client_session cookie, validates is_verified=True and expiry against DB, returns Client via selectinload |
| `backend/app/schemas/client.py` | Pydantic schemas for OTP, bookings, reviews | VERIFIED | OTPRequest, OTPVerify, OTPResponse, SessionResponse, ClientBookingRead, ClientBookingsResponse, ReviewCreate, ReviewCreateResponse all present |
| `backend/alembic/versions/014_add_otp_columns_to_client_sessions.py` | Migration for otp_hash, otp_attempts, is_verified | VERIFIED | Adds 3 columns to client_sessions; revises 013_add_payment_fns_receipt |
| `backend/app/models/client_session.py` | Updated model with 3 new columns | VERIFIED | otp_hash (String(64) nullable), otp_attempts (Integer, server_default=0), is_verified (Boolean, server_default=false) |

#### Plan 11-02 Artifacts (Routing)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `Caddyfile` | Dual-path routing /m/* and /my/* to public:3002 | VERIFIED | Both handle /m/* and handle /my/* blocks present, no strip_prefix, both point to public:3002; /assets/* handler also present |
| `public/vite.config.ts` | base: "/" | VERIFIED | `base: "/"` confirmed on line 7 |
| `public/src/App.tsx` | basename="/" with /m/:username and /my routes | VERIFIED | BrowserRouter basename="/", routes for /m/:username, /m/:username/book/*, /my, /my/bookings all present |
| `public/Dockerfile` | Nginx with /m/, /my/, /assets/ SPA fallback | VERIFIED | All three location blocks with try_files fallback to /index.html |

#### Plan 11-03 Artifacts (Frontend UI)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `public/src/stores/auth.ts` | Zustand auth store with useAuth | VERIFIED | 37 lines; isAuthenticated, isLoading, phone, setPhone, setAuthenticated, checkSession (calls GET /client/bookings), logout |
| `public/src/api/client-cabinet.ts` | API functions: requestOTP, verifyOTP, getClientBookings, createReview | VERIFIED | All 6 functions present (requestOTP, verifyOTP, getClientBookings, createReview, cancelBooking, rescheduleBooking); all include credentials:"include" |
| `public/src/pages/cabinet/LoginPage.tsx` | Login page wrapper with auth redirect | VERIFIED | 41 lines; checkSession on mount, redirects to /my/bookings if authenticated, renders LoginForm |
| `public/src/pages/cabinet/BookingsPage.tsx` | Bookings list with upcoming/past sections | VERIFIED | 220 lines; useQuery for bookings, cancel handler, review toggle, skeleton loading, error with retry, two sections |
| `public/src/components/LoginForm.tsx` | Phone input + OTP verification form | VERIFIED | 308 lines; two-phase flow, Russian phone formatting, 6 separate OTP inputs, auto-focus chain, paste support, auto-submit, 60s countdown, resend |
| `public/src/components/BookingCard.tsx` | Booking card with action buttons | VERIFIED | 154 lines; master initials avatar, clickable master name to /m/{username}, Russian date/time via dayjs, status badges, cancel/reschedule for upcoming, rebook/review for past completed |
| `public/src/components/ReviewForm.tsx` | Star rating + text review form | VERIFIED | 133 lines; 5 interactive stars, textarea with 500-char limit and counter, submit/error/success states, calls createReview |

### Key Link Verification

#### Plan 11-01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `client_auth.py` | `client_session.py` | ClientSession model for token storage | VERIFIED | `from app.models.client_session import ClientSession` imported; ClientSession rows created and queried |
| `client_auth.py` | `notification.py` | notification_service.send_message for OTP delivery | VERIFIED | `from app.bots.common.notification import notification_service` imported; `notification_service.send_message(platform, platform_user_id, ...)` called in OTP delivery loop |
| `client_cabinet.py` | `dependencies.py` | Depends(get_current_client) | VERIFIED | `from app.core.dependencies import get_current_client, get_db` imported; both endpoints use `Annotated[Client, Depends(get_current_client)]` |
| `router.py` | `client_auth.py` | router include at /client/auth | VERIFIED | `from app.api.v1.client_auth import router as client_auth_router` and `api_v1_router.include_router(client_auth_router, prefix="/client/auth", tags=["client-auth"])` |
| `router.py` | `client_cabinet.py` | router include at /client | VERIFIED | `from app.api.v1.client_cabinet import router as client_cabinet_router` and `api_v1_router.include_router(client_cabinet_router, prefix="/client", tags=["client-cabinet"])` |

#### Plan 11-02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `Caddyfile` | `public:3002` | reverse_proxy without strip_prefix | VERIFIED | Both /m/* and /my/* blocks use `reverse_proxy public:3002` with no `uri strip_prefix` directive |
| `App.tsx` | `MasterPage.tsx` | Route path=/m/:username | VERIFIED | `<Route path="/m/:username" element={<MasterPage />} />` present |

#### Plan 11-03 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `auth.ts` | `/api/v1/client/bookings` | session check with credentials:include | VERIFIED | checkSession calls apiRequest("/client/bookings", { credentials: "include" }) |
| `BookingsPage.tsx` | `/api/v1/client/bookings` | useQuery fetch with credentials | VERIFIED | queryFn: getClientBookings which uses credentials:"include" |
| `BookingCard.tsx` | `/m/{username}/book` | navigate for rebook action | VERIFIED | handleRebook navigates to `/m/${booking.master_username}/book?service=${booking.service_id}` |
| `ReviewForm.tsx` | `/api/v1/client/reviews` | POST mutation via createReview | VERIFIED | calls createReview({booking_id, rating, text}) from client-cabinet.ts which POSTs to /client/reviews |
| `App.tsx` | `LoginPage.tsx` | Route path=/my | VERIFIED | `<Route path="/my" element={<LoginPage />} />` and `<Route path="/my/bookings" element={<BookingsPage />} />` both present |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CCAB-01 | 11-01, 11-02, 11-03 | Client can access cabinet at /my by phone + 6-digit OTP | SATISFIED | /my route renders LoginPage; OTP flow fully implemented; session cookie enables persistent access |
| CCAB-02 | 11-01 | OTP sent via messenger bot (TG/MAX/VK); SMS fallback for web-booked clients | PARTIAL | Messenger delivery (TG>MAX>VK) implemented. SMS fallback is not implemented — silent success=True with "not connected" message instead of actual SMS delivery |
| CCAB-03 | 11-01, 11-03 | OTP has 5-min expiration, max 3 attempts, 60-sec cooldown | SATISFIED | All three constraints enforced in client_auth.py (constants OTP_EXPIRY_MINUTES=5, MAX_OTP_ATTEMPTS=3, COOLDOWN_SECONDS=60); countdown timer in LoginForm |
| CCAB-04 | 11-01, 11-03 | Client sees upcoming bookings with cancel/reschedule buttons | SATISFIED | BookingsPage.upcoming section; BookingCard renders cancel (functional via API) and reschedule (MVP alert placeholder per plan intent) buttons for confirmed upcoming bookings |
| CCAB-05 | 11-01, 11-03 | Client sees past visits with "Zapisatsya snova" (pre-fills master + service) | SATISFIED | BookingCard.handleRebook navigates to `/m/${master_username}/book?service=${service_id}` for past completed bookings |
| CCAB-06 | 11-01, 11-03 | Client can leave a review after completed visit (1-5 stars + optional text) | SATISFIED | ReviewForm with 5 interactive stars, optional textarea (500 char), createReview API call; backend validates completed status, ownership, no-duplicate, 30-day window |
| CCAB-07 | 11-01, 11-03 | Client sees bookings from all masters in one list | SATISFIED | GET /client/bookings queries WHERE client_id == client.id with no master_id filter; returns all cross-master bookings; BookingsPage renders them in one unified upcoming/past list |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/app/api/v1/client_auth.py` | 143-146 | Returns `success=True` when OTP cannot be delivered (no messenger platform) | Warning | Web-booked clients without a messenger platform see no error indication; they receive success but never get the OTP code. This is deferred SMS work, not a code defect, but misaligns with CCAB-02 |
| `public/src/pages/cabinet/BookingsPage.tsx` | 81 | `alert("Функция переноса записи находится в разработке")` | Info | Reschedule is a known MVP placeholder per Plan 11-03; does not block any core goal |

### Human Verification Required

#### 1. End-to-End OTP Login Flow

**Test:** Open /my in a browser; enter a valid Russian phone number for a client who has booked via Telegram; click "Получить код"; confirm 6-digit OTP inputs appear with 60-second countdown; enter the code received in Telegram; verify redirect to /my/bookings and bookings list renders.
**Expected:** Smooth two-phase flow; OTP arrives within seconds; bookings page shows correct data from all masters.
**Why human:** Requires live bot, seeded client, real Telegram delivery.

#### 2. Rebook Navigation with Pre-Selected Service

**Test:** On /my/bookings, for a past completed booking, click "Записаться снова"; verify the booking flow at /m/{username}/book opens with the correct service already selected.
**Expected:** ServiceStep shows the correct service pre-highlighted from the `?service={id}` query param.
**Why human:** Requires a live session and bookings data; query param handling in ServiceStep needs visual confirmation.

#### 3. Inline Review Submission

**Test:** Click "Оставить отзыв" on a completed past booking; select 4 stars; type optional text; click "Отправить отзыв"; verify "Спасибо за отзыв!" appears and the form closes.
**Expected:** Review created in backend; form shows success feedback; clicking again should show 409 error.
**Why human:** Requires live authenticated session and a completed booking in the database.

### Gaps Summary

**One gap blocking full CCAB-02 compliance:** The SMS fallback for web-booked clients without a messenger platform is not implemented. When a client has no linked Telegram/MAX/VK platform, `request_otp_code` logs a warning and returns `OTPResponse(success=True, message="SMS-отправка пока не подключена. Код не доставлен.")`. The client sees no error on the frontend (requestOTP resolves successfully) and receives no OTP code, making login impossible for this cohort.

The ROADMAP success criterion explicitly requires SMS fallback ("web-booked clients without a bot connection receive OTP via SMS fallback"), and CCAB-02 in REQUIREMENTS.md specifies "SMS fallback for web-booked clients (~2 rub)".

All other phase goals are fully achieved: the OTP security model (SHA256, 5-min expiry, 3 attempts, 60-sec cooldown, 7-day session cookie) is correctly implemented; the dual-path SPA routing (/m/* and /my/*) is correctly wired through Caddy, Vite, and nginx; and the full frontend cabinet (phone input, 6-digit OTP, bookings list, cancel, rebook, review form) is substantive and wired to the backend.

---

_Verified: 2026-03-21T06:00:00Z_
_Verifier: Claude (gsd-verifier)_
