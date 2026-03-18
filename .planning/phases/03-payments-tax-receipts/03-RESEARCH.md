# Phase 3: Payments + Tax Receipts - Research

**Researched:** 2026-03-18
**Domain:** Robokassa payment integration (SBP link generation, callback handling), Robochecks fiscalization for self-employed, QR code generation for manual payments, credential encryption, payment flow UX in mini-app
**Confidence:** HIGH

## Summary

Phase 3 adds three payment modes (manual income entry, Robokassa SBP link, QR with requisites) and three-tier fiscalization (no receipts / manual data for "Moy Nalog" / automatic via Robochecks) to the existing booking system. The existing `Payment` model already has the right structure (status, payment_method, receipt_status, robokassa_invoice_id) and only needs minor extension (receipt_id, fiscalization_level, receipt_data fields). The `Master` model needs new columns for payment requisites and encrypted Robokassa credentials.

The Robokassa API is straightforward: payment initiation is an HMAC-signed URL redirect, and payment confirmation is a server-to-server POST to ResultURL expecting `OK{InvId}` response. The signature formula is `hash(MerchantLogin:OutSum:InvId:Receipt:Password#1)` for initiation and `hash(OutSum:InvId:Password#2)` for callback verification. The hash algorithm (MD5/SHA256) is configured in the Robokassa dashboard.

The critical architectural decision: Robochecks for self-employed (SMZ) works **automatically** when activated -- once the master grants permission in "Moy Nalog" app and activates Robochecks in Robokassa dashboard, receipts are auto-generated for every Robokassa payment. This means no separate receipt API calls are needed for the "automatic" fiscalization level -- the Receipt JSON parameter in the payment request triggers it. For receipt cancellation on refund, the Robokassa refund API handles receipt annulment automatically. For the "manual" fiscalization level, the CRM simply displays pre-formatted data for the master to copy into "Moy Nalog" app.

**Primary recommendation:** Build a `RobokassaService` (~250 lines) that handles payment URL generation, signature calculation, callback verification, and receipt JSON construction. Store per-master Robokassa credentials encrypted with Fernet (key from `ENCRYPTION_KEY` env var). Use the `qrcode` library (8.2) to generate QR codes for manual payment mode (encoding card number or phone into a plain text QR -- there is no universal SBP deeplink format for P2P transfers). Implement callback idempotency via `robokassa_invoice_id` unique constraint (already exists on Payment model).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **3 payment options for master:** (1) manual income entry, (2) Robokassa SBP link, (3) QR with requisites
- Master chooses which option at each payment, not locked globally
- "Zavershit" button on booking -> payment options bottom sheet
- Payment can happen right after booking confirmation OR after actual visit
- **Simple mode:** master enters card number, phone for SBP, bank name in Settings
- CRM shows master's requisites to client + generated QR code
- Master taps "Oplacheno" + selects payment method
- **Robokassa connection:** step-by-step wizard in Settings with screenshots
- Master enters: merchant_login, password1, password2
- Test mode toggle
- Credentials stored encrypted in DB (per-master, not platform-level)
- **Fiscalization 3 levels:** default in Settings + per-payment override
  - Level 1 (grey): one-time warning, no nagging after
  - Level 2 (manual): CRM shows ready-to-copy data for "Moy Nalog"
  - Level 3 (auto): Robochecks receipt auto-generated via Robokassa
- **Refunds:** manual only, no auto-refund through Robokassa in v1
- **Receipt cancellation:** auto if Robokassa connected, reminder if manual mode
- **Payment history:** statuses (pending, paid, cancelled, refunded) + receipt statuses (not_applicable, pending, issued, cancelled)
- Filterable by date range, status

### Claude's Discretion
- QR code generation library
- Robokassa API integration details (HMAC signing, URL format)
- Robochecks API for receipt generation/cancellation
- Payment webhook security (idempotency, signature validation)
- Database migration for payment-related columns
- Encryption approach for Robokassa credentials
- Payment notification message format

### Deferred Ideas (OUT OF SCOPE)
- Auto-refund through Robokassa API -- too complex for v1, manual refunds sufficient
- Per-service pricing variants (short hair vs long hair pricing) -- v2
- Subscription/recurring payment support -- v2
- Revenue analytics from payments -- Phase after all core features
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PAY-01 | Master can complete a visit and mark "Paid" (simple mode, cash/card-to-card) | Manual payment recording via PaymentService.create_manual_payment(). Extend booking status to "completed". Payment bottom sheet UI after "Zavershit". |
| PAY-02 | Master can optionally connect their own Robokassa for automatic SBP link | Settings wizard for Robokassa credentials. Fernet encryption for passwords. Test mode toggle. Validation endpoint to verify credentials work. |
| PAY-03 | With Robokassa connected: master taps "Complete" -> client gets SBP payment link | RobokassaService generates signed payment URL. Payment link sent to client via NotificationService. ResultURL callback handler with idempotency. |
| PAY-04 | Payment history with statuses (pending, paid, cancelled) | Extend existing Payment model. List endpoint with date/status filters. Receipt status tracking alongside payment status. |
| TAX-01 | Three fiscalization levels: no receipts / manual / automatic | fiscalization_level column on Master (default) + per-payment override on Payment. FiscalizationLevel enum. |
| TAX-02 | No receipts: master sees warning but can continue | One-time warning flag (has_seen_grey_warning) on Master. Show warning only on first selection. |
| TAX-03 | Manual: after payment, CRM shows ready data for "Moy Nalog" | Format payment data as copyable text: amount, service name, client name. "Copy data" button + "Open Moy Nalog" deep link. |
| TAX-04 | Automatic: with Robokassa connected, receipt auto-generated via Robochecks | Receipt JSON parameter in Robokassa payment URL. sno field configured per master. receipt_status tracking on Payment. Robochecks activates in Robokassa dashboard. |
</phase_requirements>

## Standard Stack

### Core (New Dependencies for Phase 3)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| cryptography | 46.0.5 | Fernet symmetric encryption | Encrypt per-master Robokassa passwords at rest. AES-128-CBC + HMAC-SHA256. Industry standard Python crypto library. Released Feb 2026. |
| qrcode | 8.2 | QR code generation | Generate QR codes for manual payment mode (card/phone requisites). Pure Python, PNG output via pypng. Released May 2025. |
| pypng | (qrcode dep) | PNG image generation | Transitive dependency of qrcode for PNG output. |

### Already in Stack (No New Install Needed)

| Library | Version | Purpose | Phase 3 Use |
|---------|---------|---------|-------------|
| FastAPI | 0.135.1+ | Web framework | Robokassa callback webhook route, payment API endpoints |
| SQLAlchemy | 2.0.48+ | ORM | Payment model extension, migration |
| Alembic | 1.18.4+ | Migrations | Add payment/master columns |
| Pydantic | 2.12+ | Validation | Payment schemas, Receipt JSON construction |
| PyJWT | 2.12.1+ | JWT auth | Existing auth for master endpoints |
| aiogram | 3.20+ | TG bot | Send payment links to clients via bot messages |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| cryptography (Fernet) | Custom AES wrapper | Fernet handles key derivation, IV, HMAC, padding. Hand-rolling is error-prone. |
| qrcode | segno | segno is faster but less popular. qrcode has 15M+ downloads/month, better community support. |
| qrcode | Frontend QR generation (qrcode.react) | Backend generation is better: QR can be embedded in bot messages as images, works across all platforms. |
| Custom Robokassa wrapper | robokassa PyPI package (1.0.8) | robokassa package is thin, unmaintained, no Robochecks support. Custom wrapper is ~250 lines and gives full control. |
| Custom Robokassa wrapper | aiorobokassa | aiorobokassa adds unnecessary abstraction. The API is 3 functions: generate URL, verify callback, build receipt JSON. |

**Installation:**
```bash
cd /Users/yannovak/development/projects/master_crm/backend
uv add cryptography qrcode
```

## Architecture Patterns

### Recommended Project Structure (Phase 3 Additions)

```
backend/app/
  api/v1/
    payments.py           # NEW: Payment CRUD + payment flow endpoints
    settings.py           # UPDATE: Add payment settings (requisites, Robokassa, fiscalization)
    router.py             # UPDATE: Include payments router
  services/
    payment_service.py    # NEW: Payment flow orchestration
    robokassa_service.py  # NEW: Robokassa API wrapper (~250 lines)
    encryption_service.py # NEW: Fernet encrypt/decrypt for credentials (~50 lines)
    qr_service.py         # NEW: QR code generation for requisites (~40 lines)
  schemas/
    payment.py            # NEW: Payment create/read/list schemas
    settings.py           # UPDATE: Add payment settings fields
  models/
    payment.py            # UPDATE: Add receipt fields, fiscalization_level
    master.py             # UPDATE: Add payment requisites, Robokassa credentials, fiscalization settings
  core/
    config.py             # UPDATE: Add ENCRYPTION_KEY, ROBOKASSA_RESULT_URL_BASE
  main.py                 # UPDATE: Add Robokassa callback webhook route
  bots/
    common/
      adapter.py          # UPDATE: Add send_payment_link method to MessengerAdapter
      notification.py     # UPDATE: Add send_payment_notification method
    telegram/
      adapter.py          # UPDATE: Implement send_payment_link (inline button with URL)
frontend/src/
  pages/master/
    Bookings.tsx          # UPDATE: Add "Zavershit" button + payment bottom sheet
    Settings.tsx          # UPDATE: Add payment config sections (requisites, Robokassa wizard, fiscalization)
    PaymentHistory.tsx    # NEW: Payment history list with filters
  components/
    PaymentSheet.tsx      # NEW: Bottom sheet for payment flow (3 options)
    ReceiptDataCard.tsx   # NEW: Copyable receipt data for manual fiscalization
    RobokassaWizard.tsx   # NEW: Step-by-step Robokassa setup
  api/
    payments.ts           # NEW: TanStack Query hooks for payment endpoints
    master-settings.ts    # UPDATE: Add payment settings mutations
```

### Pattern 1: RobokassaService (Payment URL Generation + Callback Verification)

**What:** A stateless service class that handles all Robokassa API interactions: generating signed payment URLs, verifying ResultURL callbacks, and constructing Receipt JSON for fiscalization.

**When:** Payment initiation (URL generation) and payment confirmation (callback verification).

**Critical details:**
- Payment URL: `https://auth.robokassa.ru/Merchant/Index.aspx` (POST or redirect)
- Signature for initiation: `hash(MerchantLogin:OutSum:InvId:Receipt:Password#1)` -- Receipt is URL-encoded JSON, included only if fiscalization is enabled
- Signature for callback: `hash(OutSum:InvId:Password#2)` -- simpler, uses Password#2
- Hash algorithm: configurable (MD5/SHA256/SHA512), set in Robokassa dashboard
- Shp_ custom parameters: sorted alphabetically, appended after Password in signature: `hash(MerchantLogin:OutSum:InvId:Password#1:Shp_booking_id=xxx:Shp_master_id=yyy)`
- Test mode: append `IsTest=1` to payment URL params
- ResultURL must return `OK{InvId}` as plain text with HTTP 200

**Example:**
```python
# backend/app/services/robokassa_service.py
import hashlib
import json
import urllib.parse
from dataclasses import dataclass


@dataclass
class RobokassaCredentials:
    merchant_login: str
    password1: str  # decrypted
    password2: str  # decrypted
    is_test: bool = False
    hash_algorithm: str = "sha256"  # md5, sha256, sha512


class RobokassaService:
    """Stateless service for Robokassa payment integration."""

    PAYMENT_URL = "https://auth.robokassa.ru/Merchant/Index.aspx"
    TEST_PAYMENT_URL = "https://auth.robokassa.ru/Merchant/Index.aspx"

    @staticmethod
    def _compute_hash(data: str, algorithm: str) -> str:
        """Compute hash using the configured algorithm."""
        if algorithm == "md5":
            return hashlib.md5(data.encode("utf-8")).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(data.encode("utf-8")).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(data.encode("utf-8")).hexdigest()
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    @staticmethod
    def generate_payment_url(
        creds: RobokassaCredentials,
        inv_id: int,
        out_sum: str,  # "100.00" format
        description: str,
        receipt_json: dict | None = None,
        shp_params: dict[str, str] | None = None,
        email: str | None = None,
    ) -> str:
        """Generate a signed Robokassa payment URL."""
        # Build signature string
        sig_parts = [creds.merchant_login, out_sum, str(inv_id)]

        # Include Receipt in signature if present
        receipt_encoded = None
        if receipt_json:
            receipt_str = json.dumps(receipt_json, ensure_ascii=False)
            receipt_encoded = urllib.parse.quote(receipt_str)
            sig_parts.append(receipt_encoded)

        sig_parts.append(creds.password1)

        # Append Shp_ params sorted alphabetically
        if shp_params:
            for key in sorted(shp_params.keys()):
                sig_parts.append(f"{key}={shp_params[key]}")

        signature = RobokassaService._compute_hash(
            ":".join(sig_parts), creds.hash_algorithm
        )

        # Build URL params
        params = {
            "MerchantLogin": creds.merchant_login,
            "OutSum": out_sum,
            "InvId": str(inv_id),
            "SignatureValue": signature,
            "Description": description,
        }
        if receipt_encoded:
            params["Receipt"] = receipt_encoded
        if email:
            params["Email"] = email
        if creds.is_test:
            params["IsTest"] = "1"
        if shp_params:
            params.update(shp_params)

        return f"{RobokassaService.PAYMENT_URL}?{urllib.parse.urlencode(params)}"

    @staticmethod
    def verify_result_signature(
        creds: RobokassaCredentials,
        out_sum: str,
        inv_id: str,
        received_signature: str,
        shp_params: dict[str, str] | None = None,
    ) -> bool:
        """Verify ResultURL callback signature using Password#2."""
        sig_parts = [out_sum, str(inv_id), creds.password2]

        if shp_params:
            for key in sorted(shp_params.keys()):
                sig_parts.append(f"{key}={shp_params[key]}")

        expected = RobokassaService._compute_hash(
            ":".join(sig_parts), creds.hash_algorithm
        )
        # Case-insensitive comparison (Robokassa sends uppercase)
        return expected.upper() == received_signature.upper()

    @staticmethod
    def build_receipt_json(
        service_name: str,
        amount_rub: str,  # "1500.00"
        sno: str = "patent",  # or configured per master
    ) -> dict:
        """Build Receipt JSON for fiscalization (54-FZ)."""
        return {
            "sno": sno,
            "items": [
                {
                    "name": service_name[:128],  # max 128 chars
                    "quantity": 1,
                    "sum": float(amount_rub),
                    "payment_method": "full_payment",
                    "payment_object": "service",
                    "tax": "none",  # self-employed on NPD/patent = no VAT
                }
            ],
        }
```

**Confidence:** HIGH -- Signature formulas verified across multiple sources (official Robokassa docs, PHP/Python/Node.js implementations). Receipt JSON structure verified against official fiscalization docs.

### Pattern 2: Credential Encryption with Fernet

**What:** Encrypt per-master Robokassa passwords before storing in the database. Decrypt on demand when generating payment URLs or verifying callbacks.

**When:** Saving Robokassa credentials in Settings, reading them for payment operations.

**Critical details:**
- Single `ENCRYPTION_KEY` in env vars, generated once with `Fernet.generate_key()`
- Store encrypted bytes as text (base64) in DB columns
- Fernet provides authenticated encryption (AES-128-CBC + HMAC-SHA256)
- If the key is compromised, all stored credentials must be re-encrypted with a new key

**Example:**
```python
# backend/app/services/encryption_service.py
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def get_fernet() -> Fernet:
    """Get Fernet instance using the app encryption key."""
    return Fernet(settings.encryption_key.encode("utf-8"))


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value. Returns base64-encoded ciphertext."""
    f = get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str | None:
    """Decrypt a string value. Returns None if decryption fails."""
    try:
        f = get_fernet()
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
```

**Confidence:** HIGH -- Fernet is the standard Python approach for symmetric encryption. The `cryptography` library is maintained by the Python Cryptographic Authority.

### Pattern 3: Payment Callback with Idempotency

**What:** Handle Robokassa ResultURL callback idempotently. The callback may be sent multiple times if the first response is not `OK{InvId}`.

**When:** Every Robokassa payment completion.

**Critical flow:**
1. Receive POST from Robokassa with OutSum, InvId, SignatureValue, Shp_* params
2. Look up master's credentials by Shp_master_id
3. Verify signature with Password#2
4. Check idempotency: if Payment with this InvId is already "paid", return `OK{InvId}` immediately
5. Update Payment status to "paid", set paid_at timestamp
6. Send payment confirmation notification to master via bot
7. Return `OK{InvId}` as plain text

**Example:**
```python
# In main.py or a dedicated webhook router
from fastapi import Request
from fastapi.responses import PlainTextResponse

@app.post("/webhook/robokassa/result")
async def robokassa_result_callback(request: Request):
    """Robokassa ResultURL callback handler.

    MUST return OK{InvId} on success, otherwise Robokassa retries.
    """
    form_data = await request.form()

    out_sum = form_data.get("OutSum", "")
    inv_id = form_data.get("InvId", "")
    signature = form_data.get("SignatureValue", "")

    # Extract Shp_ params
    shp_params = {
        k: v for k, v in form_data.items() if k.startswith("Shp_")
    }
    master_id = shp_params.get("Shp_master_id")

    if not master_id or not inv_id:
        return PlainTextResponse("bad request", status_code=400)

    # Look up payment + master credentials, verify, update
    # (delegated to payment_service)
    success = await payment_service.handle_robokassa_callback(
        master_id=master_id,
        inv_id=int(inv_id),
        out_sum=out_sum,
        signature=signature,
        shp_params=shp_params,
    )

    if success:
        return PlainTextResponse(f"OK{inv_id}")

    return PlainTextResponse("signature verification failed", status_code=403)
```

**Confidence:** HIGH -- ResultURL response format (`OK{InvId}`) confirmed in official docs. Idempotency pattern (check-before-update) is standard.

### Pattern 4: QR Code Generation for Manual Payments

**What:** Generate a QR code containing the master's payment requisites (card number or phone number for SBP transfer). The client scans the QR in their banking app.

**When:** Master selects "Show requisites + QR" payment option.

**Critical insight:** There is no universal SBP deeplink format for person-to-person transfers. Each bank has its own deeplink scheme. The practical approach is to encode the card number or phone number as plain text in the QR code. When a client scans it with their camera, their banking app will recognize the phone number for SBP transfer. For card-to-card transfers, the client manually enters the card number shown alongside the QR.

**Example:**
```python
# backend/app/services/qr_service.py
import io
import base64
import qrcode
from qrcode.image.pil import PilImage


def generate_payment_qr(
    data: str,
    box_size: int = 8,
    border: int = 2,
) -> str:
    """Generate a QR code and return as base64-encoded PNG.

    data: phone number ("+79161234567") or card number ("2200123456789012")
    Returns: base64 string suitable for <img src="data:image/png;base64,...">
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("utf-8")
```

**Confidence:** HIGH for QR generation, MEDIUM for SBP integration. SBP does not have a public deeplink standard for P2P transfers -- encoding the phone number as text is the practical approach used by services like stqr.ru.

### Pattern 5: Payment Flow Bottom Sheet

**What:** When master taps "Zavershit" on a booking, a bottom sheet appears with three payment options. The flow differs based on the selected option.

**When:** After master completes a service (booking status transitions to "completed").

**Flow for each option:**
1. **Manual income entry:** Master selects payment method (cash/card/transfer/SBP) -> Payment created with status "paid" -> If fiscalization is "manual", show receipt data card -> Done
2. **Robokassa SBP link:** Payment created with status "pending" -> Robokassa URL generated -> Link sent to client via bot -> Await callback -> Status becomes "paid" -> Receipt auto-generated if Robochecks active
3. **Show requisites + QR:** Payment created with status "pending" -> Show master's card/phone + QR code to client -> Master taps "Paid" when payment received -> Status becomes "paid" -> If fiscalization is "manual", show receipt data card -> Done

**Confidence:** HIGH -- follows established booking flow patterns from Phase 2.

### Anti-Patterns to Avoid

- **Blocking ResultURL handler on heavy processing:** Return `OK{InvId}` immediately, then process notifications/receipt tracking asynchronously. Robokassa retries if no response within a few seconds.
- **Mixing Password#1 and Password#2:** Password#1 is for payment URL generation. Password#2 is for callback verification. Never swap them.
- **Storing Robokassa passwords in plaintext:** Even in the database. Always encrypt with Fernet.
- **Case-sensitive signature comparison:** Robokassa sends SignatureValue in uppercase. Always compare `.upper()` to `.upper()`.
- **Hardcoding hash algorithm:** Hash algorithm is configured per merchant in Robokassa dashboard. Store the algorithm choice alongside credentials and use it dynamically.
- **Generating InvId from auto-increment:** Use a unique integer sequence per master or a global sequence. InvId must be unique within the Robokassa merchant account. Since each master has their own merchant account, InvId can be a simple per-payment counter.
- **Skipping receipt in signature:** If Receipt parameter is included in the payment URL, it MUST also be included in the signature calculation between InvId and Password#1.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Credential encryption | Custom AES/XOR cipher | `cryptography.fernet.Fernet` | Handles IV generation, padding, HMAC authentication, base64 encoding. 3 lines vs 50+ with edge cases. |
| QR code generation | Canvas/SVG drawing code | `qrcode` library (8.2) | Handles error correction levels, optimal encoding mode, sizing. Outputs PNG/SVG/ASCII. |
| Robokassa signature | Manual string concatenation | `RobokassaService._compute_hash()` | Centralized, testable, handles Shp_ param sorting and Receipt URL-encoding. |
| Receipt JSON construction | Manual dict building scattered across codebase | `RobokassaService.build_receipt_json()` | Enforces 128-char name limit, correct field names, proper sno value. Single source of truth. |
| Payment status machine | Ad-hoc status string assignments | Explicit status transition validator | Prevents invalid transitions (e.g., "cancelled" -> "paid"). |

**Key insight:** The Robokassa API is intentionally simple (3 functions: generate URL, verify callback, build receipt). The complexity is in the integration plumbing: idempotency, credential management, status tracking, notification sending. Don't over-abstract the API wrapper -- keep it thin and put the intelligence in PaymentService.

## Common Pitfalls

### Pitfall 1: Robokassa Password Case Sensitivity
**What goes wrong:** Signature verification fails intermittently. The Robokassa dashboard shows successful payment, but your callback handler rejects the signature.
**Why it happens:** Robokassa has known issues with password case sensitivity. Passwords with mixed case in the dashboard may behave differently in hash calculations.
**How to avoid:** Keep passwords lowercase in both the Robokassa dashboard and your stored credentials. When comparing signatures, always use `.upper()` on both sides (Robokassa sends SignatureValue in uppercase).
**Warning signs:** Sporadic signature mismatch errors in logs.

### Pitfall 2: ResultURL Not Accessible
**What goes wrong:** Client pays successfully, but the payment is never confirmed in your system. The booking stays in "pending" state.
**Why it happens:** Robokassa sends the ResultURL callback server-to-server. If your server is behind a firewall, on a non-standard port, or the URL is not publicly accessible, the callback never arrives. Test mode may also use different URLs.
**How to avoid:** Ensure the ResultURL is a publicly accessible HTTPS endpoint on port 443. Test the full flow in Robokassa test mode before going live. Log all incoming requests to the callback endpoint.
**Warning signs:** Payments in Robokassa dashboard marked as paid but your DB shows "pending".

### Pitfall 3: Receipt Included in URL but Not in Signature
**What goes wrong:** Payment initiation fails with "signature error" from Robokassa.
**Why it happens:** When the Receipt JSON parameter is sent with the payment URL, it must also be included in the signature calculation: `hash(MerchantLogin:OutSum:InvId:Receipt:Password#1)`. Developers forget to add Receipt between InvId and Password#1.
**How to avoid:** The `RobokassaService.generate_payment_url()` method handles this automatically -- always use it, never construct URLs manually. The Receipt must be URL-encoded before inclusion in both the signature and the URL params.
**Warning signs:** Payments with fiscalization fail, but payments without fiscalization work fine.

### Pitfall 4: Duplicate Payment Processing
**What goes wrong:** Robokassa sends the ResultURL callback twice (retry after timeout). The system processes both, creating duplicate payment records or sending duplicate notifications.
**Why it happens:** The first callback took too long to process (sending notifications, updating multiple tables before returning `OK{InvId}`).
**How to avoid:** (1) Return `OK{InvId}` immediately at the start of processing, after signature verification. (2) Check idempotency: if Payment with this InvId already has status "paid", skip processing. (3) Use database-level unique constraint on `robokassa_invoice_id`.
**Warning signs:** Duplicate bot messages to master, duplicate payment records.

### Pitfall 5: Encryption Key Loss
**What goes wrong:** The `ENCRYPTION_KEY` environment variable is lost or changed. All stored Robokassa credentials become undecryptable. Every master must re-enter their credentials.
**Why it happens:** Key stored only in .env file, server rebuilt without backing up env vars.
**How to avoid:** (1) Back up `ENCRYPTION_KEY` in a secure location (password manager, not git). (2) Add a health check that verifies decryption works on startup. (3) Document key rotation procedure.
**Warning signs:** `InvalidToken` exceptions when reading Robokassa credentials.

### Pitfall 6: InvId Uniqueness Within Merchant Account
**What goes wrong:** Two payments from different bookings get the same InvId. Robokassa rejects the second payment or associates it with the wrong booking.
**Why it happens:** Each master has their own Robokassa merchant account. InvId must be unique within that account. If using a global auto-increment, it works. If using booking_id (UUID), Robokassa requires InvId to be an integer (1-2147483647).
**How to avoid:** Use a sequential integer (database sequence) as InvId. Store the mapping between InvId and your Payment UUID. Since each master has their own Robokassa account, a simple per-payment counter works.
**Warning signs:** Robokassa returns "duplicate InvId" error.

## Code Examples

### Database Migration for Phase 3

```python
# alembic/versions/004_add_payment_and_settings_columns.py
def upgrade():
    # Extend masters table with payment settings
    op.add_column("masters", sa.Column(
        "card_number", sa.String(20), nullable=True
    ))
    op.add_column("masters", sa.Column(
        "sbp_phone", sa.String(20), nullable=True
    ))
    op.add_column("masters", sa.Column(
        "bank_name", sa.String(100), nullable=True
    ))
    op.add_column("masters", sa.Column(
        "robokassa_merchant_login", sa.String(255), nullable=True
    ))
    op.add_column("masters", sa.Column(
        "robokassa_password1_encrypted", sa.Text, nullable=True
    ))
    op.add_column("masters", sa.Column(
        "robokassa_password2_encrypted", sa.Text, nullable=True
    ))
    op.add_column("masters", sa.Column(
        "robokassa_is_test", sa.Boolean, default=False, nullable=False,
        server_default="false"
    ))
    op.add_column("masters", sa.Column(
        "robokassa_hash_algorithm", sa.String(10), default="sha256",
        nullable=False, server_default="sha256"
    ))
    op.add_column("masters", sa.Column(
        "fiscalization_level", sa.String(20), default="none",
        nullable=False, server_default="none"
    ))  # none, manual, auto
    op.add_column("masters", sa.Column(
        "has_seen_grey_warning", sa.Boolean, default=False,
        nullable=False, server_default="false"
    ))
    op.add_column("masters", sa.Column(
        "receipt_sno", sa.String(30), default="patent",
        nullable=False, server_default="patent"
    ))  # osn, usn_income, patent, etc.

    # Extend payments table
    op.add_column("payments", sa.Column(
        "robokassa_inv_id", sa.Integer, nullable=True, unique=True
    ))
    op.add_column("payments", sa.Column(
        "fiscalization_level", sa.String(20), nullable=True
    ))  # per-payment override
    op.add_column("payments", sa.Column(
        "receipt_data", sa.Text, nullable=True
    ))  # JSON receipt data for manual mode
    op.add_column("payments", sa.Column(
        "receipt_id", sa.String(255), nullable=True
    ))  # Robokassa receipt ID
    op.add_column("payments", sa.Column(
        "payment_url", sa.Text, nullable=True
    ))  # Robokassa payment URL

    # Create index for payment history queries
    op.create_index(
        "ix_payments_master_id_created_at",
        "payments",
        ["master_id", "created_at"],
    )


def downgrade():
    # Remove indexes
    op.drop_index("ix_payments_master_id_created_at")

    # Remove payment columns
    for col in ["robokassa_inv_id", "fiscalization_level",
                "receipt_data", "receipt_id", "payment_url"]:
        op.drop_column("payments", col)

    # Remove master columns
    for col in ["card_number", "sbp_phone", "bank_name",
                "robokassa_merchant_login", "robokassa_password1_encrypted",
                "robokassa_password2_encrypted", "robokassa_is_test",
                "robokassa_hash_algorithm", "fiscalization_level",
                "has_seen_grey_warning", "receipt_sno"]:
        op.drop_column("masters", col)
```

### Payment Settings Schema Extension

```python
# backend/app/schemas/settings.py -- extended
class PaymentSettings(BaseModel):
    # Simple mode requisites
    card_number: str | None = None
    sbp_phone: str | None = None
    bank_name: str | None = None

    # Robokassa
    has_robokassa: bool = False  # computed: merchant_login is not None
    robokassa_is_test: bool = False
    robokassa_hash_algorithm: str = "sha256"

    # Fiscalization
    fiscalization_level: str = "none"  # none, manual, auto
    has_seen_grey_warning: bool = False
    receipt_sno: str = "patent"

    model_config = {"from_attributes": True}


class RobokassaSetup(BaseModel):
    merchant_login: str = Field(min_length=1)
    password1: str = Field(min_length=1)
    password2: str = Field(min_length=1)
    is_test: bool = False
    hash_algorithm: str = Field(default="sha256", pattern="^(md5|sha256|sha512)$")
```

### Payment Notification via Bot

```python
# Extend MessengerAdapter with payment-related methods
class MessengerAdapter(ABC):
    # ... existing methods ...

    @abstractmethod
    async def send_payment_link(
        self,
        platform_user_id: str,
        payment_url: str,
        service_name: str,
        amount_display: str,  # "1 500 ₽"
    ) -> bool:
        """Send a payment link button to the client."""
        ...

# TelegramAdapter implementation
async def send_payment_link(
    self, platform_user_id: str, payment_url: str,
    service_name: str, amount_display: str,
) -> bool:
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    text = (
        f"Оплата за услугу <b>{service_name}</b>\n"
        f"Сумма: <b>{amount_display}</b>\n\n"
        f"Нажмите кнопку ниже для оплаты через СБП:"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить", url=payment_url)]
    ])

    await self.bot.send_message(
        chat_id=int(platform_user_id),
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return True
```

### Receipt Data for Manual Fiscalization

```python
def format_receipt_data_for_manual(
    amount_kopecks: int,
    service_name: str,
    client_name: str,
) -> str:
    """Format payment data for manual entry into 'Moy Nalog' app.

    Returns a human-readable string for the master to copy.
    """
    amount_rub = amount_kopecks / 100
    return (
        f"Сумма: {amount_rub:.2f} ₽\n"
        f"Услуга: {service_name}\n"
        f"Клиент: {client_name}\n"
        f"Дата: {datetime.now().strftime('%d.%m.%Y')}"
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| MD5 for Robokassa signatures | SHA-256 recommended | 2023+ | MD5 still supported but SHA-256 is preferred. Configure in Robokassa dashboard. |
| passlib for encryption | cryptography.fernet | 2024+ | passlib is abandoned. Fernet from `cryptography` is the standard. |
| SBP via bank-specific APIs | SBP still no universal P2P deeplink | Current | No standard deeplink for P2P SBP transfers. QR with phone number is the practical approach. |
| Robochecks manual API calls | Robochecks auto-activates with Receipt param | Current | For SMZ, receipt is auto-generated when Receipt JSON is included in payment URL and Robochecks is activated in dashboard. |

**Deprecated/outdated:**
- MD5 for signatures: still works but SHA-256 is recommended. Default in new Robokassa accounts may be SHA-256.
- robokassa PyPI package (1.0.8): last release unclear, no Robochecks support. Build custom.

## Open Questions

1. **Robochecks SNO value for self-employed (SMZ)**
   - What we know: Official Robokassa fiscalization docs list sno values: `osn`, `usn_income`, `usn_income_outcome`, `esn`, `patent`. Self-employed on NPD is NOT explicitly listed.
   - What's unclear: Whether SMZ uses a special sno value or if Robochecks SMZ handles it differently from the standard Receipt parameter. The Robochecks SMZ service may bypass the standard fiscalization Receipt parameter entirely.
   - Recommendation: Start with `receipt_sno` defaulting to `"patent"` (most common for self-employed masters). If the master is on NPD specifically, Robochecks SMZ may handle fiscalization separately from the Receipt parameter. Test in Robokassa test mode. The master can configure their sno in Settings.

2. **InvId strategy for per-master Robokassa accounts**
   - What we know: InvId must be a positive integer, unique within the merchant account. Each master has their own Robokassa merchant account.
   - What's unclear: Whether to use a global database sequence or a per-master counter.
   - Recommendation: Use a global database sequence (`CREATE SEQUENCE robokassa_inv_id_seq`). Even though InvId uniqueness is per-merchant-account, a global sequence is simpler and still unique. Map InvId to Payment UUID in the `robokassa_inv_id` column.

3. **Robokassa callback URL with per-master routing**
   - What we know: Robokassa sends callbacks to the ResultURL configured in the merchant dashboard. Each master has their own merchant account with their own ResultURL.
   - What's unclear: Whether the ResultURL can be set per-payment or is fixed in the dashboard. If fixed, all masters' Robokassa accounts must point to the same callback URL.
   - Recommendation: Use a single callback URL (`/webhook/robokassa/result`) and identify the master via `Shp_master_id` custom parameter. This avoids requiring each master to configure a different ResultURL. The master configures their ResultURL in the Robokassa dashboard to point to your server's callback endpoint.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (existing) |
| Config file | `backend/pyproject.toml` [tool.pytest.ini_options] -- exists |
| Quick run command | `cd /Users/yannovak/development/projects/master_crm/backend && uv run pytest tests/ -x -q` |
| Full suite command | `cd /Users/yannovak/development/projects/master_crm/backend && uv run pytest tests/ -v --tb=short` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PAY-01 | Manual payment creation (cash/card/transfer/SBP) | integration | `uv run pytest tests/test_payments.py::test_create_manual_payment -x` | No -- Wave 0 |
| PAY-01 | Booking status transitions to "completed" on payment | integration | `uv run pytest tests/test_payments.py::test_booking_completed_on_payment -x` | No -- Wave 0 |
| PAY-02 | Save encrypted Robokassa credentials | integration | `uv run pytest tests/test_payments.py::test_save_robokassa_credentials -x` | No -- Wave 0 |
| PAY-02 | Decrypt credentials for payment URL generation | unit | `uv run pytest tests/test_robokassa.py::test_encrypt_decrypt_roundtrip -x` | No -- Wave 0 |
| PAY-03 | Generate signed Robokassa payment URL | unit | `uv run pytest tests/test_robokassa.py::test_generate_payment_url -x` | No -- Wave 0 |
| PAY-03 | Verify ResultURL callback signature | unit | `uv run pytest tests/test_robokassa.py::test_verify_result_signature -x` | No -- Wave 0 |
| PAY-03 | Idempotent callback handling (duplicate InvId) | integration | `uv run pytest tests/test_payments.py::test_idempotent_callback -x` | No -- Wave 0 |
| PAY-04 | Payment history with status/date filters | integration | `uv run pytest tests/test_payments.py::test_payment_history_filters -x` | No -- Wave 0 |
| TAX-01 | Fiscalization level stored on master and per-payment | integration | `uv run pytest tests/test_payments.py::test_fiscalization_levels -x` | No -- Wave 0 |
| TAX-02 | Grey warning shown only once | integration | `uv run pytest tests/test_settings.py::test_grey_warning_flag -x` | No -- Wave 0 |
| TAX-03 | Manual receipt data formatted correctly | unit | `uv run pytest tests/test_robokassa.py::test_format_receipt_data -x` | No -- Wave 0 |
| TAX-04 | Receipt JSON included in payment URL and signature | unit | `uv run pytest tests/test_robokassa.py::test_receipt_in_signature -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd /Users/yannovak/development/projects/master_crm/backend && uv run pytest tests/ -x -q`
- **Per wave merge:** `cd /Users/yannovak/development/projects/master_crm/backend && uv run pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_robokassa.py` -- covers PAY-03, TAX-03, TAX-04 (unit tests for RobokassaService)
- [ ] `backend/tests/test_payments.py` -- covers PAY-01, PAY-02, PAY-03, PAY-04, TAX-01 (integration tests)
- [ ] `backend/tests/test_settings.py` -- UPDATE existing file for TAX-02 (grey warning flag)
- [ ] Framework install: `uv add cryptography qrcode` -- Phase 3 dependencies

## Sources

### Primary (HIGH confidence)
- [Robokassa Official Documentation](https://docs.robokassa.ru/) -- Payment URL format, signature formulas, callback handling
- [Robokassa API integration guide](https://robokassa.com/blog/articles/podklyuchenie-robokassa-k-vashey-platforme/) -- Signature formula: `MD5(MerchantLogin:OutSum:InvId:Password#1)`, ResultURL format `OK{InvId}`
- [Robokassa Fiscalization docs](https://docs.robokassa.ru/ru/fiscalization) -- Receipt JSON structure, sno values, items array, signature with Receipt
- [Robochecks SMZ for self-employed](https://robokassa.com/online-check/robocheck-smz/) -- Auto-activation, "Moy Nalog" integration
- [cryptography.fernet docs](https://cryptography.io/en/latest/fernet/) -- Fernet API, key generation, encrypt/decrypt
- [PyPI: cryptography 46.0.5](https://pypi.org/project/cryptography/) -- Feb 2026
- [PyPI: qrcode 8.2](https://pypi.org/project/qrcode/) -- May 2025
- [Robokassa Robochecks self-employed page](https://robokassa.com/solutions/business/samozanyatye/) -- Setup process for SMZ

### Secondary (MEDIUM confidence)
- [Robokassa PHP implementation (kvalood)](https://github.com/kvalood/Robokassa/blob/master/Robokassa.php) -- Receipt JSON structure with sno, items, tax fields
- [Robokassa Python library (byBenPuls)](https://github.com/byBenPuls/robokassa) -- HashAlgorithm enum, payment link generation API
- [Robokassa Node.js implementation (betsol)](https://github.com/betsol/node-robokassa) -- Password case sensitivity issue documentation
- [SBP QR code generator (stqr.ru)](https://stqr.ru/generator/sbp) -- Practical SBP QR approach for Russia
- [NSPK SBP official site](https://sbp.nspk.ru/) -- SBP payment modes (QR, NFC, link, bound account)
- Existing codebase: `backend/app/models/payment.py` -- Payment model already has status, payment_method, receipt_status, robokassa_invoice_id columns
- Existing codebase: `backend/app/core/security.py` -- HMAC pattern reusable for Robokassa signatures

### Tertiary (LOW confidence)
- Robokassa SNO for self-employed (NPD): NOT explicitly documented in the standard fiscalization docs. The Robochecks SMZ service may handle this separately. Needs testing in Robokassa test mode.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- cryptography and qrcode are well-established, versions verified on PyPI
- Architecture (RobokassaService): HIGH -- Signature formulas verified across official docs and 4+ implementations (PHP, Python, Node.js, Ruby)
- Architecture (callback handling): HIGH -- `OK{InvId}` response format confirmed in official docs
- Pitfalls: HIGH -- Password case sensitivity, Receipt in signature, idempotency all documented across multiple sources
- Fiscalization (standard): HIGH -- Receipt JSON structure verified against official docs and implementations
- Fiscalization (SMZ/NPD sno): LOW -- Not explicitly documented for self-employed. Needs testing.
- QR for SBP: MEDIUM -- No universal SBP deeplink standard. Phone number encoding is the practical approach.

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (Robokassa API is stable, 30-day validity)
