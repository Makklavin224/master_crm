"""Payment schemas for API request/response validation."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    """Create a manual payment (master marks booking as paid)."""

    booking_id: uuid.UUID
    payment_method: Literal["cash", "card_to_card", "transfer", "sbp"]
    fiscalization_level: Literal["none", "manual", "auto"] | None = None  # override
    amount_override: int | None = None  # If set, overrides service price (for discounts/extras), kopecks


class RobokassaPaymentCreate(BaseModel):
    """Initiate a Robokassa payment (sends SBP link to client)."""

    booking_id: uuid.UUID
    fiscalization_level: Literal["none", "manual", "auto"] | None = None  # override
    amount_override: int | None = None  # If set, overrides service price (for discounts/extras), kopecks


class RequisitesPaymentCreate(BaseModel):
    """Initiate a requisites payment (show QR code to client)."""

    booking_id: uuid.UUID
    fiscalization_level: Literal["none", "manual", "auto"] | None = None  # override


class PaymentConfirm(BaseModel):
    """Confirm a pending requisites payment (master marks as paid)."""

    payment_method: Literal["cash", "card_to_card", "transfer", "sbp"] = "sbp"


class PaymentRead(BaseModel):
    """Payment response with display fields."""

    id: uuid.UUID
    booking_id: uuid.UUID
    amount: int  # in kopecks
    status: str  # pending, paid, cancelled, refunded
    payment_method: str | None
    receipt_status: str  # not_applicable, pending, issued, failed, cancelled
    fiscalization_level: str | None
    paid_at: datetime | None
    created_at: datetime
    payment_url: str | None = None
    fns_receipt_url: str | None = None

    # Display fields (joined from booking -> service, booking -> client)
    service_name: str | None = None
    client_name: str | None = None

    model_config = {"from_attributes": True}


class PaymentListResponse(BaseModel):
    """Paginated payment list."""

    items: list[PaymentRead]
    total: int
    total_revenue: int = 0  # Sum of paid payment amounts in kopecks for the filtered query


class PaymentHistoryFilters(BaseModel):
    """Filters for payment history queries."""

    status: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ManualReceiptData(BaseModel):
    """Pre-formatted data for manual receipt entry in 'Moy Nalog'."""

    amount_display: str  # "1 500.00 rub"
    service_name: str
    client_name: str
    date: str  # "18.03.2026"


class PaymentRequisites(BaseModel):
    """Master's payment requisites with generated QR code."""

    card_number: str | None = None
    sbp_phone: str | None = None
    bank_name: str | None = None
    qr_code_base64: str  # base64-encoded PNG QR code
